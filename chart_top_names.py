"""
Top first names on ASX boards, coloured by dominant gender.
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from name_combos import load_combined

DATA_DIR   = "data"
OUTPUT     = os.path.join(DATA_DIR, "chart_top_names.png")
BG         = "white"
TOP_N      = 40

MALE_COLOR   = "#3a6fd8"
FEMALE_COLOR = "#7b4fa0"
GOSPEL       = {"Matthew", "Mark", "Luke", "John"}
GOSPEL_COLOR = "#e07020"


def draw():
    counts, gender_map = load_combined(DATA_DIR)
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
    ax.set_yticklabels(names, color="#1a1a2a", fontsize=10)
    ax.invert_yaxis()

    ax.xaxis.grid(True, color="#e8e8ee", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_edgecolor("#cccccc")
    ax.tick_params(colors="#777788")
    ax.set_xlabel("Board seats", color="#777788", fontsize=9)

    max_val = max(vals)
    for i, (v, bar) in enumerate(zip(vals, bars)):
        ax.text(v + max_val * 0.01, i, str(v),
                va="center", color="#111111", fontsize=8.5, fontweight="bold")

    ax.set_xlim(0, max_val * 1.18)

    # legend
    from matplotlib.patches import Patch
    legend_els = [
        Patch(facecolor=MALE_COLOR,   label="Men's names"),
        Patch(facecolor=FEMALE_COLOR, label="Women's names"),
    ]
    ax.legend(handles=legend_els, loc="lower right",
              facecolor="white", edgecolor="#cccccc",
              labelcolor="#1a1a2a", fontsize=9)

    fig.suptitle(f"Most common first names on ASX boards  —  top {TOP_N}",
                 color="#1a1a2a", fontsize=13, fontweight="bold", y=1.01)
    fig.text(0.5, -0.01,
             "ASX-listed companies, March 2026  ·  Boards with 3+ members  ·  "
             "Gender inferred from name prefix (Mr / Ms / Mrs / Miss)",
             ha="center", color="#888899", fontsize=8)

    plt.tight_layout()
    # ── Rounded dotted border ──────────────────────────────────────
    from matplotlib.patches import FancyBboxPatch as _FBP
    fig.add_artist(_FBP(
        (0.01, 0.01), 0.98, 0.98,
        boxstyle="round,pad=0.0", linewidth=1.2, linestyle=":",
        edgecolor="#aaaaaa", facecolor="none",
        transform=fig.transFigure, clip_on=False, zorder=10,
    ))
    plt.savefig(OUTPUT, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close()
    print(f"Saved {OUTPUT}")


if __name__ == "__main__":
    draw()
