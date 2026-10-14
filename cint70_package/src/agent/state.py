"""
CINT-70 Agent State - Production Grade
Supports full LangGraph cycles with recovery
"""
from typing import TypedDict, List, Dict, Any, Optional, Annotated, Sequence
from langgraph.graph.message import add_messages
from dataclasses import dataclass
from enum import Enum

class PipelineStage(Enum):
    RETRIEVE = "retrieve"
    PLAN = "plan"
    VALIDATE = "validate"
    APPROVED = "approved"
    REJECTED = "rejected"
    RECOVERING = "recovering"
    EXHAUSTED = "exhausted"
    FLAGGED = "flagged_for_review"

class ViolationType(Enum):
    JOINT_LIMIT = "joint_limit"
    COLLISION = "collision"
    KINEMATICS = "kinematics"
    THERMAL = "thermal"
    FORCE = "force"
    OBSTRUCTION = "obstruction"
    TOOL_MISSING = "tool_missing"
    SIGNAL_LAG = "signal_lag"
    SENSOR_BLIND = "sensor_blind"

@dataclass
class ConstraintViolation:
    step_id: int
    violation_type: ViolationType
    severity: float  # 0.0 to 1.0
    message: str
    evidence_source: str
    suggested_fix: str

class AgentState(TypedDict):
    # Input
    command: str
    task_id: str
    expected_safe: bool
    
    # Retrieval
    retrieved_docs: List[Dict[str, Any]]
    graph_constraints: List[Dict[str, Any]]
    
    # Planning
    plan: List[Dict[str, Any]]
    plan_json: str
    
    # Validation
    violations: List[Dict[str, Any]]
    all_checks_passed: bool
    trust_score: float
    
    # Recovery
    recovery_count: int
    max_recoveries: int
    failure_context: str
    
    # Pipeline control
    stage: str
    
    # Evidence
    evidence_log: List[Dict[str, Any]]
    
    # Messages for LangGraph
    messages: Annotated[list, add_messages]