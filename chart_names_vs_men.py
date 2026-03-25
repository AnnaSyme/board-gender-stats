"""
Lollipop chart: female first names that outnumber ALL men on an ASX board.
Reads from data/directors.csv (gender field: M / F / U).
Output: data/names_vs_men_lollipop.png
"""

import csv
import os
from collections import defaultdict, Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA_DIR    = "data"
OUTPUT_PATH = os.path.join(DATA_DIR, "names_vs_men_lollipop.png")
BG          = "white"
DOT_COLOR   = "#7b4fa0"   # purple — women's colour used throughout the project
LINE_COLOR  = "#bbbbcc"
TEXT_COLOR  = "#111111"
AXIS_COLOR  = "#bbbbcc"


def compute_female_beats():
    by_company = defaultdict(list)
    with open(os.path.join(DATA_DIR, "directors.csv"), newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["is_board"] == "True":
                by_company[row["ticker"]].append(row)

    boards = {t: m for t, m in by_company.items() if len(m) >= 3}
    total_boards = len(boards)

    female_beats = Counter()

    for members in boards.values():
        female_names = Counter(
            d["first_name"] for d in members if d["gender"] == "F"
        )
        n_men = sum(d["gender"] == "M" for d in members)

        seen = set()
        for name, cnt in female_names.items():
            if cnt > n_men and name not in seen:
                female_beats[name] += 1
                seen.add(name)

    return female_beats, total_boards


def save_chart(female_beats, total_boards):
    top = female_beats.most_common(20)
    if not top:
        print("No female names outnumber men on any board.")
        return

    names  = [t[0] for t in top][::-1]
    counts = [t[1] for t in top][::-1]
    y      = range(len(names))
    max_c  = max(counts)

    fig, ax = plt.subplots(figsize=(10, 8))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    for yi, count in zip(y, counts):
        ax.hlines(yi, 0, count, colors=LINE_COLOR, linewidth=1.5, zorder=1)
        ax.scatter(count, yi, color=DOT_COLOR, s=120, zorder=3)
        ax.text(count + 0.3, yi, str(count),
                va="center", ha="left", color=TEXT_COLOR,
                fontsize=10, fontweight="bold")

    ax.set_yticks(list(y))
    ax.set_yticklabels(names, fontsize=11, color="#1a1a2a")
    ax.set_xlabel(
        "Number of ASX boards where this name outnumbers all men combined",
        color=AXIS_COLOR, fontsize=10, labelpad=12,
    )
    ax.set_xlim(0, max_c + 5)
    ax.set_title(
        '"More [Name]s Than Men"\nASX-listed company boards, March 2026',
        color="#1a1a2a", fontsize=14, fontweight="bold", pad=16,
    )
    fig.text(
        0.5, 0.01,
        f"Boards where a single female first name appears more times than the "
        f"total number of men on that board.  "
        f"({total_boards:,} boards with 3+ members)",
        ha="center", color="#888899", fontsize=9,
    )

    ax.xaxis.grid(True, color="#e8e8ee", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(colors=AXIS_COLOR, which="both")
    for spine in ax.spines.values():
        spine.set_edgecolor("#cccccc")

    plt.tight_layout(rect=[0, 0.04, 1, 1])
    plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close()
    print(f"Saved {OUTPUT_PATH}")

    print(f"\nTop {len(top)} female names that outnumber all men on a board:")
    for name, count in top:
        pct = count / total_boards * 100
        print(f"  {name:<15} {count:>4}  ({pct:.2f}% of boards)")


if __name__ == "__main__":
    female_beats, total_boards = compute_female_beats()
    save_chart(female_beats, total_boards)
