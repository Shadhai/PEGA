"""
CINT-70 Real Validation Test
Forces actual constraint violations to verify system works
"""
import json
from src.graph.queries import ConstraintQueries
from src.validator.kinematics import KinematicsValidator

print("=" * 60)
print("REAL VALIDATION TEST")
print("=" * 60)

# Test 1: Graph DB Queries
print("\n[TEST 1] Graph DB Joint Limit Check")
graph = ConstraintQueries()

# Check a joint that SHOULD fail
result = graph.check_joint_limits("shoulder_pitch", 200.0)  # Way beyond 90° max
print(f"  Angle 200° on shoulder_pitch (max 90°): {'❌ FAIL' if not result['passed'] else '✅ PASS (WRONG!)'}")
print(f"  Result: {result}")

# Check valid joint
result = graph.check_joint_limits("shoulder_pitch", 45.0)
print(f"  Angle 45° on shoulder_pitch: {'✅ PASS' if result['passed'] else '❌ FAIL (WRONG!)'}")

# Test 2: Collision Detection
print("\n[TEST 2] Collision Detection")
result = graph.check_collision(0.8, 0.5, 1.8)  # Right at solar panel position
print(f"  Position at solar panel: {'❌ COLLISION' if not result['passed'] else '✅ CLEAR (WRONG!)'}")
print(f"  Result: {result}")

result = graph.check_collision(5.0, 5.0, 5.0)  # Far away
print(f"  Position far away: {'✅ CLEAR' if result['passed'] else '❌ COLLISION (WRONG!)'}")

# Test 3: Kinematics
print("\n[TEST 3] Kinematics Reachability")
kin = KinematicsValidator()

reachable, dist = kin.is_reachable([1.5, 0.5, 2.0])  # Within 2.1m
print(f"  Target [1.5, 0.5, 2.0]: {'✅ Reachable' if reachable else '❌ Unreachable'} (dist: {dist:.2f}m)")

reachable, dist = kin.is_reachable([10.0, 10.0, 10.0])  # Way too far
print(f"  Target [10, 10, 10]: {'✅ Reachable' if reachable else '❌ Unreachable (CORRECT!)'} (dist: {dist:.2f}m)")

# Test 4: Force Limit
print("\n[TEST 4] Tool Force Limit")
result = graph.check_tool_force("thermal_applicator", 100.0)  # Way above 15N max
print(f"  Force 100N on thermal_applicator (max 15N): {'❌ FAIL' if not result['passed'] else '✅ PASS (WRONG!)'}")
print(f"  Result: {result}")

result = graph.check_tool_force("thermal_applicator", 10.0)
print(f"  Force 10N on thermal_applicator: {'✅ PASS' if result['passed'] else '❌ FAIL (WRONG!)'}")

print("\n" + "=" * 60)
print("IF YOU SEE '(WRONG!)' ANYWHERE - SYSTEM IS BROKEN")
print("IF EVERYTHING IS CORRECT - GRAPH DB AND VALIDATORS WORK")
print("=" * 60)