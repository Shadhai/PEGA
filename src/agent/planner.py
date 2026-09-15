"""
CINT-70 Planner — Production Grade
LLM for task classification + symbolic adaptive planner
"""
import torch
import json
import random
from typing import List, Dict, Any

from transformers import AutoModelForCausalLM, AutoTokenizer

from src.graph.queries import ConstraintQueries
from src.validator.kinematics import KinematicsValidator
from src.memory.experience import ExperienceMemory


class Planner:
    def __init__(self):
        print("  Loading planner model...")
        self.tokenizer = AutoTokenizer.from_pretrained(
            "./models/qwen2.5-1.5b",
            trust_remote_code=True
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            "./models/qwen2.5-1.5b",
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True
        )
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.memory = ExperienceMemory()
        print("  Planner ready!")

    # ------------------------------------------------------------------
    # MAIN ENTRY
    # ------------------------------------------------------------------
    def generate(self, command: str, documents: List[Dict], constraints: List[Dict]) -> List[Dict]:
        # 1. Classify task with LLM (or fallback)
        task_info = self._classify_command(command)
        task_type = task_info.get("task_type", "general")
        tool = task_info.get("tool", "thermal_applicator")

        # 2. Find safe coordinates (memory -> candidates -> random search)
        safe_coords = self._find_safe_coordinates(task_type, constraints)

        # 3. Build plan using symbolic library
        return self._build_plan(task_type, tool, safe_coords)

    # ------------------------------------------------------------------
    # LLM CLASSIFICATION
    # ------------------------------------------------------------------
    def _classify_command(self, command: str) -> Dict[str, str]:
        prompt = f"""Extract the following from the command as JSON:
- task_type: one of [repair, inspect, replace, sample, leak_check]
- tool: the primary tool mentioned (e.g., thermal_applicator, inspection_camera, torque_wrench, sample_scoop, leak_detector)
- target: what is being repaired/inspected/replaced (short phrase)

Command: {command}

Return ONLY valid JSON, no other text.
JSON:"""

        try:
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=60,
                    do_sample=False,          # No temperature/top_p warnings
                    pad_token_id=self.tokenizer.eos_token_id
                )
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except Exception:
            pass

        return self._fallback_classify(command)

    def _fallback_classify(self, command: str) -> Dict[str, str]:
        cmd = command.lower()
        if "repair" in cmd or "thermal" in cmd or "blanket" in cmd:
            return {"task_type": "repair", "tool": "thermal_applicator", "target": "panel_3"}
        if "inspect" in cmd or "camera" in cmd or "micrometeoroid" in cmd:
            return {"task_type": "inspect", "tool": "inspection_camera", "target": "antenna"}
        if "replace" in cmd or "wrench" in cmd or "tool change" in cmd:
            return {"task_type": "replace", "tool": "torque_wrench", "target": "holster"}
        if "sample" in cmd or "scoop" in cmd or "regolith" in cmd:
            return {"task_type": "sample", "tool": "sample_scoop", "target": "surface"}
        if "leak" in cmd or "detector" in cmd or "ammonia" in cmd:
            return {"task_type": "leak_check", "tool": "leak_detector", "target": "radiator"}
        return {"task_type": "general", "tool": "thermal_applicator", "target": "panel"}

    # ------------------------------------------------------------------
    # ADAPTIVE SAFE COORDINATE SEARCH
    # ------------------------------------------------------------------
    def _find_safe_coordinates(self, task_type: str, constraints: List[Dict]) -> List[float]:
        graph = ConstraintQueries()
        kin = KinematicsValidator()

        # ---- 1. Memory-first: use previously successful coordinates ----
        try:
            successful = self.memory.get_successful_strategies(task_type)
            for strat in successful:
                coords = strat.get("safe_coordinates")
                if coords and len(coords) == 3:
                    reachable, _ = kin.is_reachable(coords)
                    if reachable and graph.check_collision(coords[0], coords[1], coords[2])["passed"]:
                        return coords
        except Exception:
            pass  # Memory is non-critical

        # ---- 2. Task-specific candidate points ----
        candidates = {
            "repair": [[1.5, 0.2, 1.8], [2.0, -0.5, 2.0], [1.2, -0.8, 1.5], [5.0, 0.0, 2.0]],
            "inspect": [[-0.5, 0.0, 2.3], [-1.0, -0.5, 2.0], [-0.8, -0.3, 2.2], [-5.0, 0.0, 3.0]],
            "replace": [[1.2, -0.3, 1.0], [1.0, 0.5, 0.8], [1.2, 0.3, 1.0], [3.0, 0.0, 1.5]],
            "sample": [[1.5, 0.0, 1.8], [1.0, -0.5, 1.5], [2.0, 0.0, 0.5]],
            "leak_check": [[-0.5, 0.5, 2.0], [-0.8, 0.2, 2.2], [-3.0, 0.0, 2.0]],
        "general": [[1.5, 0.0, 1.8]]
        }
        points = candidates.get(task_type, [[1.5, 0.0, 1.8]])

        for point in points:
            reachable, _ = kin.is_reachable(point)
            if reachable and graph.check_collision(point[0], point[1], point[2])["passed"]:
                return point

        # ---- 3. Randomized workspace sampling ----
        bounds = {
    "x": (-20.0, 20.0),
    "y": (-20.0, 20.0),
    "z": (-5.0, 10.0)
}
        for _ in range(200):  # 200 attempts < 1 sec on CPU
            pt = [
                random.uniform(*bounds["x"]),
                random.uniform(*bounds["y"]),
                random.uniform(*bounds["z"])
            ]
            reachable, _ = kin.is_reachable(pt)
            if reachable and graph.check_collision(pt[0], pt[1], pt[2])["passed"]:
                return pt

        # ---- 4. Fallback (will trigger recovery if unsafe) ----
        return points[0]

    # ------------------------------------------------------------------
    # PLAN LIBRARY
    # ------------------------------------------------------------------
    def _build_plan(self, task_type: str, tool: str, coords: List[float]) -> List[Dict]:
        stow = {
            "step_id": 99,
            "action": "move_joint",
            "joint": "shoulder_pitch",
            "target_angle_deg": 0.0,
            "velocity_rad_s": 0.3,
            "rationale": "Return arm to stow position"
        }

        if task_type == "repair":
            return [
                {"step_id": 1, "action": "move_joint", "joint": "shoulder_pitch", "target_angle_deg": 45.0, "velocity_rad_s": 0.3, "rationale": "Raise arm to safe height"},
                {"step_id": 2, "action": "move_joint", "joint": "shoulder_yaw", "target_angle_deg": 30.0, "velocity_rad_s": 0.3, "rationale": "Rotate toward starboard approach"},
                {"step_id": 3, "action": "move_joint", "joint": "elbow_pitch", "target_angle_deg": -40.0, "velocity_rad_s": 0.2, "rationale": "Extend toward panel"},
                {"step_id": 4, "action": "grasp_tool", "tool_name": tool, "rationale": "Retrieve repair tool"},
                {"step_id": 5, "action": "move_to", "target_coordinates": coords, "rationale": "Position tool at repair site"},
                {"step_id": 6, "action": "apply_tool", "tool_name": tool, "contact_force_n": 10.0, "duration_s": 30, "target_coordinates": coords, "rationale": "Repair damage"},
                {"step_id": 7, "action": "return_tool", "tool_name": tool, "rationale": "Stow tool"},
                stow
            ]

        if task_type == "inspect":
            return [
                {"step_id": 1, "action": "move_joint", "joint": "shoulder_pitch", "target_angle_deg": 30.0, "velocity_rad_s": 0.3, "rationale": "Raise arm"},
                {"step_id": 2, "action": "move_joint", "joint": "shoulder_yaw", "target_angle_deg": -20.0, "velocity_rad_s": 0.2, "rationale": "Rotate toward antenna"},
                {"step_id": 3, "action": "grasp_tool", "tool_name": "inspection_camera", "rationale": "Retrieve camera"},
                {"step_id": 4, "action": "move_to", "target_coordinates": coords, "rationale": "Position camera"},
                {"step_id": 5, "action": "apply_tool", "tool_name": "inspection_camera", "contact_force_n": 2.0, "duration_s": 60, "target_coordinates": coords, "rationale": "Capture imagery"},
                {"step_id": 6, "action": "return_tool", "tool_name": "inspection_camera", "rationale": "Return camera"},
                stow
            ]

        if task_type == "replace":
            return [
                {"step_id": 1, "action": "move_joint", "joint": "shoulder_pitch", "target_angle_deg": 20.0, "velocity_rad_s": 0.3, "rationale": "Position arm near holsters"},
                {"step_id": 2, "action": "move_to", "target_coordinates": coords, "rationale": "Approach holster"},
                {"step_id": 3, "action": "grasp_tool", "tool_name": tool, "rationale": "Grasp failed tool"},
                {"step_id": 4, "action": "move_to", "target_coordinates": [c + 0.3 for c in coords], "rationale": "Move to disposal"},
                {"step_id": 5, "action": "move_to", "target_coordinates": [c - 0.3 for c in coords], "rationale": "Approach backup holster"},
                {"step_id": 6, "action": "grasp_tool", "tool_name": tool, "rationale": "Retrieve backup tool"},
                {"step_id": 7, "action": "move_to", "target_coordinates": coords, "rationale": "Place backup in primary holster"},
                {"step_id": 8, "action": "return_tool", "tool_name": tool, "rationale": "Stow"},
                stow
            ]

        if task_type == "sample":
            return [
                {"step_id": 1, "action": "move_joint", "joint": "shoulder_pitch", "target_angle_deg": 30.0, "velocity_rad_s": 0.3, "rationale": "Raise arm"},
                {"step_id": 2, "action": "grasp_tool", "tool_name": "sample_scoop", "rationale": "Retrieve scoop"},
                {"step_id": 3, "action": "move_to", "target_coordinates": coords, "rationale": "Position scoop over surface"},
                {"step_id": 4, "action": "apply_tool", "tool_name": "sample_scoop", "contact_force_n": 5.0, "duration_s": 20, "target_coordinates": coords, "rationale": "Collect sample"},
                {"step_id": 5, "action": "return_tool", "tool_name": "sample_scoop", "rationale": "Stow scoop"},
                stow
            ]

        if task_type == "leak_check":
            return [
                {"step_id": 1, "action": "move_joint", "joint": "shoulder_pitch", "target_angle_deg": 30.0, "velocity_rad_s": 0.3, "rationale": "Raise arm"},
                {"step_id": 2, "action": "grasp_tool", "tool_name": "leak_detector", "rationale": "Retrieve leak detector"},
                {"step_id": 3, "action": "move_to", "target_coordinates": coords, "rationale": "Position detector near radiator"},
                {"step_id": 4, "action": "apply_tool", "tool_name": "leak_detector", "contact_force_n": 1.0, "duration_s": 60, "target_coordinates": coords, "rationale": "Scan for ammonia"},
                {"step_id": 5, "action": "return_tool", "tool_name": "leak_detector", "rationale": "Stow detector"},
                stow
            ]

        # Generic fallback
        return [
            {"step_id": 1, "action": "move_joint", "joint": "shoulder_pitch", "target_angle_deg": 30.0, "velocity_rad_s": 0.3, "rationale": "Move to operational position"},
            {"step_id": 2, "action": "grasp_tool", "tool_name": tool, "rationale": "Retrieve tool"},
            {"step_id": 3, "action": "apply_tool", "tool_name": tool, "contact_force_n": 10.0, "duration_s": 30, "target_coordinates": coords, "rationale": "Execute task"},
            {"step_id": 4, "action": "return_tool", "tool_name": tool, "rationale": "Return tool"},
            stow
        ]