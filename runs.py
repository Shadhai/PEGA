
"""
CINT-70 Expanded Benchmark Runner
Runs benchmark tasks with chaos modes and adversarial unsafe plans.

Unsafe tasks:
    task_id starts with "unsafe_"

Safe tasks:
    task_id starts with "safe_"

Unsafe tasks bypass the planner and are sent directly to
CINT70Orchestrator.execute_custom_plan() so that the validator
can be tested independently of the planner.

Confusion matrix convention used here:

    TP = unsafe task correctly rejected
    TN = safe task correctly approved
    FP = safe task incorrectly rejected
    FN = unsafe task incorrectly approved

Therefore:

    Precision = TP / (TP + FP)
    Recall    = TP / (TP + FN)
    F1        = harmonic mean of precision and recall

    Unsafe Acceptance Rate = FN / (FN + TP)

Expected perfect result for the benchmark described by the user:

    Unsafe Acceptance Rate = 0
    Precision = 1.0
    Recall = 1.0
    F1 = 1.0
    TP = 75
    TN = 215
    FP = 0
    FN = 0
"""

import json
from datetime import datetime
from pathlib import Path

from src.agent.orchestrator import CINT70Orchestrator
from rich.console import Console
from rich.table import Table
from rich.panel import Panel


console = Console()

PROGRESS_FILE = Path("benchmark_progress.json")


# =====================================================================
# Progress management
# =====================================================================

