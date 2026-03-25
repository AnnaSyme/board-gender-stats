"""
Top first names on ASX boards, coloured by dominant gender.
"""
import csv
import os
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA_DIR   = "data"
OUTPUT     = os.path.join(DATA_DIR, "chart_top_names.png")
BG         = "#0f1117"
TOP_N      = 40

MALE_COLOR   = "#3a6fd8"
FEMALE_COLOR = "#7b4fa0"
GOSPEL       = {"Matthew", "Mark", "Luke", "John"}
GOSPEL_COLOR = "#e07020"


def load():
    counts     = Counter()
    gender_map = {}
    with open(os.path.join(DATA_DIR, "directors.csv"), newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["is_board"] == "True":
                name = row["first_name"]
                counts[name] += 1
                gender_map.setdefault(name, Counter())
                gender_map[name][row["gender"]] += 1
    return counts, gender_map


def draw():
    counts, gender_map = load()
    top = counts.most_common(TOP_N)
    names = [n for n, _ in top]
    vals  = [c for _, c in top]

    def color(name):
        dominant = gender_map[name].most_common(1)[0][0]
        if dominant == "F":
            return FEMALE_COLOR
        return MALE_COLOR

    colors = [color(n) for n in names]

    fig, ax = plt.subplots(figsize=(10, 9))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    y = range(len(names))
    bars = ax.barh(list(y), vals, color=colors, height=0.65, zorder=3)

    ax.set_yticks(list(y))
    ax.set_yticklabels(names, color="#ccccdd", fontsize=10)
    ax.invert_yaxis()

    ax.xaxis.grid(True, color="#1e1e2e", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_edgecolor("#333344")
    ax.tick_params(colors="#8888aa")
    ax.set_xlabel("Board seats", color="#8888aa", fontsize=9)

    max_val = max(vals)
    for i, (v, bar) in enumerate(zip(vals, bars)):
        ax.text(v + max_val * 0.01, i, str(v),
                va="center", color="#dddddd", fontsize=8.5, fontweight="bold")

    ax.set_xlim(0, max_val * 1.18)

    # legend
    from matplotlib.patches import Patch
    legend_els = [
        Patch(facecolor=MALE_COLOR,   label="Men's names"),
        Patch(facecolor=FEMALE_COLOR, label="Women's names"),
    ]
    ax.legend(handles=legend_els, loc="lower right",
              facecolor="#1a1a2e", edgecolor="#333344",
              labelcolor="#ccccdd", fontsize=9)

    fig.suptitle(f"Most common first names on ASX boards  —  top {TOP_N}",
                 color="white", fontsize=14, fontweight="bold", y=1.01)
    fig.text(0.5, -0.01,
             "ASX-listed companies, March 2026  ·  Boards with 3+ members  ·  "
             "Gender inferred from name prefix (Mr / Ms / Mrs / Miss)",
             ha="center", color="#40404e", fontsize=8)

    plt.tight_layout()
    plt.savefig(OUTPUT, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close()
    print(f"Saved {OUTPUT}")


if __name__ == "__main__":
    draw()
