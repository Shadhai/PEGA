"""Generate HITL routing figure (Figure 4)."""
import matplotlib.pyplot as plt
from pathlib import Path

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))

# Pie chart
labels = ["Auto-approved\n(195)", "Auto-rejected\n(75)", "Flagged for\nreview (3)"]
sizes = [195, 75, 3]
colors = ["#2ecc71", "#e74c3c", "#f39c12"]
explode = (0, 0, 0.15)

wedges, texts, autotexts = ax1.pie(
    sizes, labels=labels, colors=colors, explode=explode,
    autopct=lambda p: f"{p:.1f}%" if p > 5 else f"{p:.2f}%",
    startangle=90, textprops={"fontsize": 10},
    wedgeprops={"edgecolor": "black", "linewidth": 0.8}
)
for at in autotexts:
    at.set_color("white")
    at.set_fontweight("bold")
ax1.set_title("Three-Way Routing Distribution", fontsize=11, fontweight="bold")

# Bar chart of flagged plan details
flagged_tasks = ["path_crossing_001", "path_crossing_002", "path_crossing_003"]
severities = [0.70, 0.70, 0.70]
trust_scores = [0.30, 0.30, 0.30]

bars = ax2.barh(flagged_tasks, trust_scores, color="#f39c12",
                edgecolor="black", height=0.5)
ax2.set_xlabel("Trust Score", fontsize=11)
ax2.set_title("Flagged Tasks (borderline trajectory violations)",
              fontsize=11, fontweight="bold")
ax2.set_xlim(0, 1.0)
ax2.axvline(x=0.75, color="green", linestyle="--", linewidth=1.5,
            label="Flag threshold (0.75)")
ax2.axvline(x=0.30, color="red", linestyle="--", linewidth=1.5,
            label="Plan trust score")
for b, v in zip(bars, trust_scores):
    ax2.text(v + 0.02, b.get_y() + b.get_height()/2, f"{v:.2f}",
             va="center", fontsize=10, fontweight="bold")
ax2.legend(fontsize=9, loc="lower right")
ax2.grid(axis="x", alpha=0.3)

plt.tight_layout()
Path("figures").mkdir(exist_ok=True)
plt.savefig("figures/hitl.pdf", bbox_inches="tight", dpi=300)
plt.savefig("figures/hitl.png", bbox_inches="tight", dpi=300)
print("✅ Saved figures/hitl.pdf and .png")