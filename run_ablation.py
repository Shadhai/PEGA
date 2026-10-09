"""
Ablation study — measure each component's contribution.
"""
import json
from pathlib import Path
from src.agent.orchestrator import CINT70Orchestrator
from rich.console import Console
from rich.table import Table

console = Console()

ABLATIONS = [
    ("full",            {}),
    ("no_graph",        {"use_graph": False}),
    ("no_kinematics",   {"use_kinematics": False}),
    ("no_trajectory",   {"use_trajectory": False}),
    ("no_force_check",  {"use_force_check": False}),
    ("graph_only",      {"use_kinematics": False, "use_force_check": False, "use_trajectory": False}),
    ("kinematics_only", {"use_graph": False, "use_force_check": False, "use_trajectory": False}),
]

with open("data/extracted/task_library.json", encoding="utf-8") as f:
    tasks = json.load(f)["tasks"]

table = Table(title="Ablation Study — Component Contribution")
table.add_column("Config", style="cyan")
table.add_column("TP")
table.add_column("FP")
table.add_column("FN")
table.add_column("Precision")
table.add_column("Recall")
table.add_column("F1")

for name, overrides in ABLATIONS:
    base = {
        "use_graph": True,
        "use_kinematics": True,
        "use_trajectory": True,
        "use_force_check": True,
    }
    base.update(overrides)

    orch = CINT70Orchestrator(ablation=base)

    tp = fp = tn = fn = 0
    for task in tasks:
        task_id = task.get("task_id", "")
        if task_id.startswith("unsafe_"):
            plan = task.get("adversarial_plan", [])
            r = orch.execute_custom_plan(
                command=task["instruction"],
                plan=plan,
                task_id=task_id,
            )
            if not r.get("all_checks_passed", False):
                tp += 1
            else:
                fn += 1
        else:
            r = orch.execute(
                task["instruction"],
                task_id=task_id,
                expected_safe=True,
            )
            if r.get("all_checks_passed", False):
                tn += 1
            else:
                fp += 1

    p = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * p * rec / (p + rec) if (p + rec) else 0.0

    table.add_row(name, str(tp), str(fp), str(fn), f"{p:.3f}", f"{rec:.3f}", f"{f1:.3f}")

console.print(table)

# Save for paper
results = []
for row in table.rows:
    results.append({
        "config": str(row.cells[0]),
        "tp": int(str(row.cells[1])),
        "fp": int(str(row.cells[2])),
        "fn": int(str(row.cells[3])),
        "precision": float(str(row.cells[4])),
        "recall": float(str(row.cells[5])),
        "f1": float(str(row.cells[6])),
    })

out = Path("logs/benchmarks/ablation_results.json")
with open(out, "w") as f:
    json.dump(results, f, indent=2)
console.print(f"\nSaved: {out}")    