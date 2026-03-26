"""
Two lollipop charts: male names on ASX boards that outnumber all women.
Chart 1 (names_comparison_gender.png):   legend = male names only
Chart 2 (names_comparison_gender2.png):  legend also shows female names
                                          + female names plotted on chart
Both share the same x-axis scale.
"""

import csv
import os
from collections import defaultdict, Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from name_combos import canonical

DATA_DIR  = "data"
BG        = "white"
MALE_COLOR = "#c0392b"
FEM_COLOR  = "#7b4fa0"
LINE_COLOR = "#bbbbcc"
AXIS_COLOR = "#bbbbcc"
N_MALE     = 15   # top male names to include
MIN_COUNT  = 40   # minimum boards threshold for male names


def compute_beats():
    by_company = defaultdict(list)
    with open(os.path.join(DATA_DIR, "directors.csv"), newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["is_board"] == "True":
                by_company[row["ticker"]].append(row)

    boards = {t: m for t, m in by_company.items() if len(m) >= 3}
    total  = len(boards)

    male_beats   = Counter()
    female_beats = Counter()

    for members in boards.values():
        male_names   = Counter(canonical(d["first_name"]) for d in members if d["gender"] == "M")
        female_names = Counter(canonical(d["first_name"]) for d in members if d["gender"] == "F")
        n_women = sum(d["gender"] == "F" for d in members)
        n_men   = sum(d["gender"] == "M" for d in members)

        for name, cnt in male_names.items():
            if cnt > n_women:
                male_beats[name] += 1
        for name, cnt in female_names.items():
            if cnt > n_men:
                female_beats[name] += 1

    return male_beats, female_beats, total


def draw_chart(rows, max_x, total, output_path, legend_entries, subtitle, title="Number of ASX boards with more Daves than women"):
    names  = [r[0] for r in rows]
    counts = [r[1] for r in rows]
    colors = [MALE_COLOR if r[2] == "M" else FEM_COLOR for r in rows]
    n      = len(rows)
    y      = range(n)

    # Compact height: ~0.42 inches per row, min 5
    fig_h = max(5, n * 0.42)
    fig, ax = plt.subplots(figsize=(10, fig_h))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    for yi, cnt, col in zip(y, counts, colors):
        ax.hlines(yi, 0, max(cnt, 0.5), colors=LINE_COLOR, linewidth=1.5, zorder=1)
        ax.scatter(max(cnt, 0.5), yi, color=col, s=90, zorder=3)
        ax.text(cnt + max_x * 0.013, yi, str(cnt),
                va="center", ha="left", color="#111111",
                fontsize=11, fontweight="bold")

    ax.set_yticks(list(y))
    ax.set_yticklabels(names, fontsize=12, color="#1a1a2a")
    ax.set_xlim(0, max_x)
    ax.set_xlabel(
        "Number of ASX boards where this name outnumbers the entire other gender",
        color=AXIS_COLOR, fontsize=10, labelpad=10,
    )
    ax.xaxis.grid(True, color="#e8e8ee", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(colors=AXIS_COLOR, which="both", labelsize=10)
    for spine in ax.spines.values():
        spine.set_edgecolor("#cccccc")

    ax.legend(handles=legend_entries, loc="lower right",
              facecolor="white", edgecolor="#cccccc",
              labelcolor="#1a1a2a", fontsize=10)

    ax.set_title(
        title,
        color="#1a1a2a", fontsize=15, fontweight="bold", pad=14,
    )
    fig.text(0.5, -0.04, subtitle,
             ha="center", color="#666677", fontsize=9, style="italic")
    fig.text(
        0.5, -0.08,
        f"{total:,} ASX boards with 3+ members  ·  "
        "Gender inferred from name prefix (Mr / Ms / Mrs / Miss)",
        ha="center", color="#888899", fontsize=8.5, style="italic",
    )

    plt.tight_layout()
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
    print(f"Saved {output_path}")


def main():
    male_beats, female_beats, total = compute_beats()

    # Male rows: above threshold, sorted ascending (highest at top)
    male_rows = sorted(
        [(n, c, "M") for n, c in male_beats.most_common(N_MALE) if c >= MIN_COUNT],
        key=lambda x: x[1]
    )
    # Female rows: all qualifying names, sorted ascending
    female_rows = sorted(
        [(n, c, "F") for n, c in female_beats.most_common()],
        key=lambda x: x[1]
    )

    max_x = max(r[1] for r in male_rows) * 1.18

    legend_male_only = [
        mpatches.Patch(color=MALE_COLOR, label="Male name outnumbers all women"),
    ]
    legend_both = [
        mpatches.Patch(color=MALE_COLOR, label="Male name outnumbers all women"),
        mpatches.Patch(color=FEM_COLOR,  label="Female name outnumbers all men"),
    ]

    # Chart 1: male names only, legend male only
    draw_chart(
        rows           = male_rows,
        max_x          = max_x,
        total          = total,
        output_path    = os.path.join(DATA_DIR, "names_comparison_gender.png"),
        legend_entries = legend_male_only,
        subtitle       = f"Names appearing on {MIN_COUNT}+ boards where that name outnumbers all women combined",
    )

    # Chart 2: same male names, legend includes female entry to show the contrast
    draw_chart(
        rows           = male_rows,
        max_x          = max_x,
        total          = total,
        output_path    = os.path.join(DATA_DIR, "names_comparison_gender2.png"),
        legend_entries = legend_both,
        subtitle       = f"Names appearing on {MIN_COUNT}+ boards where that name outnumbers the entire other gender  ·  No female name reaches this threshold",
        title          = "ASX boards with more Kates than men",
    )


if __name__ == "__main__":
    main()
