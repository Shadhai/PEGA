"""
CINT-70 Constraint Checker
Validates joint limits, thermal limits, and force limits
"""
import json
import csv
from typing import Dict, Any

class ConstraintChecker:
    def __init__(self):
        self.joint_limits = self._load_joint_limits()
        self.thermal_limits = self._load_thermal_limits()
        self.tool_specs = self._load_tool_specs()
    
    def _load_joint_limits(self):
        limits = {}
        try:
            with open("data/raw/spdm_joint_limits.csv") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    limits[row["joint_name"]] = {
                        "min": float(row["min_deg"]),
                        "max": float(row["max_deg"]),
                        "max_velocity": float(row["max_velocity_rad_s"])
                    }
        except:
            pass
        return limits
    
    def _load_thermal_limits(self):
        try:
            with open("data/raw/thermal_constraints.json") as f:
                return json.load(f)
        except:
            return []
    
    def _load_tool_specs(self):
        try:
            with open("data/raw/tool_specifications.json") as f:
                return {t["tool_name"]: t for t in json.load(f)}
        except:
            return {}
    
    def check_joint_limits(self, step: Dict[str, Any]) -> bool:
        """Check if joint angle is within limits"""
        joint = step.get("joint")
        angle = step.get("target_angle_deg")
        
        if not joint or angle is None:
            return True
        
        if joint in self.joint_limits:
            limits = self.joint_limits[joint]
            if angle < limits["min"] or angle > limits["max"]:
                return False
        
        return True
    
    def check_thermal(self, step: Dict[str, Any]) -> bool:
        """Check thermal constraints (simplified)"""
        # In a real system, this would check current temperature
        # against material limits
        return True
    
    def check_force(self, step: Dict[str, Any]) -> bool:
        """Check force limits for tool operations"""
        force = step.get("contact_force_n")
        tool_name = step.get("tool_name")
        
        if not force or not tool_name:
            return True
        
        if tool_name in self.tool_specs:
            max_force = self.tool_specs[tool_name].get("max_contact_force_n", float("inf"))
            if force > max_force:
                return False
        
        return True