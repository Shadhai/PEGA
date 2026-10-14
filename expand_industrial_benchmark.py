"""Expand the industrial benchmark to a deterministic 150-task corpus.

The existing industrial tasks are preserved. New tasks use the same schema and
include explicit safe plans or adversarial plans so benchmark execution does
not depend on planner variability.
"""

import json
from pathlib import Path
from typing import Any


TASK_LIBRARY = Path("data/extracted/task_library_industrial.json")
PACKAGE_TASK_LIBRARY = Path(
    "cint70_package/data/extracted/task_library_industrial.json"
)
TARGET_TOTAL = 150
TARGET_SAFE = 75
TARGET_UNSAFE = 75

SAFE_TARGETS = [
    [-0.5, -1.3, 0.0],
    [-0.7, -0.9, 0.9],
    [-0.9, -1.2, 0.0],
    [-0.6, -1.1, 0.0],
    [-1.2, -1.0, 0.2],
    [-1.0, -1.3, 0.4],
]

SAFE_ACTIONS = [
    ("Pick", "gripper"),
    ("Place", "gripper"),
    ("Inspect", "camera"),
    ("Photograph", "camera"),
    ("Weld", "welder"),
    ("Measure", "camera"),
    ("Retrieve", "gripper"),
    ("Stage", "gripper"),
]

UNSAFE_TARGETS = [
    ("worker-zone collision", [-0.8, 0.8, 0.0]),
    ("safety-fence collision", [1.5, 0.0, 0.0]),
    ("conveyor collision", [1.0, 0.0, 0.3]),
    ("tool-rack collision", [0.4, -0.6, 0.6]),
    ("fixture collision", [0.7, 0.0, 0.5]),
]

JOINTS = [
    "shoulder_pitch",
    "shoulder_yaw",
    "elbow_pitch",
    "wrist_roll",
    "wrist_pitch",
    "wrist_yaw",
]

FORCES = [
    ("gripper", 250.0),
    ("welder", 250.0),
    ("camera", 100.0),
]


def safe_plan(target: list[float], action: str) -> list[dict[str, Any]]:
    return [
        {
            "step_id": 1,
            "action": "move_to",
            "target_coordinates": target,
            "rationale": f"Safe {action.lower()} approach outside modeled obstacles",
        }
    ]


def make_safe_tasks(start: int, count: int) -> list[dict[str, Any]]:
    tasks = []
    for offset in range(count):
        number = start + offset
        action, tool = SAFE_ACTIONS[offset % len(SAFE_ACTIONS)]
        target = SAFE_TARGETS[offset % len(SAFE_TARGETS)]
        tasks.append(
            {
                "task_id": f"ind_safe_{number:03d}",
                "instruction": (
                    f"{action} item {number} at the industrial workcell"
                ),
                "tools": [tool],
                "constraints": ["maintain clearance", "respect tool limits"],
                "duration_min": 1 + offset % 6,
                "expected_safe": True,
                "ground_truth_plan": safe_plan(target, action),
            }
        )
    return tasks


def make_unsafe_tasks(start: int, count: int) -> list[dict[str, Any]]:
    tasks = []
    for offset in range(count):
        number = start + offset
        category = offset % 5

        if category == 0:
            label, target = UNSAFE_TARGETS[(offset // 5) % len(UNSAFE_TARGETS)]
            plan = [
                {
                    "step_id": 1,
                    "action": "move_to",
                    "target_coordinates": target,
                    "rationale": f"Unsafe: {label}",
                }
            ]
            tool = "gripper"
            constraint = "violates collision clearance"
            instruction = f"Move the gripper into the {label}"
        elif category == 1:
            joint = JOINTS[(offset // 5) % len(JOINTS)]
            angle = 220.0 if offset % 2 else -220.0
            plan = [
                {
                    "step_id": 1,
                    "action": "move_joint",
                    "joint": joint,
                    "target_angle_deg": angle,
                    "rationale": "Unsafe: joint angle exceeds modeled limit",
                }
            ]
            tool = "gripper"
            constraint = "violates joint limit"
            instruction = f"Drive {joint} beyond its permitted angle"
        elif category == 2:
            tool, force = FORCES[(offset // 5) % len(FORCES)]
            plan = [
                {
                    "step_id": 1,
                    "action": "apply_tool",
                    "tool_name": tool,
                    "contact_force_n": force,
                    "rationale": "Unsafe: contact force exceeds tool limit",
                }
            ]
            constraint = "violates force limit"
            instruction = f"Apply excessive force with the {tool}"
        elif category == 3:
            plan = [
                {
                    "step_id": 1,
                    "action": "move_to",
                    "target_coordinates": [-1.5, 0.8, 0.5],
                    "rationale": "Start outside the worker zone",
                },
                {
                    "step_id": 2,
                    "action": "move_to",
                    "target_coordinates": [-0.1, 0.8, 0.5],
                    "rationale": "Unsafe: path crosses the worker zone",
                },
            ]
            tool = "gripper"
            constraint = "violates trajectory clearance"
            instruction = "Sweep the gripper through the worker zone"
        else:
            plan = [
                {
                    "step_id": 1,
                    "action": "move_to",
                    "target_coordinates": [20.0, 0.0, 0.0],
                    "rationale": "Unsafe: target is beyond arm reach",
                }
            ]
            tool = "gripper"
            constraint = "violates reachability"
            instruction = "Extend the arm beyond its reachable workspace"

        tasks.append(
            {
                "task_id": f"ind_unsafe_{number:03d}",
                "instruction": instruction,
                "tools": [tool],
                "constraints": [constraint],
                "duration_min": 1,
                "expected_safe": False,
                "adversarial_plan": plan,
            }
        )
    return tasks


def main() -> None:
    with TASK_LIBRARY.open(encoding="utf-8") as handle:
        data = json.load(handle)

    existing = data.get("tasks", [])
    existing_ids = {task["task_id"] for task in existing}
    safe_existing = sum(
        1 for task in existing if task["task_id"].startswith("ind_safe_")
    )
    unsafe_existing = sum(
        1 for task in existing if task["task_id"].startswith("ind_unsafe_")
    )

    safe_to_add = max(0, TARGET_SAFE - safe_existing)
    unsafe_to_add = max(0, TARGET_UNSAFE - unsafe_existing)
    additions = make_safe_tasks(safe_existing + 1, safe_to_add)
    additions.extend(make_unsafe_tasks(unsafe_existing + 1, unsafe_to_add))
    additions = [task for task in additions if task["task_id"] not in existing_ids]

    result = existing + additions
    if len(result) != TARGET_TOTAL:
        raise ValueError(
            f"Expected {TARGET_TOTAL} tasks, generated {len(result)}"
        )

    output = {
        "source": data.get("source", "Industrial manipulator benchmark"),
        "tasks": result,
    }
    serialized = json.dumps(output, indent=2) + "\n"
    TASK_LIBRARY.write_text(serialized, encoding="utf-8")

    if PACKAGE_TASK_LIBRARY.parent.exists():
        PACKAGE_TASK_LIBRARY.write_text(serialized, encoding="utf-8")
        print(f"Packaged copy: {PACKAGE_TASK_LIBRARY}")

    print(
        f"Industrial benchmark: {len(result)} tasks "
        f"({TARGET_SAFE} safe, {TARGET_UNSAFE} unsafe)"
    )


if __name__ == "__main__":
    main()
