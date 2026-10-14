"""Formal constraint verification using Z3."""
from math import sqrt
from typing import Dict, Any, List

try:
    from z3 import Real, Solver, sat
    Z3_AVAILABLE = True
except ImportError:
    Z3_AVAILABLE = False


class FormalVerifier:
    def __init__(self, graph):
        self.graph = graph
        self.z3_available = Z3_AVAILABLE

    def verify_joint_within_range(self, joint: str, angle: float) -> Dict[str, Any]:
        if not self.z3_available:
            return {"verifiable": False, "passed": None, "reason": "Z3 not installed"}
        result = self.graph.conn.execute(
            f"MATCH (j:Joint) WHERE j.name = '{joint}' RETURN j.min_angle, j.max_angle"
        )
        if not result.has_next():
            return {"verifiable": False, "passed": None, "reason": "joint not found"}
        row = result.get_next()
        min_a, max_a = float(row[0]), float(row[1])
        x = Real("x"); s = Solver()
        s.add(x == angle); s.add(x >= min_a, x <= max_a)
        if s.check() == sat:
            return {"verifiable": True, "passed": True, "reason": f"Z3 proves {angle} in [{min_a}, {max_a}]"}
        return {"verifiable": True, "passed": False, "reason": f"Z3 refutes: {angle} not in [{min_a}, {max_a}]"}

    def verify_force_within_limit(self, tool: str, force: float) -> Dict[str, Any]:
        if not self.z3_available:
            return {"verifiable": False, "passed": None, "reason": "Z3 not installed"}
        result = self.graph.conn.execute(
            f"MATCH (t:Tool) WHERE t.name = '{tool}' RETURN t.max_force"
        )
        if not result.has_next():
            return {"verifiable": False, "passed": None, "reason": "tool not found"}
        max_force = float(result.get_next()[0])
        x = Real("x"); s = Solver()
        s.add(x == force); s.add(x >= 0, x <= max_force)
        if s.check() == sat:
            return {"verifiable": True, "passed": True, "reason": f"Z3 proves {force}N in [0, {max_force}N]"}
        return {"verifiable": True, "passed": False, "reason": f"Z3 refutes: {force}N not in [0, {max_force}N]"}

    def verify_reachability(self, point: List[float], max_reach: float = 17.6) -> Dict[str, Any]:
        if not self.z3_available:
            return {"verifiable": False, "passed": None, "reason": "Z3 not installed"}
        dist = sqrt(sum(float(c) ** 2 for c in point))
        x = Real("x"); s = Solver()
        s.add(x == dist); s.add(x <= max_reach)
        if s.check() == sat:
            return {"verifiable": True, "passed": True, "reason": f"Z3 proves reachable ({dist:.2f} <= {max_reach})"}
        return {"verifiable": True, "passed": False, "reason": f"Z3 refutes: {dist:.2f} > {max_reach}"}

    def verify_clearance(self, point: List[float]) -> Dict[str, Any]:
        if not self.z3_available:
            return {"verifiable": False, "passed": None, "reason": "Z3 not installed"}
        result = self.graph.conn.execute(
            "MATCH (o:Obstacle) RETURN o.name, o.x, o.y, o.z, o.radius, o.clearance"
        )
        violations = []
        while result.has_next():
            row = result.get_next()
            name, ox, oy, oz, radius, clearance = row
            dx = point[0] - float(ox); dy = point[1] - float(oy); dz = point[2] - float(oz)
            dist = sqrt(dx*dx + dy*dy + dz*dz)
            required = float(radius) + float(clearance)
            x = Real("x"); s = Solver()
            s.add(x == dist); s.add(x >= required)
            if s.check() != sat:
                violations.append(f"{name} (dist {dist:.2f} < need {required:.2f})")
        if violations:
            return {"verifiable": True, "passed": False, "reason": f"Z3 refutes: {', '.join(violations)}"}
        return {"verifiable": True, "passed": True, "reason": "Z3 proves clearance"}