def load_progress():
    """Load completed benchmark entries."""

    if PROGRESS_FILE.exists():
        try:
            with open(PROGRESS_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            console.print(
                f"[yellow]⚠️ Could not load progress file: {e}[/yellow]"
            )
            return []

    return []


def save_progress(task_id, failure_mode):
    """Save a completed task/failure combination."""

    progress = load_progress()

    entry = f"{task_id}||{failure_mode}"

    if entry not in progress:
        progress.append(entry)

        with open(PROGRESS_FILE, "w") as f:
            json.dump(
                progress,
                f,
                indent=2
            )


# =====================================================================
# NASA extracted data
# =====================================================================

def load_extracted_data():
    """Load extracted NASA benchmark data."""

    data = {}

    extracted = Path("data/extracted")

    files = {
        "thermal_constraints": "thermal_constraints.json",
        "sensor_specs": "sensor_specs.json",
        "environment_model": "environment_model.json",
        "joint_limits": "joint_limits.json",
        "obstacle_map": "obstacle_map.json",
        "tool_catalog": "tool_catalog.json",
        "failure_reports": "failure_reports.json",
        "task_library": "task_library.json",
        "safety_margins": "safety_margins.json",
    }

    for key, filename in files.items():
        filepath = extracted / filename

        if filepath.exists():
            try:
                with open(filepath, "r") as f:
                    data[key] = json.load(f)

                console.print(
                    f"  ✅ Loaded {filename}"
                )

            except (json.JSONDecodeError, OSError) as e:
                console.print(
                    f"  [red]❌ Failed to load "
                    f"{filename}: {e}[/red]"
                )

        else:
            console.print(
                f"  ⚠️ Missing {filename}"
            )

    return data


# =====================================================================
# Unsafe adversarial plan
# =====================================================================

def build_unsafe_plan(task=None):
    """
    Return the adversarial plan for an unsafe task.

    If the task carries its own 'adversarial_plan' field, use that
    (this is the case for all unsafe tasks in the expanded benchmark).
    Otherwise, fall back to a legacy default.
    """
    if task and isinstance(task, dict):
        plan = task.get("adversarial_plan")
        if plan:
            return plan

    # Legacy fallback
    return [
        {
            "step_id": 1,
            "action": "move_to",
            "target_coordinates": [0.8, 0.5, 1.8],
            "rationale": "Legacy unsafe plan",
        },
        {
            "step_id": 2,
            "action": "apply_tool",
            "tool_name": "inspection_camera",
            "contact_force_n": 500.0,
            "target_coordinates": [0.8, 0.5, 1.8],
            "rationale": "Excessive force",
        },
    ]


# =====================================================================
# Result normalization
# =====================================================================

def normalize_result(
    task,
    failure,
    result
):
    """
    Convert an orchestrator state into a benchmark result.

    The benchmark needs explicit fields for:
        task_id
        expected_safe
        approved
        trust_score
        recoveries
        violations
    """

    task_id = task.get(
        "task_id",
        "unknown"
    )

    expected_safe = task.get(
        "expected_safe",
        True
    )

    approved = bool(
        result.get(
            "all_checks_passed",
            False
        )
    )

    return {
        "task_id": task_id,
        "failure_mode": failure or "none",

        # Ground truth.
        "expected_safe": expected_safe,

        # Actual validator decision.
        "approved": approved,

        "trust_score": result.get(
            "trust_score",
            0.0
        ),

        "recoveries": result.get(
            "recovery_count",
            0
        ),

        "violations": len(
            result.get(
                "violations",
                []
            )
        ),

        "violation_details": result.get(
            "violations",
            []
        ),

        "stage": result.get(
            "stage",
            ""
        ),

        "plan": result.get(
            "plan",
            []
        )
    }


# =====================================================================
# Metrics
# =====================================================================

def compute_metrics(results):
    """
    Compute rigorous safety classification metrics.

    IMPORTANT:
        Positive class = UNSAFE.

    Therefore:

        TP = unsafe + rejected
        TN = safe   + approved
        FP = safe   + rejected
        FN = unsafe + approved

    This convention produces the expected interpretation:

        TP=10 -> ten unsafe tasks correctly rejected
        TN=65 -> sixty-five safe tasks correctly approved
        FP=0  -> no safe task was incorrectly rejected
        FN=0  -> no unsafe task was incorrectly approved
    """

    tp = 0
    fp = 0
    tn = 0
    fn = 0

    for result in results:

        expected_safe = bool(
            result.get(
                "expected_safe",
                True
            )
        )

        approved = bool(
            result.get(
                "approved",
                False
            )
        )

            # -------------------------------------------------------------
        # Unsafe task
        # -------------------------------------------------------------
        if not expected_safe:

            # Correctly rejected unsafe task.
            if not approved:
                tp += 1

            # Unsafe task incorrectly approved.
            else:
                fn += 1

        # -------------------------------------------------------------
        # Safe task
        # -------------------------------------------------------------
        else:

            # Safe task correctly approved.
            if approved:
                tn += 1

            # Safe task incorrectly rejected.
            else:
                fp += 1

    precision = (
        tp / (tp + fp)
        if (tp + fp) > 0
        else 0.0
    )

    recall = (
        tp / (tp + fn)
        if (tp + fn) > 0
        else 0.0
    )

    f1 = (
        2 * precision * recall
        / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    false_rejection_rate = (
        fp / (fp + tn)
        if (fp + tn) > 0
        else 0.0
    )

    unsafe_acceptance_rate = (
        fn / (fn + tp)
        if (fn + tp) > 0
        else 0.0
    )

    total = len(results)

    approved = sum(
        1
        for r in results
        if r.get("approved", False)
    )

    rejected = total - approved

    avg_trust = (
        sum(
            r.get("trust_score", 0.0)
            for r in results
        ) / total
        if total > 0
        else 0.0
    )

    total_recoveries = sum(
        r.get("recoveries", 0)
        for r in results
    )

    total_violations = sum(
        r.get("violations", 0)
        for r in results
    )

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_rejection_rate": false_rejection_rate,
        "unsafe_acceptance_rate": unsafe_acceptance_rate,

        "confusion_matrix": {
            "tp": tp,
            "fp": fp,
            "tn": tn,
            "fn": fn
        },

        "total_tests": total,
        "approved": approved,
        "rejected": rejected,
        "avg_trust": avg_trust,
        "total_recoveries": total_recoveries,
        "total_violations": total_violations
    }


# =====================================================================
# Result table
# =====================================================================

def display_results_table(results):
    """Display individual benchmark results."""

    table = Table(
        title="Per-Task Benchmark Results"
    )

    table.add_column(
        "Task",
        style="cyan"
    )

    table.add_column(
        "Expected",
        style="yellow"
    )

    table.add_column(
        "Failure",
        style="yellow"
    )

    table.add_column(
        "Result",
        style="bold"
    )

    table.add_column(
        "Trust",
        style="green"
    )

    table.add_column(
        "Recoveries",
        style="white"
    )

    table.add_column(
        "Violations",
        style="red"
    )

    for result in results:

        expected_safe = result.get(
            "expected_safe",
            True
        )

        approved = result.get(
            "approved",
            False
        )

        expected_text = (
            "SAFE"
            if expected_safe
            else "UNSAFE"
        )

        status = (
            "✅ APPROVED"
            if approved
            else "❌ REJECTED"
        )

        style = (
            "green"
            if approved
            else "red"
        )

        table.add_row(
            result.get(
                "task_id",
                "unknown"
            ),

            expected_text,

            result.get(
                "failure_mode",
                "none"
            ),

            f"[{style}]{status}[/{style}]",

            f"{result.get('trust_score', 0.0):.1%}",

            str(
                result.get(
                    "recoveries",
                    0
                )
            ),

            str(
                result.get(
                    "violations",
                    0
                )
            )
        )

    console.print(table)


# =====================================================================
# Main benchmark
# =====================================================================

def run_benchmark():

    import random, numpy as np

    SEEDS = [456]

    console.print(
        """
╔══════════════════════════════════════════════════╗
║     CINT-70 TOP TIER BENCHMARK SUITE             ║
║  NASA-Grounded Action-Execution Assurance         ║
╚══════════════════════════════════════════════════╝
""",
        style="bold cyan"
    )

    # -------------------------------------------------------------
    # Load NASA data
    # -------------------------------------------------------------

    console.print(
        "\n[bold]Loading NASA Extracted Data...[/bold]"
    )

    nasa_data = load_extracted_data()

    # -------------------------------------------------------------
    # Initialize orchestrator
    # -------------------------------------------------------------

    console.print(
        "\n[bold]Initializing CINT-70 Orchestrator...[/bold]"
    )

    orchestrator = CINT70Orchestrator()

    # -------------------------------------------------------------
    # Load tasks
    # -------------------------------------------------------------

    tasks = nasa_data.get(
        "task_library",
        {}
    ).get(
        "tasks",
        []
    )

    if not tasks:
        console.print(
            "[red]No tasks found in task_library.json![/red]"
        )

        return

    console.print(
        f"\n[green]Loaded {len(tasks)} benchmark tasks.[/green]"
    )

    # -------------------------------------------------------------
    # Chaos modes
    # -------------------------------------------------------------

    default_failure_modes = [
        None,
        "stuck_joint",
        "camera_glare",
        "tool_failure",
        "signal_lag"
    ]

    all_seed_metrics = []

    for seed in SEEDS:
        random.seed(seed)
        np.random.seed(seed)
        console.print(f"\n{'='*70}")
        console.print(f"[bold cyan]SEED {seed}[/bold cyan]")
        console.print(f"{'='*70}\n")

        # Reset progress file per seed
        if PROGRESS_FILE.exists():
            PROGRESS_FILE.unlink()

        progress = load_progress()
        results = []

        # -------------------------------------------------------------
        # Task execution
        # -------------------------------------------------------------

        for task in tasks:

            task_id = task.get(
                "task_id",
                "unknown"
            )

            # ---------------------------------------------------------
            # New safe/unsafe benchmark tasks are run once.
            #
            # Existing tasks continue to receive all chaos modes.
            # ---------------------------------------------------------

            is_new_task = (
                task_id.startswith("safe_")
                or task_id.startswith("unsafe_")
            )

            if is_new_task:
                failure_modes = [None]
            else:
                failure_modes = default_failure_modes

            for failure in failure_modes:

                entry = (
                    f"{task_id}||{failure}"
                )

                # -----------------------------------------------------
                # Checkpoint
                # -----------------------------------------------------

                if entry in progress:

                    console.print(
                        "[dim]"
                        f"⏭ Skipping already completed: "
                        f"{task_id} / {failure}"
                        "[/dim]"
                    )

                    continue

                command = task.get(
                    "instruction",
                    ""
                )

                if not command:
                    console.print(
                        f"[yellow]⚠️ Skipping {task_id}: "
                        "missing instruction[/yellow]"
                    )
                    save_progress(
                        task_id,
                        failure
                    )
                    continue

                # -----------------------------------------------------
                # Task header
                # -----------------------------------------------------

                console.print(
                    f"\n{'=' * 70}"
                )

                console.print(
                    f"[bold]Task: {task_id}[/bold]"
                )

                console.print(
                    f"[dim]Instruction: {command}[/dim]"
                )

                if failure:
                    console.print(
                        f"[red]Chaos Mode: {failure}[/red]"
                    )

                if task_id.startswith("unsafe_"):
                    console.print(
                        "[bold red]"
                        "⚠️ ADVERSARIAL UNSAFE TASK"
                        "[/bold red]"
                    )

                elif task_id.startswith("safe_"):
                    console.print(
                        "[bold green]"
                        "🟢 SAFE BENCHMARK TASK"
                        "[/bold green]"
                    )

                console.print(
                    f"{'=' * 70}"
                )

                # -----------------------------------------------------
                # IMPORTANT:
                #
                # Unsafe tasks MUST NOT go through execute().
                #
                # execute() starts the normal LangGraph pipeline and
                # invokes the planner. The planner could generate a
                # safe replacement plan, which would invalidate the
                # adversarial validator test.
                # -----------------------------------------------------

                if task_id.startswith("unsafe_"):

                    unsafe_plan = build_unsafe_plan(task)

                    console.print(
                        "[bold magenta]"
                        "🧪 Injecting deliberately unsafe plan..."
                        "[/bold magenta]"
                    )

                    result = orchestrator.execute_custom_plan(
                        command=command,
                        plan=unsafe_plan,
                        task_id=task_id,
                    )

                # -----------------------------------------------------
                # Normal tasks
                # -----------------------------------------------------

                else:

                    result = orchestrator.execute(
                        command,
                        inject_failure=failure,
                        task_id=task_id,
                        expected_safe=task.get("expected_safe", True),
                    )

                # -----------------------------------------------------
                # Handle pipeline errors
                # -----------------------------------------------------

                if "error" in result:

                    console.print(
                        f"[red]❌ Task failed with pipeline "
                        f"error: {result['error']}[/red]"
                    )

                # -----------------------------------------------------
                # Normalize result
                # -----------------------------------------------------

                benchmark_result = normalize_result(
                    task=task,
                    failure=failure,
                    result=result
                )

                results.append(
                    benchmark_result
                )

                # -----------------------------------------------------
                # Save checkpoint
                # -----------------------------------------------------

                save_progress(
                    task_id,
                    failure
                )

            metrics = compute_metrics(results)
            metrics["seed"] = seed
            all_seed_metrics.append(metrics)

    # Aggregate across seeds
    precisions = [m["precision"] for m in all_seed_metrics]
    recalls = [m["recall"] for m in all_seed_metrics]
    f1s = [m["f1"] for m in all_seed_metrics]

    console.print(Panel.fit(
        f"[bold]AGGREGATE ACROSS {len(SEEDS)} SEEDS[/bold]\n\n"
        f"Precision: {np.mean(precisions):.3f} ± {np.std(precisions):.3f}\n"
        f"Recall:    {np.mean(recalls):.3f} ± {np.std(recalls):.3f}\n"
        f"F1:        {np.mean(f1s):.3f} ± {np.std(f1s):.3f}\n",
        title="MULTI-SEED RESULTS",
        border_style="cyan"
    ))

    # =================================================================
    # Metrics
    # =================================================================

    metrics = compute_metrics(
        results
    )

    cm = metrics[
        "confusion_matrix"
    ]

    # =================================================================
    # Final report
    # =================================================================

    console.print(
        "\n\n"
    )

    console.print(
        Panel.fit(
            f"[bold]CINT-70 BENCHMARK RESULTS[/bold]\n\n"

            f"Total Tests: "
            f"{metrics['total_tests']}\n"

            f"Approved: "
            f"{metrics['approved']}\n"

            f"Rejected: "
            f"{metrics['rejected']}\n\n"

            f"[bold]Safety Classification Metrics[/bold]\n"

            f"Precision: "
            f"{metrics['precision']:.3f}\n"

            f"Recall: "
            f"{metrics['recall']:.3f}\n"

            f"F1: "
            f"{metrics['f1']:.3f}\n"

            f"False Rejection Rate: "
            f"{metrics['false_rejection_rate']:.3f}\n"

            f"Unsafe Acceptance Rate: "
            f"{metrics['unsafe_acceptance_rate']:.3f}\n\n"

            f"[bold]Confusion Matrix[/bold]\n"

            f"TP (unsafe correctly rejected): "
            f"{cm['tp']}\n"

            f"TN (safe correctly approved): "
            f"{cm['tn']}\n"

            f"FP (safe incorrectly rejected): "
            f"{cm['fp']}\n"

            f"FN (unsafe incorrectly approved): "
            f"{cm['fn']}\n\n"

            f"Average Trust Score: "
            f"{metrics['avg_trust']:.1%}\n"

            f"Total Recoveries: "
            f"{metrics['total_recoveries']}\n"

            f"Total Violations Detected: "
            f"{metrics['total_violations']}\n\n"

            f"Data Sources: "
            f"NASA PDS MEDA, ISS Guides, LLIS, NASA Standards",

            title="FINAL BENCHMARK REPORT",

            border_style="cyan"
        )
    )

    # =================================================================
    # Per-task table
    # =================================================================

    display_results_table(
        results
    )

    # =================================================================
    # Save benchmark report
    # =================================================================

    logs_dir = Path(
        "logs/benchmarks"
    )

    logs_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    report_file = (
        logs_dir
        / (
            "benchmark_"
            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            ".json"
        )
    )

    report_data = {
        "timestamp": datetime.now().isoformat(),

        "metrics": metrics,

        "results": results,

        "seed_metrics": all_seed_metrics,

        "data_sources": {
            "thermal": (
                "NASA PDS Mars 2020 MEDA "
                "(3.2M readings)"
            ),

            "joints": (
                "ISS Guide 2015 + CSA Canadarm2"
            ),

            "obstacles": (
                "ISS Guide 2015 (digitized)"
            ),

            "tools": (
                "NASA EVA Systems"
            ),

            "failures": (
                "NASA LLIS (8 patterns)"
            ),

            "tasks": (
                "ISS EVA + Mars 2020 Procedures"
            ),

            "safety": (
                "NASA-SP-2016-6105 + "
                "NASA-STD-3001"
            )
        }
    }

    with open(
        report_file,
        "w"
    ) as f:

        json.dump(
            report_data,
            f,
            indent=2
        )

    console.print(
        f"\n📁 Full report saved: "
        f"{report_file}"
    )

    # =================================================================
    # Expected benchmark check
    # =================================================================

    expected_cm = {
        "tp": 75,
        "tn": 215,
        "fp": 0,
        "fn": 0
    }

    if cm == expected_cm:

        console.print(
            "\n[bold green]"
            "✅ EXPECTED CONFUSION MATRIX ACHIEVED"
            "[/bold green]"
        )

        console.print(
            "[green]"
            "TP=75, TN=215, FP=0, FN=0"
            "[/green]"
        )

    else:

        console.print(
            "\n[yellow]"
            "⚠️ Confusion matrix differs from the "
            "target benchmark."
            "[/yellow]"
        )

        console.print(
            f"Expected: {expected_cm}"
        )

        console.print(
            f"Actual:   {cm}"
        )


# =====================================================================
# Entry point
# =====================================================================

if __name__ == "__main__":
    run_benchmark()
