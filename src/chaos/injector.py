"""
CINT-70 Chaos Injection Suite
Injects failures to test agent recovery
"""
import random
from typing import Dict, Any, Optional

class ChaosInjector:
    def __init__(self):
        self.active_failures = {}
        self.scenarios = {
            "stuck_joint": self._inject_stuck_joint,
            "camera_glare": self._inject_camera_glare,
            "signal_lag": self._inject_signal_lag,
            "tool_failure": self._inject_tool_failure,
            "environment_drift": self._inject_drift,
        }
    
    def inject(self, failure_type: str) -> Dict[str, Any]:
        """Inject a specific failure"""
        if failure_type in self.scenarios:
            return self.scenarios[failure_type]()
        return {"injected": False, "reason": "Unknown failure type"}
    
    def _inject_stuck_joint(self):
        joint = random.choice(["elbow_pitch", "wrist_roll", "shoulder_yaw"])
        self.active_failures["stuck_joint"] = joint
        return {
            "injected": True,
            "type": "stuck_joint",
            "joint": joint,
            "message": f"WARNING: {joint} actuator stalled!"
        }
    
    def _inject_camera_glare(self):
        self.active_failures["camera_glare"] = True
        return {
            "injected": True,
            "type": "camera_glare",
            "message": "WARNING: All cameras saturated! Switching to blind mode."
        }
    
    def _inject_signal_lag(self):
        lag = random.uniform(1.5, 3.0)
        self.active_failures["signal_lag"] = lag
        return {
            "injected": True,
            "type": "signal_lag",
            "latency_s": lag,
            "message": f"WARNING: Signal latency increased to {lag:.1f}s!"
        }
    
    def _inject_tool_failure(self):
        tool = random.choice(["thermal_applicator", "torque_wrench"])
        self.active_failures["tool_failure"] = tool
        return {
            "injected": True,
            "type": "tool_failure",
            "tool": tool,
            "message": f"ERROR: {tool} reports zero power draw!"
        }
    
    def _inject_drift(self):
        drift = random.uniform(0.2, 0.5)
        self.active_failures["environment_drift"] = drift
        return {
            "injected": True,
            "type": "environment_drift",
            "drift_m": drift,
            "message": f"WARNING: Solar panel position drifted by {drift:.2f}m!"
        }
    
    def reset(self):
        """Clear all active failures"""
        self.active_failures = {}
    
    def is_active(self, failure_type: str) -> bool:
        return failure_type in self.active_failures