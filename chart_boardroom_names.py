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

from name_combos import canonical

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
    "other_men":"#ddddee",
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

    name_map = {n: n.lower() for n in TARGET_NAMES}

    cats = {k: 0 for k in ORDER}
    for d in all_d:
        if d["gender"] == "F":
            cats["women"] += 1
        elif d["gender"] == "M" and canonical(d["first_name"]) in name_map:
            cats[name_map[canonical(d["first_name"])]] += 1
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

    BG = "white"
    fig, ax = plt.subplots(figsize=(10, 10))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_aspect("equal")
    ax.set_xlim(-3.0, 3.0)
    ax.set_ylim(-2.4, 2.8)
    ax.axis("off")

    # ── Table ─────────────────────────────────────────────────────────────────
    ax.add_patch(Circle((0, 0), TABLE_R, facecolor="white",
                         edgecolor="#888899", linewidth=2.5, zorder=2))
    ax.text(0, 0.15, f"{total:,}", ha="center", va="center",
            color="#444466", fontsize=15, fontweight="bold", zorder=10)
    ax.text(0, -0.18, "board\nseats", ha="center", va="center",
            color="#666688", fontsize=9, linespacing=1.5, zorder=10)

    # ── Chairs ────────────────────────────────────────────────────────────────
    for i, color in enumerate(chair_colors):
        a = np.radians(90 - i * 360 / N_CHAIRS)
        ax.add_patch(Circle((CHAIR_R * np.cos(a), CHAIR_R * np.sin(a)),
                             SCALE, fill=False, edgecolor=color, linewidth=7.5, zorder=5))

    # ── Group bracket arcs ────────────────────────────────────────────────────
    from matplotlib.patches import Arc

    STEP_DEG = 360 / N_CHAIRS
    ARC_R = CHAIR_R + SCALE + 0.16   # just outside the chair circles

    def draw_group_arc(i_start, n_chairs, color, linestyle):
        if n_chairs == 0:
            return
        i_end = i_start + n_chairs - 1
        a_hi = 90 - i_start * STEP_DEG + STEP_DEG * 0.45
        a_lo = 90 - i_end   * STEP_DEG - STEP_DEG * 0.45
        ax.add_patch(Arc((0, 0), 2 * ARC_R, 2 * ARC_R,
                         theta1=a_lo, theta2=a_hi,
                         color=color, linewidth=3.5, linestyle=linestyle, zorder=6))

    named_cats = ["david", "michael", "peter", "andrew", "john", "mark"]
    n_women = chair_counts["women"]
    n_named = sum(chair_counts[c] for c in named_cats)

    # Women's bracket — solid purple
    draw_group_arc(0, n_women, COLORS["women"], "-")

    # Named men's bracket — dashed dark navy
    draw_group_arc(n_women, n_named, "#2c3e6b", (0, (7, 3)))

    # ── Annotations ───────────────────────────────────────────────────────────
    named_set = set(named_cats)

    for cat in ORDER:
        if chair_counts[cat] == 0:
            continue
        if cat in named_set:
            continue   # handled below as a combined group
        indices = [i for i, c in enumerate(chair_colors) if c == COLORS[cat]]
        mid = indices[len(indices) // 2]
        angle_rad = np.radians(90 - mid * 360 / N_CHAIRS)
        cx = CHAIR_R * np.cos(angle_rad)
        cy = CHAIR_R * np.sin(angle_rad)

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
            color="#1a1a2a", fontsize=8.5, fontweight="bold",
            linespacing=1.5,
            arrowprops=dict(arrowstyle="->", color="#888899", lw=1.0),
        )

    # ── Combined named-men annotation ─────────────────────────────────────────
    named_with_chairs = [c for c in named_cats if chair_counts[c] > 0]
    if named_with_chairs:
        named_colors = {COLORS[c] for c in named_with_chairs}
        named_indices = [i for i, col in enumerate(chair_colors) if col in named_colors]
        mid_i = named_indices[len(named_indices) // 2]
        angle_rad = np.radians(90 - mid_i * 360 / N_CHAIRS)
        cx = CHAIR_R * np.cos(angle_rad)
        cy = CHAIR_R * np.sin(angle_rad)
        label_r = CHAIR_R + 0.72
        lx = label_r * np.cos(angle_rad)
        ly = label_r * np.sin(angle_rad)
        n_total = sum(cats[c] for c in named_cats)
        pct_total = n_total / total * 100
        parts = [LABELS[c] for c in named_with_chairs]
        mid_wrap = len(parts) // 2
        names_str = ", ".join(parts[:mid_wrap]) + ",\n" + ", ".join(parts[mid_wrap:])
        ax.annotate(
            f"{names_str}\n{n_total:,}  ({pct_total:.0f}%)",
            xy=(cx, cy), xytext=(lx, ly),
            ha="center", va="center",
            color="#1a1a2a", fontsize=8.5, fontweight="bold",
            linespacing=1.5,
            arrowprops=dict(arrowstyle="->", color="#888899", lw=1.0),
        )

    # ── Title ─────────────────────────────────────────────────────────────────
    ax.text(0, 2.62, "A seat at the table",
            ha="center", va="center", color="#1a1a2a",
            fontsize=20, fontweight="bold")
    ax.text(0, 2.38,
            "Every ASX board seat, represented as 28 chairs",
            ha="center", va="center", color="#9090bb", fontsize=9.5)

    # ── Footer ────────────────────────────────────────────────────────────────
    fig.text(0.5, 0.01,
             "ASX-listed companies, March 2026  ·  Boards with 3+ members  ·  "
             "Gender inferred from name prefix (Mr / Ms / Mrs / Miss)",
             ha="center", color="#888899", fontsize=8)

    plt.tight_layout(rect=[0, 0.03, 1, 1])
    # ── Rounded dotted border ──────────────────────────────────────
    from matplotlib.patches import FancyBboxPatch as _FBP
    fig.add_artist(_FBP(
        (0.01, 0.01), 0.98, 0.98,
        boxstyle="round,pad=0.0", linewidth=1.2, linestyle=":",
        edgecolor="#aaaaaa", facecolor="none",
        transform=fig.transFigure, clip_on=False, zorder=10,
    ))
    plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close()
    print(f"\nSaved {OUTPUT_PATH}")


if __name__ == "__main__":
    draw_chart()
