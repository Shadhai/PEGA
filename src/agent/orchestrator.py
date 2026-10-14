"""
CINT-70 Orchestrator - Production Grade
Full LangGraph state machine with recovery cycles
Supports domains: space | industrial
"""

import json
from typing import Dict, Any, Literal, Optional, List
from datetime import datetime

from langgraph.graph import StateGraph, END
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress

from src.utils.evidence_db import EvidenceDB
from .state import AgentState, PipelineStage, ViolationType
from .planner import Planner
from src.rag.retriever import Retriever
from src.graph.queries import ConstraintQueries
from src.validator.kinematics import KinematicsValidator
from src.validator.constraints import ConstraintChecker
from src.chaos.injector import ChaosInjector


console = Console()


class CINT70Orchestrator:
    """Production-grade CINT-70 with LangGraph recovery cycles."""

    def __init__(
        self,
        ablation: Optional[Dict[str, bool]] = None,
        domain: Literal["space", "industrial"] = "space",
    ):
        if domain not in {"space", "industrial"}:
            raise ValueError(
                f"Unsupported domain {domain!r}; expected 'space' or 'industrial'"
            )
        self.domain = domain

        # Always start from full defaults, then merge any ablation overrides
        self.ablation = {
            "use_graph": True,
            "use_kinematics": True,
            "use_trajectory": True,
            "use_force_check": True,
        }
        if ablation is not None:
            self.ablation.update(ablation)

        console.print(
            "[bold cyan]╔══════════════════════════════════════╗[/bold cyan]"
        )
        console.print(
            f"[bold cyan]║   CINT-70 {self.domain.upper():<12} v2.0   ║[/bold cyan]"
        )
        console.print(
            "[bold cyan]╚══════════════════════════════════════╝[/bold cyan]"
        )

        with Progress() as progress:
            task = progress.add_task("[cyan]Loading components...", total=5)

            progress.update(task, description="Loading LLM...")
            self.planner = Planner()
            progress.advance(task)

            progress.update(task, description="Loading RAG...")
            self.retriever = Retriever()
            progress.advance(task)

            progress.update(task, description="Loading Graph DB...")
            self.graph = ConstraintQueries(domain=self.domain)
            progress.advance(task)

            progress.update(task, description="Loading Physics...")
            self.kinematics = KinematicsValidator()
            self.constraints = ConstraintChecker()
            progress.advance(task)

            progress.update(task, description="Loading Chaos Suite...")
            self.chaos = ChaosInjector()
            self.evidence_db = EvidenceDB()
            progress.advance(task)

        self._last_move_to_position: Dict[int, List[float]] = {}

        # Build LangGraph
        self.workflow = self._build_graph()
        self.app = self.workflow.compile()

        console.print("[bold green]✅ CINT-70 Ready![/bold green]\n")

    def _build_graph(self) -> StateGraph:
        """Build the full LangGraph state machine."""
        workflow = StateGraph(AgentState)

        workflow.add_node("node_retrieve", self._retrieve_node)
        workflow.add_node("node_plan", self._plan_node)
        workflow.add_node("node_validate", self._validate_node)
        workflow.add_node("node_approve", self._approve_node)
        workflow.add_node("node_recover", self._recover_node)
        workflow.add_node("node_reject", self._reject_node)
        workflow.add_node("node_flag", self._flag_node)

        workflow.set_entry_point("node_retrieve")
        workflow.add_edge("node_retrieve", "node_plan")
        workflow.add_edge("node_plan", "node_validate")

        workflow.add_conditional_edges(
            "node_validate",
            self._route_after_validation,
            {
                "approve": "node_approve",
                "recover": "node_recover",
                "reject": "node_reject",
                "flag": "node_flag",
            },
        )

        workflow.add_edge("node_recover", "node_plan")
        workflow.add_edge("node_approve", END)
        workflow.add_edge("node_reject", END)
        workflow.add_edge("node_flag", END)

        return workflow

    # ------------------------------------------------------------------
    # Nodes
    # ------------------------------------------------------------------

    def _retrieve_node(self, state: AgentState) -> AgentState:
        console.print("[yellow]📚 PHASE 1: EVIDENCE RETRIEVAL[/yellow]")

        docs = self.retriever.search(state["command"], top_k=5)
        constraints = self.graph.get_all_constraints(state["command"])

        state["retrieved_docs"] = docs
        state["graph_constraints"] = constraints
        state["stage"] = PipelineStage.RETRIEVE.value

        console.print(f"   Documents retrieved: {len(docs)}")
        console.print(f"   Graph constraints: {len(constraints)}")
        return state

    def _plan_node(self, state: AgentState) -> AgentState:
        console.print("[yellow]🧠 PHASE 2: PLAN GENERATION[/yellow]")

        command = state["command"]
        if state.get("failure_context"):
            command = (
                f"{command}\n\n"
                "PREVIOUS FAILURES (fix these):\n"
                f"{state['failure_context']}"
            )

        plan = self.planner.generate(
            command,
            state["retrieved_docs"],
            state["graph_constraints"],
        )

        state["plan"] = plan
        state["plan_json"] = json.dumps(plan, indent=2)
        state["stage"] = PipelineStage.PLAN.value

        console.print(f"   Generated {len(plan)} step plan")
        for step in plan:
            console.print(
                f"   Step {step['step_id']}: "
                f"{step['action']} - "
                f"{step.get('rationale', '')[:50]}"
            )
        return state

    def _validate_node(self, state: AgentState) -> AgentState:
        console.print("[yellow]🔍 PHASE 3: VALIDATION[/yellow]")

        self._last_move_to_position = {}
        violations = []
        all_passed = True

        for step in state["plan"]:
            step_id = step.get("step_id", 0)

            # Joint limits (graph)
            joint = step.get("joint")
            angle = step.get("target_angle_deg")
            if self.ablation["use_graph"] and joint and angle is not None:
                result = self.graph.check_joint_limits(joint, float(angle))
                if not result["passed"]:
                    all_passed = False
                    violations.append({
                        "step_id": step_id,
                        "type": ViolationType.JOINT_LIMIT.value,
                        "message": result["violation"],
                        "severity": result["severity"],
                        "evidence": f"Graph DB: Joint {joint}",
                    })
                    console.print(f"   ❌ Step {step_id}: {result['violation']}")

            # Force limits (graph)
            tool = step.get("tool_name")
            force = step.get("contact_force_n")
            if self.ablation["use_force_check"] and tool and force is not None:
                result = self.graph.check_tool_force(tool, float(force))
                if not result["passed"]:
                    all_passed = False
                    violations.append({
                        "step_id": step_id,
                        "type": ViolationType.FORCE.value,
                        "message": result["violation"],
                        "severity": result["severity"],
                        "evidence": f"Graph DB: Tool {tool}",
                    })
                    console.print(f"   ❌ Step {step_id}: {result['violation']}")

            # Kinematics
            if self.ablation["use_kinematics"] and not self.kinematics.validate(step):
                all_passed = False
                violations.append({
                    "step_id": step_id,
                    "type": ViolationType.KINEMATICS.value,
                    "message": "Target position unreachable",
                    "severity": 0.9,
                    "evidence": "Kinematics solver",
                })
                console.print(f"   ❌ Step {step_id}: Position unreachable")

            # Collision / trajectory (graph)
            target_coordinates = step.get("target_coordinates")
            if self.ablation["use_graph"] and target_coordinates:
                end = [
                    float(target_coordinates[0]),
                    float(target_coordinates[1]),
                    float(target_coordinates[2]),
                ]

                if (
                    self.ablation["use_trajectory"]
                    and step.get("action") == "move_to"
                ):
                    previous_end = self._last_move_to_position.get(-1)
                    if previous_end is None:
                        points_to_check = [end]
                    else:
                        try:
                            points_to_check = self.kinematics.sample_trajectory(
                                previous_end, end, n_samples=15
                            )
                        except Exception:
                            points_to_check = [end]
                else:
                    points_to_check = [end]

                for idx, wp in enumerate(points_to_check):
                    is_endpoint = idx == len(points_to_check) - 1
                    if is_endpoint:
                        result = self.graph.check_collision(
                            float(wp[0]), float(wp[1]), float(wp[2])
                        )
                    else:
                        result = self.graph.check_collision_trajectory(
                            float(wp[0]), float(wp[1]), float(wp[2])
                        )

                    if not result["passed"]:
                        all_passed = False
                        if step.get("action") == "move_to" and len(points_to_check) > 1:
                            message = (
                                f"Trajectory collision at waypoint "
                                f"{idx}/{len(points_to_check) - 1} "
                                f"({wp[0]:.2f}, {wp[1]:.2f}, {wp[2]:.2f}): "
                                f"{result['violation']}"
                            )
                            console.print(
                                f"   ❌ Step {step_id}: "
                                f"Trajectory collision at waypoint {idx}"
                            )
                        else:
                            message = result["violation"]
                            console.print(
                                f"   ❌ Step {step_id}: {result['violation']}"
                            )

                        violations.append({
                            "step_id": step_id,
                            "type": ViolationType.COLLISION.value,
                            "message": message,
                            "severity": result["severity"],
                            "evidence": "Graph DB: Obstacle query",
                        })
                        break

                if step.get("action") == "move_to":
                    self._last_move_to_position[-1] = end

            # Step passed?
            if all(v["step_id"] != step_id for v in violations):
                console.print(f"   ✅ Step {step_id}: All checks passed")

        # Trust score
        if violations:
            avg_severity = sum(v["severity"] for v in violations) / len(violations)
            trust_score = max(0.0, 1.0 - avg_severity)
        else:
            trust_score = 1.0

        state["violations"] = violations
        state["all_checks_passed"] = all_passed
        state["trust_score"] = trust_score
        state["stage"] = PipelineStage.VALIDATE.value

        state["evidence_log"] = state.get("evidence_log", []) + [{
            "timestamp": datetime.now().isoformat(),
            "command": state["command"],
            "plan_steps": len(state["plan"]),
            "violations": len(violations),
            "trust_score": trust_score,
            "recovery_attempt": state.get("recovery_count", 0),
        }]

        return state

    def _route_after_validation(
        self, state: AgentState
    ) -> Literal["approve", "recover", "reject", "flag"]:
        if state["all_checks_passed"]:
            return "approve"

        max_severity = max(
            (v.get("severity", 0.0) for v in state.get("violations", [])),
            default=0.0,
        )

        # Consistent with paper / HITL section (threshold = 0.75)
        if 0 < max_severity < 0.75:
            return "flag"

        recovery_count = state.get("recovery_count", 0)
        max_recoveries = state.get("max_recoveries", 3)

        if recovery_count < max_recoveries:
            return "recover"

        return "reject"

    def _flag_node(self, state: AgentState) -> AgentState:
        max_severity = max(
            (v.get("severity", 0.0) for v in state.get("violations", [])),
            default=0.0,
        )
        console.print(
            Panel.fit(
                "[bold yellow]⚠️ PLAN FLAGGED FOR HUMAN REVIEW[/bold yellow]\n\n"
                f"Trust Score: {state['trust_score']:.2%}\n"
                f"Violations: {len(state.get('violations', []))}\n"
                f"Max Severity: {max_severity:.2f}\n\n"
                "[italic]This plan is on the boundary and requires "
                "operator judgement.[/italic]",
                title="CINT-70 REVIEW NOTICE",
                border_style="yellow",
            )
        )
        state["stage"] = PipelineStage.FLAGGED.value
        self._save_evidence(state)

        try:
            self.evidence_db.log_run(
                task_id=state.get("task_id", "unknown"),
                command=state["command"],
                expected_safe=state.get("expected_safe", True),
                approved=False,
                trust_score=state["trust_score"],
                plan=state.get("plan", []),
                violations=state.get("violations", []),
                recovery_count=state.get("recovery_count", 0),
                stage=state.get("stage", "flagged"),
                evidence_log=state.get("evidence_log", []),
            )
        except Exception as e:
            print(f"  Evidence DB write note: {e}")

        return state

    def _approve_node(self, state: AgentState) -> AgentState:
        console.print(
            Panel.fit(
                f"[bold green]✅ PLAN APPROVED FOR EXECUTION[/bold green]\n\n"
                f"Trust Score: {state['trust_score']:.2%}\n"
                f"Steps Validated: {len(state['plan'])}\n"
                f"Violations: 0\n"
                f"Recovery Attempts: {state.get('recovery_count', 0)}\n"
                f"Evidence Log: {len(state.get('evidence_log', []))} entries\n\n"
                "[italic]This decision is traceable. Evidence trail saved.[/italic]",
                title="CINT-70 ASSURANCE CERTIFICATE",
                border_style="green",
            )
        )

        state["stage"] = PipelineStage.APPROVED.value
        self._save_evidence(state)

        try:
            self.evidence_db.log_run(
                task_id=state.get("task_id", "unknown"),
                command=state["command"],
                expected_safe=state.get("expected_safe", True),
                approved=True,
                trust_score=state["trust_score"],
                plan=state.get("plan", []),
                violations=[],
                recovery_count=state.get("recovery_count", 0),
                stage=state.get("stage", "approved"),
                evidence_log=state.get("evidence_log", []),
            )
        except Exception as e:
            print(f"  Evidence DB write note: {e}")

        try:
            self.retriever.memory.store_experience(
                command=state["command"],
                plan=state["plan"],
                outcome="APPROVED",
                trust_score=state["trust_score"],
                violations=[],
                recovery_count=state.get("recovery_count", 0),
                safe_coords=self._extract_coordinates(state["plan"]),
            )
        except Exception as e:
            print(f"  Memory store note: {e}")

        return state

    def _recover_node(self, state: AgentState) -> AgentState:
        state["recovery_count"] = state.get("recovery_count", 0) + 1

        console.print(
            f"[orange1]🔄 RECOVERY ATTEMPT "
            f"{state['recovery_count']}/{state.get('max_recoveries', 3)}"
            f"[/orange1]"
        )

        failure_msgs = [
            f"Step {v['step_id']}: {v['message']} [Source: {v['evidence']}]"
            for v in state.get("violations", [])
        ]
        state["failure_context"] = "\n".join(failure_msgs)
        state["stage"] = PipelineStage.RECOVERING.value

        console.print("   Failures detected:")
        for msg in failure_msgs:
            console.print(f"   • {msg}")
        console.print("   Regenerating plan with failure context...")
        return state

    def _reject_node(self, state: AgentState) -> AgentState:
        console.print(
            Panel.fit(
                f"[bold red]❌ PLAN REJECTED[/bold red]\n\n"
                f"Max recovery attempts ({state.get('max_recoveries', 3)}) exceeded.\n"
                f"Violations: {len(state.get('violations', []))}\n\n"
                f"Manual intervention required.",
                title="CINT-70 REJECTION NOTICE",
                border_style="red",
            )
        )

        state["stage"] = PipelineStage.EXHAUSTED.value

        try:
            self.retriever.memory.store_experience(
                command=state["command"],
                plan=state["plan"],
                outcome="REJECTED",
                trust_score=state["trust_score"],
                violations=state.get("violations", []),
                recovery_count=state.get("recovery_count", 0),
            )
        except Exception as e:
            print(f"  Memory store note: {e}")

        self._save_evidence(state)

        try:
            self.evidence_db.log_run(
                task_id=state.get("task_id", "unknown"),
                command=state["command"],
                expected_safe=state.get("expected_safe", True),
                approved=False,
                trust_score=state["trust_score"],
                plan=state.get("plan", []),
                violations=state.get("violations", []),
                recovery_count=state.get("recovery_count", 0),
                stage=state.get("stage", "rejected"),
                evidence_log=state.get("evidence_log", []),
            )
        except Exception as e:
            print(f"  Evidence DB write note: {e}")

        return state

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _extract_coordinates(self, plan: List[Dict]) -> Optional[List]:
        for step in plan:
            if "target_coordinates" in step and step["target_coordinates"]:
                return step["target_coordinates"]
        return None

    def _save_evidence(self, state: AgentState):
        import os
        os.makedirs("logs/evidence", exist_ok=True)
        filename = (
            "logs/evidence/run_"
            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(filename, "w") as f:
            json.dump(
                {
                    "task_id": state.get("task_id", "unknown"),
                    "expected_safe": state.get("expected_safe", True),
                    "command": state["command"],
                    "plan": state["plan"],
                    "violations": state.get("violations", []),
                    "trust_score": state["trust_score"],
                    "stage": state["stage"],
                    "recovery_count": state.get("recovery_count", 0),
                    "evidence_log": state.get("evidence_log", []),
                },
                f,
                indent=2,
            )
        console.print(f"   📁 Evidence saved: {filename}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def execute(
        self,
        command: str,
        inject_failure: str = None,
        max_recoveries: int = 3,
        task_id: str = "unknown",
        expected_safe: bool = True,
    ) -> Dict:
        """Execute a command through the full pipeline."""
        chaos_info = None
        if inject_failure:
            chaos_info = self.chaos.inject(inject_failure)
            console.print(f"[red]💥 CHAOS INJECTED: {chaos_info['message']}[/red]")

        initial_state: AgentState = {
            "command": command,
            "task_id": task_id,
            "expected_safe": expected_safe,
            "retrieved_docs": [],
            "graph_constraints": [],
            "plan": [],
            "plan_json": "",
            "violations": [],
            "all_checks_passed": False,
            "trust_score": 0.0,
            "recovery_count": 0,
            "max_recoveries": max_recoveries,
            "failure_context": "",
            "stage": PipelineStage.RETRIEVE.value,
            "evidence_log": [],
            "messages": [],
        }

        try:
            final_state = self.app.invoke(initial_state, {"recursion_limit": 50})

            table = Table(title=f"RESULTS: {command[:50]}...")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="bold")
            table.add_row(
                "Status",
                "✅ APPROVED" if final_state["all_checks_passed"] else "❌ REJECTED",
            )
            table.add_row("Trust Score", f"{final_state['trust_score']:.2%}")
            table.add_row("Steps", str(len(final_state.get("plan", []))))
            table.add_row("Violations", str(len(final_state.get("violations", []))))
            table.add_row("Recoveries", str(final_state.get("recovery_count", 0)))
            if chaos_info:
                table.add_row("Chaos", chaos_info["type"])
            console.print(table)

            return final_state
        except Exception as e:
            console.print(f"[red]❌ Pipeline error: {str(e)}[/red]")
            return {"error": str(e)}

    def execute_custom_plan(
        self,
        command: str,
        plan: List[Dict[str, Any]],
        inject_failure: str = None,
        task_id: str = "unknown",
    ) -> Dict[str, Any]:
        """
        Validate a manually supplied plan without invoking the planner.
        Used for adversarial / unsafe benchmark tasks.
        """
        console.print(
            "[bold magenta]🧪 CUSTOM PLAN / ADVERSARIAL VALIDATION[/bold magenta]"
        )

        chaos_info = None
        if inject_failure:
            chaos_info = self.chaos.inject(inject_failure)
            console.print(f"[red]💥 CHAOS INJECTED: {chaos_info['message']}[/red]")

        try:
            retrieved_docs = self.retriever.search(command, top_k=5)
            graph_constraints = self.graph.get_all_constraints(command)
        except Exception as e:
            console.print(f"[red]❌ Custom-plan retrieval error: {str(e)}[/red]")
            return {"error": str(e)}

        initial_state: AgentState = {
            "command": command,
            "task_id": task_id,
            "expected_safe": False,
            "retrieved_docs": retrieved_docs,
            "graph_constraints": graph_constraints,
            "plan": plan,
            "plan_json": json.dumps(plan, indent=2),
            "violations": [],
            "all_checks_passed": False,
            "trust_score": 0.0,
            "recovery_count": 0,
            "max_recoveries": 0,          # no recovery for adversarial tests
            "failure_context": "",
            "stage": PipelineStage.VALIDATE.value,
            "evidence_log": [],
            "messages": [],
        }

        console.print(f"   Custom plan contains {len(plan)} step(s)")
        for step in plan:
            console.print(
                f"   Step {step.get('step_id', 0)}: "
                f"{step.get('action', 'unknown')} - "
                f"{step.get('rationale', '')[:60]}"
            )

        try:
            final_state = self._validate_node(initial_state)
        except Exception as e:
            console.print(f"[red]❌ Custom-plan validation error: {str(e)}[/red]")
            return {"error": str(e)}

        if final_state["all_checks_passed"]:
            final_state = self._approve_node(final_state)
        else:
            max_sev = max(
                (v.get("severity", 0.0) for v in final_state.get("violations", [])),
                default=0.0,
            )
            if 0 < max_sev < 0.75:
                final_state = self._flag_node(final_state)
            else:
                final_state = self._reject_node(final_state)

        table = Table(title=f"ADVERSARIAL RESULTS: {command[:50]}...")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="bold")
        table.add_row(
            "Status",
            "⚠️ APPROVED" if final_state["all_checks_passed"] else "🛑 REJECTED",
        )
        table.add_row("Trust Score", f"{final_state['trust_score']:.2%}")
        table.add_row("Steps", str(len(final_state.get("plan", []))))
        table.add_row("Violations", str(len(final_state.get("violations", []))))
        table.add_row("Recoveries", str(final_state.get("recovery_count", 0)))
        if chaos_info:
            table.add_row("Chaos", chaos_info["type"])
        console.print(table)

        return final_state