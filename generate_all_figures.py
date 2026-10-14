"""Run all figure generators. Outputs to figures/."""
import subprocess, sys
from pathlib import Path

Path("figures").mkdir(exist_ok=True)

scripts = [
    "figures/generate_ablation.py",
    "figures/generate_crossdomain.py",
    "figures/generate_hitl.py",
    "figures/generate_trajectory.py",
]

for script in scripts:
    if not Path(script).exists():
        print(f"⚠️  {script} missing")
        continue
    print(f"\n▶ Running {script}")
    result = subprocess.run([sys.executable, script], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(f"  stderr: {result.stderr[:300]}")

# Copy the existing ROC/PR plot from Kaggle if it exists locally
import shutil
for src in ["logs/benchmarks/roc_pr_curves.png"]:
    if Path(src).exists():
        shutil.copy(src, "figures/roc_pr_curves.png")
        print(f"✅ Copied {src} → figures/roc_pr_curves.png")

print("\n" + "=" * 60)
print("FIGURE GENERATION COMPLETE")
print("=" * 60)
for f in sorted(Path("figures").glob("*")):
    size_kb = f.stat().st_size / 1024
    print(f"  {f.name:30s}  {size_kb:8.1f} KB")