"""Generate trajectory violation figure (Figure 5)."""
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

fig = plt.figure(figsize=(11, 4.2))
gs = fig.add_gridspec(1, 2, wspace=0.3)

# Left: 3D view of the trajectory violation
ax1 = fig.add_subplot(gs[0, 0], projection="3d")

# Obstacle (truss segment S0 as a sphere)
u, v = np.mgrid[0:2*np.pi:30j, 0:np.pi:15j]
r = 6.7
xs = r * np.cos(u) * np.sin(v)
ys = r * np.sin(u) * np.sin(v)
zs = r * np.cos(v)
ax1.plot_surface(xs, ys, zs, color="red", alpha=0.25, edgecolor="none")

# Endpoints (clear)
p1 = np.array([0, 0, 15])
p2 = np.array([0, 0, -15])
ax1.scatter(*p1, color="green", s=100, label="Endpoint 1 (clear)")
ax1.scatter(*p2, color="green", s=100, label="Endpoint 2 (clear)")

# Trajectory (straight line through sphere)
t = np.linspace(0, 1, 50)
line = np.outer(1-t, p1) + np.outer(t, p2)
ax1.plot(line[:, 0], line[:, 1], line[:, 2], "b--", linewidth=2,
         label="Straight-line trajectory")
ax1.scatter(*line[25], color="orange", s=120, marker="x", linewidth=3,
            label="Waypoint inside truss")

ax1.set_xlabel("X (m)"); ax1.set_ylabel("Y (m)"); ax1.set_zlabel("Z (m)")
ax1.set_title("Trajectory Collision (Endpoints Clear)", fontsize=11,
              fontweight="bold")
ax1.legend(fontsize=8, loc="upper left")
ax1.set_xlim(-10, 10); ax1.set_ylim(-10, 10); ax1.set_zlim(-20, 20)

# Right: distance profile along the trajectory
ax2 = fig.add_subplot(gs[0, 1])

z_vals = np.linspace(15, -15, 50)
distances = np.abs(z_vals)  # distance from origin along Z axis
safe_distance = 7.0  # truss safe distance

ax2.plot(z_vals, distances, "b-", linewidth=2, label="Distance from truss")
ax2.axhline(y=safe_distance, color="red", linestyle="--",
            linewidth=2, label="Required clearance (7.0 m)")
ax2.fill_between(z_vals, 0, safe_distance, color="red", alpha=0.1)
ax2.fill_between(z_vals, safe_distance, 20, color="green", alpha=0.1)

# Highlight the violation region
violation_mask = distances < safe_distance
if violation_mask.any():
    z_violation = z_vals[violation_mask]
    d_violation = distances[violation_mask]
    ax2.fill_between(z_violation, 0, d_violation, color="red", alpha=0.3,
                     label="VIOLATION region")

# Mark endpoints
ax2.scatter([15, -15], [15, 15], color="green", s=120, zorder=5,
            label="Endpoints (safe)")
ax2.scatter([0], [0], color="orange", s=150, marker="x", linewidth=3,
            zorder=5, label="Midpoint (inside truss)")

ax2.set_xlabel("Trajectory position along Z (m)", fontsize=11)
ax2.set_ylabel("Distance from truss center (m)", fontsize=11)
ax2.set_title("Distance Profile Along Trajectory", fontsize=11,
              fontweight="bold")
ax2.legend(fontsize=9, loc="upper right")
ax2.grid(alpha=0.3)
ax2.set_ylim(0, 20)

plt.subplots_adjust(left=0.10, right=0.95, top=0.92, bottom=0.12)
Path("figures").mkdir(exist_ok=True)
plt.savefig("figures/trajectory.pdf", bbox_inches="tight", dpi=300)
plt.savefig("figures/trajectory.png", bbox_inches="tight", dpi=300)
print("✅ Saved figures/trajectory.pdf and .png")