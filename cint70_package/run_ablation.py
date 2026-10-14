"""
Ablation study — full pipeline, 7 configs.
Runs each config with a fresh experience DB so memory doesn't contaminate.

Expected runtime: ~4.5 hours (7 configs × ~40 min each)
"""

import json
import gc
import os
import time
from pathlib import Path
from datetime import datetime

import torch
from rich.console import Console
from rich.table import Table

from src.agent.orchestrator import CINT70Orchestrator

if not torch.cuda.is_available():
    raise SystemExit(
        "GPU not available. Ablation will not run at acceptable speed on CPU.\n"
        "Fix CUDA/GPU before proceeding."
    )
print(f"GPU: {torch.cuda.get_device_name(0)}")
print(f"VRAM free: {torch.cuda.mem_get_info()[0] / 1e9:.2f} GB")

console = Console()


# ----------------------------------------------------------------
# Ablation configs
# ----------------------------------------------------------------
ABLATIONS = [
    ("full",            {}),
    ("no_graph",        {"use_graph": False}),
    ("no_kinematics",   {"use_kinematics": False}),
    ("no_trajectory",   {"use_trajectory": False}),
    ("no_force_check",  {"use_force_check": False}),
    ("graph_only",      {"use_kinematics": False, "use_force_check": False, "use_trajectory": False}),
    ("kinematics_only", {"use_graph": False, "use_force_check": False, "use_trajectory": False}),
]


# ----------------------------------------------------------------
# Helper — reset state between configs
# ----------------------------------------------------------------
def reset_state():
    """Free GPU state and remove files so each config starts fresh."""
    gc.collect()
    torch.cuda.empty_cache()

    for p in ["data/experience.db", "benchmark_progress.json"]:
        if os.path.exists(p):
            try:
                os.remove(p)
            except OSError:
                pass


# ----------------------------------------------------------------
# Load tasks once
# ----------------------------------------------------------------
with open("data/extracted/task_library.json", encoding="utf-8") as f:
    tasks = json.load(f)["tasks"]

console.print(f"[cyan]Loaded {len(tasks)} tasks[/cyan]\n")


# ----------------------------------------------------------------
# Run each config
# ----------------------------------------------------------------
table = Table(title="Ablation Study — Full Pipeline")
table.add_column("Config",     style="cyan")
table.add_column("TP")
table.add_column("FP")
table.add_column("FN")
table.add_column("TN")
table.add_column("Precision")
table.add_column("Recall")
table.add_column("F1")
table.add_column("Time (min)")

results_for_save = []
overall_start = time.time()

for config_index, (name, overrides) in enumerate(ABLATIONS, start=1):
    console.rule(f"[bold]Config {config_index}/{len(ABLATIONS)}: {name}[/bold]")
    config_start = time.time()

    if "orch" in locals():
        del orch
    reset_state()

    base = {
        "use_graph": True,
        "use_kinematics": True,
        "use_trajectory": True,
        "use_force_check": True,
    }
    base.update(overrides)

    orch = CINT70Orchestrator(ablation=base)

    tp = fp = tn = fn = 0
    completed = 0

    for task in tasks:
        task_id = task.get("task_id", "")
        command = task.get("instruction", "")
        is_unsafe = task_id.startswith("unsafe_")

        try:
            if is_unsafe:
                plan = task.get("adversarial_plan", [])
                r = orch.execute_custom_plan(
                    command=command,
                    plan=plan,
                    task_id=task_id,
                )
                approved = bool(r.get("all_checks_passed", False))
                if not approved:
                    tp += 1
                else:
                    fn += 1
            else:
                r = orch.execute(
                    command=command,
                    task_id=task_id,
                    expected_safe=True,
                )
                approved = bool(r.get("all_checks_passed", False))
                if approved:
                    tn += 1
                else:
                    fp += 1
        except Exception as e:
            console.print(f"[red]  Task {task_id} error: {e}[/red]")

        completed += 1

        # Progress every 25 tasks
        if completed % 25 == 0:
            elapsed = time.time() - config_start
            rate = completed / elapsed if elapsed > 0 else 0
            remaining = (len(tasks) - completed) / rate if rate > 0 else 0
            console.print(
                f"  [{completed}/{len(tasks)}]  "
                f"TP={tp}  FP={fp}  FN={fn}  TN={tn}  "
                f"~{remaining/60:.1f} min left"
            )

    p = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * p * rec / (p + rec) if (p + rec) else 0.0

    config_time = (time.time() - config_start) / 60

    table.add_row(
        name,
        str(tp), str(fp), str(fn), str(tn),
        f"{p:.3f}", f"{rec:.3f}", f"{f1:.3f}",
        f"{config_time:.1f}",
    )

    results_for_save.append({
        "config": name,
        "overrides": overrides,
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "precision": p, "recall": rec, "f1": f1,
        "time_minutes": config_time,
    })

    # Save partial results after each config
    with open("logs/benchmarks/ablation_results.json", "w") as f:
        json.dump(results_for_save, f, indent=2)

    console.print(f"[green]  Config {name} finished in {config_time:.1f} min[/green]\n")


# ----------------------------------------------------------------
# Final report
# ----------------------------------------------------------------
overall_time = (time.time() - overall_start) / 60

console.print("\n")
console.print(table)
console.print(f"\n[bold]Total time: {overall_time:.1f} min ({overall_time/60:.2f} hours)[/bold]")
console.print(f"Saved: logs/benchmarks/ablation_results.json")