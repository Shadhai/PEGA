"""Generate ablation bar chart (Figure 2)."""
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

configs = ["full", "no_traj", "no_force", "no_kin", "graph_only", "no_graph", "kin_only"]
tp =      [78,     75,        78,         65,       65,           43,         17]
f1 =      [1.000,  0.980,     1.000,      0.909,    0.909,        0.711,      0.358]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))

# True positives
colors = ["#2ecc71" if t == 78 else "#e74c3c" if t < 50 else "#f39c12" for t in tp]
bars = ax1.bar(configs, tp, color=colors, edgecolor="black", linewidth=0.6)
ax1.set_ylabel("True Positives (TP)", fontsize=11)
ax1.set_title("Component Contribution to Unsafe Detection", fontsize=11, fontweight="bold")
ax1.set_ylim(0, 90)
ax1.axhline(y=78, color="black", linestyle="--", linewidth=1, alpha=0.5, label="Full = 78")
ax1.legend(loc="upper right", fontsize=9)
ax1.tick_params(axis="x", rotation=45, labelsize=9)
for b, v in zip(bars, tp):
    ax1.text(b.get_x() + b.get_width()/2, v + 1, str(v), ha="center", fontsize=9)
ax1.grid(axis="y", alpha=0.3)

# F1 score
colors2 = ["#2ecc71" if f == 1.0 else "#f39c12" if f >= 0.9 else "#e74c3c" for f in f1]
bars2 = ax2.bar(configs, f1, color=colors2, edgecolor="black", linewidth=0.6)
ax2.set_ylabel("F1 Score", fontsize=11)
ax2.set_title("Classification Quality", fontsize=11, fontweight="bold")
ax2.set_ylim(0, 1.1)
ax2.axhline(y=1.0, color="black", linestyle="--", linewidth=1, alpha=0.5)
ax2.tick_params(axis="x", rotation=45, labelsize=9)
for b, v in zip(bars2, f1):
    ax2.text(b.get_x() + b.get_width()/2, v + 0.02, f"{v:.3f}", ha="center", fontsize=9)
ax2.grid(axis="y", alpha=0.3)

plt.tight_layout()
Path("figures").mkdir(exist_ok=True)
plt.savefig("figures/ablation.pdf", bbox_inches="tight", dpi=300)
plt.savefig("figures/ablation.png", bbox_inches="tight", dpi=300)
print("✅ Saved figures/ablation.pdf and .png")