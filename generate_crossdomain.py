"""Generate cross-domain comparison (Figure 3)."""
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

domains = ["Aerospace\n(273 tasks)", "Industrial\n(15 tasks)"]
tp = [78, 7]
tn = [195, 8]
fp = [0, 0]
fn = [0, 0]
f1 = [1.000, 1.000]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2),
                                gridspec_kw={"width_ratios": [1.4, 1]})

# Stacked bars for confusion matrix
x = np.arange(len(domains))
w = 0.5

p1 = ax1.bar(x, tp, w, label="TP (unsafe rejected)", color="#2ecc71", edgecolor="black")
p2 = ax1.bar(x, tn, w, bottom=tp, label="TN (safe approved)", color="#3498db", edgecolor="black")
p3 = ax1.bar(x, fn, w, bottom=[tp[i]+tn[i] for i in range(len(domains))],
             label="FN (unsafe approved)", color="#e74c3c", edgecolor="black")
p4 = ax1.bar(x, fp, w, bottom=[tp[i]+tn[i]+fn[i] for i in range(len(domains))],
             label="FP (safe rejected)", color="#f39c12", edgecolor="black")

ax1.set_ylabel("Number of Tasks", fontsize=11)
ax1.set_title("Confusion Matrix by Domain", fontsize=11, fontweight="bold")
ax1.set_xticks(x)
ax1.set_xticklabels(domains, fontsize=10)
ax1.legend(fontsize=8, loc="upper right")
ax1.grid(axis="y", alpha=0.3)

# Annotate
for i, (t, n) in enumerate(zip(tp, tn)):
    ax1.text(i, t/2, f"{t}", ha="center", color="white", fontweight="bold", fontsize=11)
    ax1.text(i, t + n/2, f"{n}", ha="center", color="white", fontweight="bold", fontsize=11)

# F1 bars
bars = ax2.bar(domains, f1, color=["#2ecc71", "#2ecc71"], edgecolor="black", width=0.5)
ax2.set_ylabel("F1 Score", fontsize=11)
ax2.set_title("Domain-Independent Safety Performance", fontsize=11, fontweight="bold")
ax2.set_ylim(0, 1.15)
for b, v in zip(bars, f1):
    ax2.text(b.get_x() + b.get_width()/2, v + 0.03, f"{v:.3f}",
             ha="center", fontsize=12, fontweight="bold")
ax2.grid(axis="y", alpha=0.3)

plt.tight_layout()
Path("figures").mkdir(exist_ok=True)
plt.savefig("figures/crossdomain.pdf", bbox_inches="tight", dpi=300)
plt.savefig("figures/crossdomain.png", bbox_inches="tight", dpi=300)
print("✅ Saved figures/crossdomain.pdf and .png")