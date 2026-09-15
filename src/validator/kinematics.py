"""
CINT-70 Kinematics Validator - Production Grade
Proper forward kinematics using Denavit-Hartenberg parameters
"""
import numpy as np
from typing import Dict, List, Tuple, Any

class KinematicsValidator:
    def __init__(self):
        # DH Parameters for 6-DOF space robotic arm
        # [a, alpha, d, theta_offset]
        self.dh_params = [
            [0.0, np.pi/2, 0.5, 0.0],      # Joint 1: shoulder_pitch
            [0.3, 0.0, 0.0, 0.0],           # Joint 2: shoulder_yaw
            [0.3, 0.0, 0.0, -np.pi/2],       # Joint 3: elbow_pitch
            [0.0, np.pi/2, 0.2, 0.0],        # Joint 4: wrist_roll
            [0.0, -np.pi/2, 0.0, 0.0],       # Joint 5: wrist_pitch
            [0.0, 0.0, 0.15, 0.0],           # Joint 6: wrist_yaw
        ]
        
        self.joint_names = [
            "shoulder_pitch", "shoulder_yaw", "elbow_pitch",
            "wrist_roll", "wrist_pitch", "wrist_yaw"
        ]
        
        self.max_reach = 17.6 # meters
    
    def dh_transform(self, a: float, alpha: float, d: float, theta: float) -> np.ndarray:
        """Compute DH transformation matrix"""
        ct = np.cos(theta)
        st = np.sin(theta)
        ca = np.cos(alpha)
        sa = np.sin(alpha)
        
        return np.array([
            [ct, -st*ca,  st*sa, a*ct],
            [st,  ct*ca, -ct*sa, a*st],
            [0,      sa,     ca,    d],
            [0,       0,      0,    1]
        ])
    
    def forward_kinematics(self, joint_angles: Dict[str, float]) -> Tuple[np.ndarray, List[np.ndarray]]:
        """Compute end-effector position and all joint positions"""
        T = np.eye(4)
        positions = [T[:3, 3].copy()]
        
        for i, name in enumerate(self.joint_names):
            if name in joint_angles:
                a, alpha, d, offset = self.dh_params[i]
                theta = np.radians(joint_angles[name]) + offset
                T_i = self.dh_transform(a, alpha, d, theta)
                T = T @ T_i
                positions.append(T[:3, 3].copy())
        
        return T[:3, 3], positions
    
    def is_reachable(self, target: List[float]) -> Tuple[bool, float]:
        """Check if target is within workspace"""
        target = np.array(target)
        base = np.array([0.0, 0.0, 0.0])
        distance = np.linalg.norm(target - base)
        return distance <= self.max_reach, distance
    
    def check_collision_with_obstacles(self, positions: List[np.ndarray], 
                                         obstacles: List[Dict]) -> List[Dict]:
        """Check if any arm segment collides with obstacles"""
        violations = []
        
        for i in range(len(positions) - 1):
            p1 = positions[i]
            p2 = positions[i + 1]
            
            for obs in obstacles:
                obs_pos = np.array(obs.get("pos", [0, 0, 0]))
                clearance = obs.get("clearance", 0.5)
                
                # Minimum distance from line segment to sphere
                distance = self._point_to_segment_distance(obs_pos, p1, p2)
                
                if distance < clearance:
                    violations.append({
                        "segment": i,
                        "obstacle": obs.get("name", "unknown"),
                        "distance": float(distance),
                        "clearance": clearance
                    })
        
        return violations
    
    def _point_to_segment_distance(self, point: np.ndarray, 
                                      seg_start: np.ndarray, 
                                      seg_end: np.ndarray) -> float:
        """Minimum distance from point to line segment"""
        seg = seg_end - seg_start
        seg_len_sq = np.dot(seg, seg)
        
        if seg_len_sq == 0:
            return np.linalg.norm(point - seg_start)
        
        t = max(0, min(1, np.dot(point - seg_start, seg) / seg_len_sq))
        projection = seg_start + t * seg
        return np.linalg.norm(point - projection)
    
    def validate(self, step: Dict[str, Any]) -> bool:
        """Validate a single step"""
        action = step.get("action", "")
        
        if action in ["move_joint", "move_to"]:
            target = step.get("target_coordinates")
            if target:
                reachable, _ = self.is_reachable(target)
                return reachable
        
        return True