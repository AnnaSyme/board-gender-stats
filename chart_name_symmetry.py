"""
Symmetric name test: "more [name] than the opposite gender"
Left side: male names where name-count > all women on that board
Right side: female names where name-count > all men on that board
"""
import csv
import os
from collections import defaultdict, Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA_DIR = "data"
OUTPUT_PATH = os.path.join(DATA_DIR, "chart_name_symmetry.png")
BG = "white"


def load(boards):
    male_beats, female_beats = Counter(), Counter()
    male_board_count, female_board_count = Counter(), Counter()

    for m in boards.values():
        male_names   = Counter(d["first_name"] for d in m if d["gender"] == "M")
        female_names = Counter(d["first_name"] for d in m if d["gender"] == "F")
        n_women = sum(d["gender"] == "F" for d in m)
        n_men   = sum(d["gender"] == "M" for d in m)

        for name, cnt in male_names.items():
            male_board_count[name] += 1
            if cnt > n_women:
                male_beats[name] += 1

        for name, cnt in female_names.items():
            female_board_count[name] += 1
            if cnt > n_men:
                female_beats[name] += 1

    return male_beats, female_beats, male_board_count, female_board_count


def draw():
    by_company = defaultdict(list)
    with open(os.path.join(DATA_DIR, "directors.csv"), newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["is_board"] == "True":
                by_company[row["ticker"]].append(row)
    boards = {t: m for t, m in by_company.items() if len(m) >= 3}
    total = len(boards)

    male_beats, female_beats, male_bc, female_bc = load(boards)

    GOSPEL = {"Matthew", "Mark", "Luke", "John"}
    top_male   = male_bc.most_common(15)
    top_female = female_bc.most_common(15)

    male_names   = [n for n, _ in top_male]
    female_names = [n for n, _ in top_female]

    male_counts   = [male_beats.get(n, 0)   for n in male_names]
    female_counts = [female_beats.get(n, 0) for n in female_names]

    fig, (ax_m, ax_f) = plt.subplots(1, 2, figsize=(13, 7),
                                      gridspec_kw={"wspace": 0.06})
    fig.patch.set_facecolor(BG)

    def style_ax(ax):
        ax.set_facecolor(BG)
        ax.tick_params(colors="#bbbbcc")
        for spine in ax.spines.values():
            spine.set_edgecolor("#cccccc")
        ax.xaxis.grid(True, color="#e8e8ee", linewidth=0.8, zorder=0)
        ax.set_axisbelow(True)

    MALE_COLOR   = "#c0392b"
    GOSPEL_COLOR = "#e07020"
    FEMALE_COLOR = "#7b4fa0"
    ZERO_COLOR   = "#ddddee"

    # ── Left: male names ──────────────────────────────────────────────────────
    style_ax(ax_m)
    y = range(len(male_names))
    colors_m = [GOSPEL_COLOR if n in GOSPEL else MALE_COLOR for n in male_names]

    bars = ax_m.barh(list(y), male_counts[::-1] if False else male_counts,
                     color=colors_m, height=0.6, zorder=3)

    ax_m.set_yticks(list(y))
    ax_m.set_yticklabels(male_names, color="#1a1a2a", fontsize=10)
    ax_m.set_xlabel("Boards where this name outnumbers all women", color="#777788", fontsize=8.5)
    ax_m.set_title("Male names", color="#e08080", fontsize=12, fontweight="bold", pad=10)

    max_val = max(male_counts + [1])
    ax_m.set_xlim(0, max_val * 1.25)
    for i, (cnt, bar) in enumerate(zip(male_counts, bars)):
        if cnt > 0:
            ax_m.text(cnt + max_val * 0.02, i, str(cnt),
                      va="center", color="#111111", fontsize=9, fontweight="bold")
        else:
            ax_m.text(max_val * 0.02, i, "0",
                      va="center", color="#bbbbcc", fontsize=9)

    # ── Right: female names ───────────────────────────────────────────────────
    style_ax(ax_f)
    y2 = range(len(female_names))
    colors_f = [FEMALE_COLOR if female_counts[i] > 0 else ZERO_COLOR
                for i in range(len(female_names))]

    bars2 = ax_f.barh(list(y2), female_counts, color=colors_f, height=0.6, zorder=3)

    ax_f.set_yticks(list(y2))
    ax_f.set_yticklabels(female_names, color="#1a1a2a", fontsize=10)
    ax_f.set_xlabel("Boards where this name outnumbers all men", color="#777788", fontsize=8.5)
    ax_f.set_title("Female names", color="#a070c0", fontsize=12, fontweight="bold", pad=10)

    ax_f.set_xlim(0, max_val * 1.25)   # same scale as left panel
    for i, cnt in enumerate(female_counts):
        if cnt > 0:
            ax_f.text(cnt + max_val * 0.02, i, str(cnt),
                      va="center", color="#111111", fontsize=9, fontweight="bold")
        else:
            ax_f.text(max_val * 0.02, i, "0",
                      va="center", color="#bbbbcc", fontsize=9)

    # ── Shared x-axis note ────────────────────────────────────────────────────
    fig.text(0.5, 0.93,
             "Same scale on both axes  —  boards where a single first name outnumbers the entire opposite gender",
             ha="center", color="#888899", fontsize=8, style="italic")

    # ── Title & footer ────────────────────────────────────────────────────────
    fig.suptitle("More [name] than the opposite gender — ASX boards",
                 color="#1a1a2a", fontsize=15, fontweight="bold", y=1.00)
    fig.text(0.5, 0.01,
             "ASX-listed companies, March 2026  ·  Boards with 3+ members  ·  "
             "Gender inferred from name prefix (Mr / Ms / Mrs / Miss)",
             ha="center", color="#888899", fontsize=8)

    plt.tight_layout(rect=[0, 0.03, 1, 0.97])
    plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close()
    print(f"Saved {OUTPUT_PATH}")


if __name__ == "__main__":
    draw()
