"""
Boardroom Table Chart — ASX Gender Diversity
Two variants:
  chart_boardroom.png       — four categories (all men / mostly men / mostly women / all women)
  chart_boardroom_two.png   — two categories (mostly men / mostly women)

Rectangle table. Chairs are plain circles evenly spaced around the perimeter.
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
N_CHAIRS = 12

# ── Colour / label config ────────────────────────────────────────────────────

FOUR_COLORS = {
    "all_men":      "#c0392b",
    "mostly_men":   "#e07020",
    "mostly_women": "#7b4fa0",
    "all_women":    "#27ae60",
}
FOUR_LABELS = {
    "all_men":      "All men",
    "mostly_men":   "Mostly men",
    "mostly_women": "Mostly women",
    "all_women":    "All women",
}
FOUR_ORDER = ["all_men", "mostly_men", "mostly_women", "all_women"]

TWO_COLORS = {
    "mostly_men":   "#e07020",
    "mostly_women": "#7b4fa0",
}
TWO_LABELS = {
    "mostly_men":   "Mostly men",
    "mostly_women": "Mostly women",
}
TWO_ORDER = ["mostly_men", "mostly_women"]

# ── Data loading ─────────────────────────────────────────────────────────────

def load_counts():
    by_company = defaultdict(list)
    with open(os.path.join(DATA_DIR, "directors.csv"), newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["is_board"] == "True":
                by_company[row["ticker"]].append(row)

    four = {k: 0 for k in FOUR_ORDER}
    two  = {k: 0 for k in TWO_ORDER}

    for members in by_company.values():
        if len(members) < 3:
            continue
        total = len(members)
        women = sum(1 for m in members if m["gender"] == "F")
        pct = women / total
        if pct == 0:
            four["all_men"] += 1
            two["mostly_men"] += 1
        elif pct < 0.5:
            four["mostly_men"] += 1
            two["mostly_men"] += 1
        elif pct < 1.0:
            four["mostly_women"] += 1
            two["mostly_women"] += 1
        else:
            four["all_women"] += 1
            two["mostly_women"] += 1

    return four, two


def proportional_chairs(cats, order, n=N_CHAIRS):
    total = sum(cats.values())
    raw = {k: cats[k] / total * n for k in order}
    floored = {k: int(v) for k, v in raw.items()}
    deficit = n - sum(floored.values())
    by_frac = sorted(order, key=lambda k: raw[k] - floored[k], reverse=True)
    for k in by_frac[:deficit]:
        floored[k] += 1
    return floored




# ── Drawing ───────────────────────────────────────────────────────────────────

def draw_person(ax, cx, cy, _face_angle_deg, color, scale=0.155):
    ax.add_patch(Circle((cx, cy), scale, fill=False, edgecolor=color, linewidth=7.5, zorder=5))


def draw_legend_icon(ax, x, y, color, scale=0.07):
    ax.add_patch(Circle((x, y), scale, fill=False, edgecolor=color, linewidth=7.5, zorder=10))


def draw_boardroom(ax, chair_colors, cats, color_map, label_map, order, total_cos,
                   title_sub):
    BG = "white"
    ax.set_facecolor(BG)
    ax.set_aspect("equal")
    ax.set_xlim(-2.6, 2.6)
    ax.set_ylim(-1.55, 2.55)
    ax.axis("off")

    # ── Circle table ──────────────────────────────────────────────────────────
    TABLE_R = 0.58
    CHAIR_R = 0.90   # tight ring — small gap between circles

    ax.add_patch(Circle((0, 0), TABLE_R, facecolor="white",
                         edgecolor="#888899", linewidth=2.5, zorder=2))

    ax.text(0, 0.15, f"{total_cos:,}", ha="center", va="center",
            color="#444466", fontsize=16, fontweight="bold", zorder=10)
    ax.text(0, -0.18, "ASX\nboards", ha="center", va="center",
            color="#666688", fontsize=9.5, linespacing=1.5, zorder=10)

    # ── Chairs evenly around circle ───────────────────────────────────────────
    for i, color in enumerate(chair_colors):
        a = np.radians(90 - i * 360 / N_CHAIRS)
        draw_person(ax, CHAIR_R * np.cos(a), CHAIR_R * np.sin(a), 0, color)

    # ── Title ─────────────────────────────────────────────────────────────────
    ax.text(0, 2.45, "The ASX Boardroom",
            ha="center", va="center", color="#1a1a2a",
            fontsize=20, fontweight="bold")
    ax.text(0, 2.20, title_sub,
            ha="center", va="center", color="#9090bb", fontsize=9.5)

    # ── Annotations ───────────────────────────────────────────────────────────
    # For each category, point to the middle chair in that group
    for cat in order:
        if cats[cat] == 0:
            continue
        indices = [i for i, c in enumerate(chair_colors) if c == color_map[cat]]
        mid = indices[len(indices) // 2]
        angle_rad = np.radians(90 - mid * 360 / N_CHAIRS)
        cx = CHAIR_R * np.cos(angle_rad)
        cy = CHAIR_R * np.sin(angle_rad)
        # Place label radially outward
        label_r = CHAIR_R + 0.72
        lx = label_r * np.cos(angle_rad)
        ly = label_r * np.sin(angle_rad)
        pct = cats[cat] / total_cos * 100
        ax.annotate(
            f"{label_map[cat]}\n{pct:.0f}%",
            xy=(cx, cy), xytext=(lx, ly),
            ha="center", va="center",
            color="#1a1a2a", fontsize=9, fontweight="bold",
            linespacing=1.5,
            arrowprops=dict(arrowstyle="->", color="#888899", lw=1.2),
        )


def save_chart(output_path, cats, color_map, label_map, order, title_sub):
    total_cos = sum(cats.values())
    chair_counts = proportional_chairs(cats, order)

    print(f"\n{output_path}")
    for k in order:
        pct = cats[k] / total_cos * 100 if total_cos else 0
        print(f"  {k:15} {cats[k]:5}  ({pct:5.1f}%)  → {chair_counts[k]} chairs")

    chair_colors = []
    for cat in order:
        chair_colors.extend([color_map[cat]] * chair_counts[cat])

    BG = "white"
    fig, ax = plt.subplots(figsize=(9, 7.0))
    fig.patch.set_facecolor(BG)

    draw_boardroom(ax, chair_colors, cats, color_map, label_map, order,
                   total_cos, title_sub)

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
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close()
    print(f"  Saved {output_path}")


if __name__ == "__main__":
    four_cats, two_cats = load_counts()

    save_chart(
        os.path.join(DATA_DIR, "chart_boardroom.png"),
        four_cats, FOUR_COLORS, FOUR_LABELS, FOUR_ORDER,
        "If 12 seats represented every ASX board — who sits at the table?",
    )

    save_chart(
        os.path.join(DATA_DIR, "chart_boardroom_two.png"),
        two_cats, TWO_COLORS, TWO_LABELS, TWO_ORDER,
        "If 12 seats represented every ASX board — who sits at the table?",
    )
