"""
Gospel names vs top women's names — on same scale as top-40 chart.
"""
import csv
import os
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

DATA_DIR = "data"
OUTPUT   = os.path.join(DATA_DIR, "chart_gospel_women.png")
BG       = "white"

MALE_COLOR   = "#3a6fd8"
FEMALE_COLOR = "#7b4fa0"
GOSPEL       = ["John", "Mark", "Matthew", "Luke"]   # descending count order
TOP_WOMEN    = 10

SAME_SCALE_MAX = 313   # David — top of the main chart


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

    women_names = [n for n in counts
                   if gender_map[n].most_common(1)[0][0] == "F"]
    top_women   = sorted(women_names, key=lambda n: -counts[n])[:TOP_WOMEN]

    # Gospel section (sorted descending) then women section
    names  = GOSPEL + top_women
    vals   = [counts[n] for n in names]
    colors = [MALE_COLOR] * len(GOSPEL) + [FEMALE_COLOR] * len(top_women)

    fig, ax = plt.subplots(figsize=(10, 7))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    y    = range(len(names))
    bars = ax.barh(list(y), vals, color=colors, height=0.65, zorder=3)

    # divider between gospel and women sections
    ax.axhline(len(GOSPEL) - 0.5, color="#cccccc", linewidth=1, linestyle="--", zorder=2)

    ax.set_yticks(list(y))
    ax.set_yticklabels(names, color="#1a1a2a", fontsize=10)
    ax.invert_yaxis()

    ax.xaxis.grid(True, color="#e8e8ee", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_edgecolor("#cccccc")
    ax.tick_params(colors="#777788")
    ax.set_xlabel("Board seats", color="#777788", fontsize=9)

    # same scale as top-40 chart
    ax.set_xlim(0, SAME_SCALE_MAX * 1.18)

    for i, (v, bar) in enumerate(zip(vals, bars)):
        ax.text(v + SAME_SCALE_MAX * 0.01, i, str(v),
                va="center", color="#111111", fontsize=8.5, fontweight="bold")

    # combined gospel annotation
    gospel_total = sum(counts[n] for n in GOSPEL)
    ax.text(SAME_SCALE_MAX * 1.15, len(GOSPEL) / 2 - 0.5,
            f"Combined:\n{gospel_total}",
            ha="right", va="center", color="#8888bb", fontsize=8.5, style="italic")

    legend_els = [
        Patch(facecolor=MALE_COLOR,   label="Gospel names (Matthew, Mark, Luke, John)"),
        Patch(facecolor=FEMALE_COLOR, label="Women's names"),
    ]
    ax.legend(handles=legend_els, loc="lower right",
              facecolor="#1a1a2e", edgecolor="#cccccc",
              labelcolor="#1a1a2a", fontsize=9)

    fig.suptitle("Gospel names vs top women's names on ASX boards",
                 color="#1a1a2a", fontsize=14, fontweight="bold", y=1.01)
    fig.text(0.5, -0.01,
             "X-axis on same scale as top-40 chart  ·  ASX-listed companies, March 2026  ·  "
             "Boards with 3+ members",
             ha="center", color="#888899", fontsize=8)

    plt.tight_layout()
    plt.savefig(OUTPUT, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close()
    print(f"Saved {OUTPUT}")


if __name__ == "__main__":
    draw()
