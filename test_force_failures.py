"""
CINT-70 Forced Failure Test
Deliberately creates bad plans to verify validation + recovery
"""
import json
from src.agent.orchestrator import CINT70Orchestrator

print("=" * 60)
print("FORCED FAILURE & RECOVERY TEST")
print("=" * 60)

# Initialize
orch = CINT70Orchestrator()

# Test 1: Manually inject a BAD plan that WILL fail
print("\n[TEST 1] Deliberately bad joint angle")
bad_state = {
    "command": "Test bad joint angle",
    "retrieved_docs": [],
    "graph_constraints": orch.graph.get_all_constraints("test"),
    "plan": [
        {
            "step_id": 1,
            "action": "move_joint",
            "joint": "shoulder_pitch",  # max is 90°
            "target_angle_deg": 200.0,  # WAY over limit!
            "velocity_rad_s": 0.3,
            "rationale": "Testing violation"
        }
    ],
    "plan_json": "",
    "violations": [],
    "all_checks_passed": False,
    "trust_score": 0.0,
    "recovery_count": 0,
    "max_recoveries": 3,
    "failure_context": "",
    "stage": "validate",
    "evidence_log": [],
    "messages": [],
}

# Run validation directly
result = orch._validate_node(bad_state)
print(f"  Violations found: {len(result['violations'])}")
for v in result['violations']:
    print(f"  ❌ {v['message']}")
print(f"  All checks passed: {result['all_checks_passed']}")
print(f"  Trust score: {result['trust_score']:.1%}")

# Test 2: Collision test
print("\n[TEST 2] Deliberate collision")
bad_state2 = {
    "command": "Test collision",
    "retrieved_docs": [],
    "graph_constraints": orch.graph.get_all_constraints("test"),
    "plan": [
        {
            "step_id": 1,
            "action": "move_to",
            "joint": None,
            "target_angle_deg": None,
            "target_coordinates": [0.8, 0.5, 1.8],  # Right at solar panel!
            "rationale": "Testing collision"
        }
    ],
    "plan_json": "",
    "violations": [],
    "all_checks_passed": False,
    "trust_score": 0.0,
    "recovery_count": 0,
    "max_recoveries": 3,
    "failure_context": "",
    "stage": "validate",
    "evidence_log": [],
    "messages": [],
}

result2 = orch._validate_node(bad_state2)
print(f"  Violations found: {len(result2['violations'])}")
for v in result2['violations']:
    print(f"  ❌ {v['message']}")
print(f"  Trust score: {result2['trust_score']:.1%}")

# Test 3: Force tool overload
print("\n[TEST 3] Deliberate tool force overload")
bad_state3 = {
    "command": "Test force overload",
    "retrieved_docs": [],
    "graph_constraints": orch.graph.get_all_constraints("test"),
    "plan": [
        {
            "step_id": 1,
            "action": "apply_tool",
            "tool_name": "thermal_applicator",  # max 15N
            "contact_force_n": 500.0,  # WAY over!
            "rationale": "Testing force limit"
        }
    ],
    "plan_json": "",
    "violations": [],
    "all_checks_passed": False,
    "trust_score": 0.0,
    "recovery_count": 0,
    "max_recoveries": 3,
    "failure_context": "",
    "stage": "validate",
    "evidence_log": [],
    "messages": [],
}

result3 = orch._validate_node(bad_state3)
print(f"  Violations found: {len(result3['violations'])}")
for v in result3['violations']:
    print(f"  ❌ {v['message']}")
print(f"  Trust score: {result3['trust_score']:.1%}")

# Test 4: Full recovery cycle
print("\n[TEST 4] Recovery cycle test")
bad_state4 = {
    "command": "Test recovery",
    "retrieved_docs": [],
    "graph_constraints": orch.graph.get_all_constraints("test"),
    "plan": [
        {
            "step_id": 1,
            "action": "move_joint",
            "joint": "elbow_pitch",
            "target_angle_deg": -200.0,  # Below -120° min
            "velocity_rad_s": 1.0,
            "rationale": "Bad plan"
        }
    ],
    "plan_json": json.dumps([{"step_id": 1, "action": "move_joint", "joint": "elbow_pitch", "target_angle_deg": -200.0}]),
    "violations": [],
    "all_checks_passed": False,
    "trust_score": 0.0,
    "recovery_count": 0,
    "max_recoveries": 2,
    "failure_context": "",
    "stage": "validate",
    "evidence_log": [],
    "messages": [],
}

# Run validate
result4 = orch._validate_node(bad_state4)
print(f"  Validation result: {'PASSED' if result4['all_checks_passed'] else 'FAILED'}")
print(f"  Violations: {len(result4['violations'])}")
for v in result4['violations']:
    print(f"  ❌ {v['message']}")

# Route decision
route = orch._route_after_validation(result4)
print(f"  Route decision: {route}")
print(f"  (Should be 'recover' since recovery_count=0 < max_recoveries=2)")

# Run recovery
if route == "recover":
    recovered = orch._recover_node(result4)
    print(f"  Recovery count: {recovered['recovery_count']}")
    print(f"  Failure context: {recovered['failure_context'][:100]}...")
    print(f"  Stage: {recovered['stage']}")

print("\n" + "=" * 60)
print("ALL TESTS COMPLETE")
print("=" * 60)