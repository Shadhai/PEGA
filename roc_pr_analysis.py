"""
ROC / PR curve analysis for CINT-70 benchmark.
Sweeps trust_score threshold, computes detection performance against ground truth.
"""

import json
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import (
    roc_curve, auc,
    precision_recall_curve, average_precision_score,
)


# ----------------------------------------------------------------
# Load latest benchmark
# --------------------------------------------------------------
bench_files = sorted(Path("logs/benchmarks").glob("benchmark_*.json"))
if not bench_files:
    raise SystemExit("No benchmark files found in logs/benchmarks/")

# Skip the FINAL copy and roc_pr_data.json
bench_files = [
    f for f in bench_files
    if f.name != "benchmark_FINAL.json"
]
if not bench_files:
    raise SystemExit("No non-FINAL benchmark files found")
latest = bench_files[-1]
print(f"Loading: {latest}\n")

with open(latest, encoding="utf-8") as f:
    data = json.load(f)

results = data["results"]
print(f"Total runs: {len(results)}\n")


# ----------------------------------------------------------------
# Build (score, label) arrays.
#
# Convention:
#   Positive class = UNSAFE (the thing we want to detect)
#   Detector score = 1 - trust_score
#     (high score → plan looks unsafe → should be rejected)
# ----------------------------------------------------------------
scores = []
labels = []  # 1 = unsafe, 0 = safe

for r in results:
    trust = float(r.get("trust_score", 1.0))
    is_safe = bool(r.get("expected_safe", True))

    scores.append(1.0 - trust)     # "unsafe-ness" score
    labels.append(0 if is_safe else 1)

scores = np.array(scores)
labels = np.array(labels)

n_safe = int((labels == 0).sum())
n_unsafe = int((labels == 1).sum())
print(f"Safe tasks:   {n_safe}")
print(f"Unsafe tasks: {n_unsafe}\n")


# ----------------------------------------------------------------
# ROC curve
# ----------------------------------------------------------------
fpr, tpr, roc_thresholds = roc_curve(labels, scores)
roc_auc = auc(fpr, tpr)

# ----------------------------------------------------------------
# PR curve
# ----------------------------------------------------------------
precision, recall, pr_thresholds = precision_recall_curve(labels, scores)
ap = average_precision_score(labels, scores)


# ----------------------------------------------------------------
# Print scalar summary
# ----------------------------------------------------------------
print("=" * 60)
print("SCALAR METRICS")
print("=" * 60)
print(f"AUC-ROC:  {roc_auc:.4f}")
print(f"AUC-PR:   {ap:.4f}")
print()

# Find operating points at common thresholds
for thr in [0.5, 0.7, 0.85, 0.95]:
    # Predict unsafe if score >= thr
    pred_unsafe = scores >= thr

    tp = int(((pred_unsafe == 1) & (labels == 1)).sum())
    fp = int(((pred_unsafe == 1) & (labels == 0)).sum())
    fn = int(((pred_unsafe == 0) & (labels == 1)).sum())
    tn = int(((pred_unsafe == 0) & (labels == 0)).sum())

    prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0

    print(f"Threshold = {thr:.2f}  (reject if unsafe-ness >= {thr})")
    print(f"  TP={tp:3d}  FP={fp:3d}  TN={tn:3d}  FN={fn:3d}")
    print(f"  Precision = {prec:.3f}  Recall = {rec:.3f}  F1 = {f1:.3f}")
    print()

print("=" * 60)
print()


# ----------------------------------------------------------------
# Plot ROC + PR side by side
# ----------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))

# ROC
axes[0].plot(fpr, tpr, color="#00b4d8", lw=2.5,
             label=f"ROC (AUC = {roc_auc:.4f})")
axes[0].plot([0, 1], [0, 1], "k--", lw=1, alpha=0.4,
             label="Random baseline")
axes[0].set_xlabel("False Positive Rate")
axes[0].set_ylabel("True Positive Rate")
axes[0].set_title("ROC Curve — Unsafe Action Detection")
axes[0].legend(loc="lower right", frameon=False)
axes[0].grid(alpha=0.3)

# PR
axes[1].plot(recall, precision, color="#e63946", lw=2.5,
             label=f"PR (AUC = {ap:.4f})")
axes[1].axhline(y=n_unsafe / (n_safe + n_unsafe), color="k", ls="--",
                lw=1, alpha=0.4, label="Class prior")
axes[1].set_xlabel("Recall")
axes[1].set_ylabel("Precision")
axes[1].set_title("Precision–Recall Curve — Unsafe Action Detection")
axes[1].legend(loc="lower left", frameon=False)
axes[1].grid(alpha=0.3)

plt.tight_layout()

out_png = Path("logs/benchmarks/roc_pr_curves.png")
plt.savefig(out_png, dpi=150, bbox_inches="tight")
print(f"Plot saved: {out_png}")


# ----------------------------------------------------------------
# Save raw curve data for the paper
# ----------------------------------------------------------------
curve_data = {
    "auc_roc": float(roc_auc),
    "auc_pr": float(ap),
    "n_safe": n_safe,
    "n_unsafe": n_unsafe,
    "roc": {
        "fpr": fpr.tolist(),
        "tpr": tpr.tolist(),
        "thresholds": roc_thresholds.tolist(),
    },
    "pr": {
        "precision": precision.tolist(),
        "recall": recall.tolist(),
        "thresholds": pr_thresholds.tolist() if len(pr_thresholds) else [],
    },
}

out_json = Path("logs/benchmarks/roc_pr_data.json")
with open(out_json, "w") as f:
    json.dump(curve_data, f, indent=2)
print(f"Data saved: {out_json}")

# (venv) PS D:\final yeat project> & "d:\final yeat project\venv\Scripts\python.exe" "d:/final yeat project/roc_pr_analysis.py"
# Loading: logs\benchmarks\benchmark_FINAL.json

# Total runs: 290

# Safe tasks:   215
# Unsafe tasks: 75

# ============================================================
# SCALAR METRICS
# ============================================================
# AUC-ROC:  1.0000
# AUC-PR:   1.0000

# Threshold = 0.50  (reject if unsafe-ness >= 0.5)
#   TP= 75  FP=  0  TN=215  FN=  0
#   Precision = 1.000  Recall = 1.000  F1 = 1.000

# Threshold = 0.70  (reject if unsafe-ness >= 0.7)
#   TP= 75  FP=  0  TN=215  FN=  0
#   Precision = 1.000  Recall = 1.000  F1 = 1.000

# Threshold = 0.85  (reject if unsafe-ness >= 0.85)
#   TP= 75  FP=  0  TN=215  FN=  0
#   Precision = 1.000  Recall = 1.000  F1 = 1.000

# Threshold = 0.95  (reject if unsafe-ness >= 0.95)
#   TP= 63  FP=  0  TN=215  FN= 12
#   Precision = 1.000  Recall = 0.840  F1 = 0.913

# ============================================================

# Plot saved: logs\benchmarks\roc_pr_curves.png
# Data saved: logs\benchmarks\roc_pr_data.json
# (venv) PS D:\final yeat project> 