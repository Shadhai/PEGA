"""
CINT-70 Collision Detector
Simple collision checking for robotic arm operations
"""
import numpy as np
from typing import Dict, Any, List

class CollisionDetector:
    def __init__(self):
        # Obstacle positions in 3D space
        self.obstacles = {
            "solar_panel": {
                "position": np.array([0.8, 0.5, 1.8]),
                "radius": 0.3,
                "clearance": 0.5
            },
            "antenna_array": {
                "position": np.array([-0.5, 0.3, 2.0]),
                "radius": 0.2,
                "clearance": 0.3
            },
            "rover_body": {
                "position": np.array([0, 0, 0.5]),
                "radius": 1.0,
                "clearance": 0.2
            }
        }
    
    def check(self, step: Dict[str, Any], constraints: List[Dict] = None) -> bool:
        """Check if step causes collision"""
        action = step.get("action", "")
        
        if action not in ["move_joint", "move_to"]:
            return True  # Static actions don't cause collisions
        
        # Get arm position (simplified)
        arm_position = self._estimate_arm_position(step)
        
        for name, obs in self.obstacles.items():
            distance = np.linalg.norm(arm_position - obs["position"])
            if distance < (obs["radius"] + obs["clearance"]):
                return False
        
        return True
    
    def _estimate_arm_position(self, step: Dict[str, Any]) -> np.ndarray:
        """Estimate arm position from joint angles"""
        joint = step.get("joint", "")
        angle = step.get("target_angle_deg", 0)
        angle_rad = np.radians(angle)
        
        # Base position + joint contribution
        position = np.array([1.5, 0.0, 1.5])
        
        offsets = {
            "shoulder_pitch": np.array([0.3 * np.cos(angle_rad), 0, 0.3 * np.sin(angle_rad)]),
            "shoulder_yaw": np.array([0.3 * np.cos(angle_rad), 0.3 * np.sin(angle_rad), 0]),
            "elbow_pitch": np.array([0.5 * np.cos(angle_rad), 0, -0.3 * np.sin(angle_rad)]),
            "wrist_roll": np.array([0.2, 0, 0]),
            "wrist_pitch": np.array([0.2 * np.cos(angle_rad), 0, 0.2 * np.sin(angle_rad)]),
            "wrist_yaw": np.array([0, 0.2 * np.sin(angle_rad), 0]),
        }
        
        return position + offsets.get(joint, np.zeros(3))