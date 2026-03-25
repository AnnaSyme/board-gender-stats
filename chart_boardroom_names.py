"""
Boardroom Names Chart — ASX board seats by name group
28 chairs around a circle table, each chair = ~1/28 of all board seats.
Named chairs: the Davids, Michaels, Peters, Andrews, Johns, Marks (one each).
Women get 5 chairs. Other men fill the rest.
"""
import csv
import os
from collections import defaultdict

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

DATA_DIR = "data"
OUTPUT_PATH = os.path.join(DATA_DIR, "chart_boardroom_names.png")

N_CHAIRS = 28
TABLE_R  = 0.88
CHAIR_R  = 1.32
SCALE    = 0.105   # circle radius — snug fit for 28

TARGET_NAMES = ["David", "Michael", "Peter", "Andrew", "John", "Mark"]

ORDER = ["women"] + [n.lower() for n in TARGET_NAMES] + ["other_men"]

COLORS = {
    "women":    "#7b4fa0",
    "david":    "#c0392b",
    "michael":  "#e07020",
    "peter":    "#c8970a",
    "andrew":   "#1a7fa0",
    "john":     "#2e6dc4",
    "mark":     "#28a068",
    "other_men":"#252538",
}

LABELS = {
    "women":    "Women",
    "david":    "Davids",
    "michael":  "Michaels",
    "peter":    "Peters",
    "andrew":   "Andrews",
    "john":     "Johns",
    "mark":     "Marks",
    "other_men":"Other men",
}


def load_counts():
    by_company = defaultdict(list)
    with open(os.path.join(DATA_DIR, "directors.csv"), newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["is_board"] == "True":
                by_company[row["ticker"]].append(row)

    all_d = [m for members in by_company.values()
             if len(members) >= 3 for m in members]

    name_set = set(n.lower() for n in TARGET_NAMES)
    name_map = {n: n.lower() for n in TARGET_NAMES}

    cats = {k: 0 for k in ORDER}
    for d in all_d:
        if d["gender"] == "F":
            cats["women"] += 1
        elif d["gender"] == "M" and d["first_name"] in name_map:
            cats[name_map[d["first_name"]]] += 1
        else:
            cats["other_men"] += 1

    return cats, len(all_d)


def proportional_chairs(cats, total, n=N_CHAIRS):
    raw = {k: cats[k] / total * n for k in ORDER}
    floored = {k: int(v) for k, v in raw.items()}
    deficit = n - sum(floored.values())
    by_frac = sorted(ORDER, key=lambda k: raw[k] - floored[k], reverse=True)
    for k in by_frac[:deficit]:
        floored[k] += 1
    return floored


def draw_chart():
    cats, total = load_counts()
    chair_counts = proportional_chairs(cats, total)

    print("Chair allocation:")
    for k in ORDER:
        print(f"  {k:12} {cats[k]:5} directors  → {chair_counts[k]} chair(s)")

    # Build colour list
    chair_colors = []
    for cat in ORDER:
        chair_colors.extend([COLORS[cat]] * chair_counts[cat])

    BG = "#0f1117"
    fig, ax = plt.subplots(figsize=(10, 10))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_aspect("equal")
    ax.set_xlim(-3.0, 3.0)
    ax.set_ylim(-2.4, 2.8)
    ax.axis("off")

    # ── Table ─────────────────────────────────────────────────────────────────
    ax.add_patch(Circle((0, 0), TABLE_R, color="#15151f", zorder=2))
    ax.add_patch(Circle((0, 0), TABLE_R, fill=False,
                         edgecolor="#2a2a44", linewidth=2.5, zorder=3))
    ax.text(0, 0.15, f"{total:,}", ha="center", va="center",
            color="#6868a0", fontsize=15, fontweight="bold", zorder=10)
    ax.text(0, -0.18, "board\nseats", ha="center", va="center",
            color="#484870", fontsize=9, linespacing=1.5, zorder=10)

    # ── Chairs ────────────────────────────────────────────────────────────────
    for i, color in enumerate(chair_colors):
        a = np.radians(90 - i * 360 / N_CHAIRS)
        ax.add_patch(Circle((CHAIR_R * np.cos(a), CHAIR_R * np.sin(a)),
                             SCALE, color=color, zorder=5))

    # ── Annotations ───────────────────────────────────────────────────────────
    for cat in ORDER:
        if chair_counts[cat] == 0:
            continue
        indices = [i for i, c in enumerate(chair_colors) if c == COLORS[cat]]
        mid = indices[len(indices) // 2]
        angle_rad = np.radians(90 - mid * 360 / N_CHAIRS)
        cx = CHAIR_R * np.cos(angle_rad)
        cy = CHAIR_R * np.sin(angle_rad)

        # Extend label further for named chairs (they cluster on one side)
        n_chairs = chair_counts[cat]
        label_r = CHAIR_R + (0.58 if n_chairs == 1 else 0.72)
        lx = label_r * np.cos(angle_rad)
        ly = label_r * np.sin(angle_rad)

        n_dir = cats[cat]
        pct = n_dir / total * 100
        label = f"{LABELS[cat]}\n{n_dir:,}  ({pct:.0f}%)"

        ax.annotate(
            label,
            xy=(cx, cy), xytext=(lx, ly),
            ha="center", va="center",
            color="#ccccdd", fontsize=8.5, fontweight="bold",
            linespacing=1.5,
            arrowprops=dict(arrowstyle="->", color="#555566", lw=1.0),
        )

    # ── Title ─────────────────────────────────────────────────────────────────
    ax.text(0, 2.62, "A seat at the table",
            ha="center", va="center", color="white",
            fontsize=20, fontweight="bold")
    ax.text(0, 2.38,
            "Every ASX board seat, represented as 28 chairs",
            ha="center", va="center", color="#9090bb", fontsize=9.5)

    # ── Footer ────────────────────────────────────────────────────────────────
    fig.text(0.5, 0.01,
             "ASX-listed companies, March 2026  ·  Boards with 3+ members  ·  "
             "Gender inferred from name prefix (Mr / Ms / Mrs / Miss)",
             ha="center", color="#40404e", fontsize=8)

    plt.tight_layout(rect=[0, 0.03, 1, 1])
    plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close()
    print(f"\nSaved {OUTPUT_PATH}")


if __name__ == "__main__":
    draw_chart()
