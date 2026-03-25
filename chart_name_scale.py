"""
Name Scale Chart — shows how single male names dwarf female names across ASX boards.
Visual: stacked female names (left) vs single male name (right), like a balance.
"""
import csv
import os
from collections import defaultdict, Counter

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

DATA_DIR = "data"
OUTPUT_PATH = os.path.join(DATA_DIR, "chart_name_scale.png")

# Gospel-name highlight color
GOSPEL_COLOR = "#e07020"
MALE_COLOR   = "#c0392b"
BG           = "white"


def load_name_boards():
    by_company = defaultdict(list)
    with open(os.path.join(DATA_DIR, "directors.csv"), newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["is_board"] == "True":
                by_company[row["ticker"]].append(row)

    boards = {t: m for t, m in by_company.items() if len(m) >= 3}
    total_boards = len(boards)

    male_name_boards = Counter()
    female_name_boards = Counter()
    for m in boards.values():
        seen_m, seen_f = set(), set()
        for d in m:
            n = d["first_name"]
            if d["gender"] == "M" and n not in seen_m:
                male_name_boards[n] += 1; seen_m.add(n)
            elif d["gender"] == "F" and n not in seen_f:
                female_name_boards[n] += 1; seen_f.add(n)

    return male_name_boards, female_name_boards, total_boards


def draw():
    male_counts, female_counts, total_boards = load_name_boards()

    # Top male names to feature (gospel highlighted)
    GOSPEL = {"Matthew", "Mark", "Luke", "John"}
    top_male = male_counts.most_common(12)
    top_female = female_counts.most_common(30)

    # Palette for female names (cool purples/blues)
    female_palette = [
        "#7b4fa0", "#9060b8", "#a570d0", "#b580e0",
        "#6050a0", "#7060b0", "#5080c0", "#6090c8",
        "#5070b0", "#4060a0", "#806098", "#9070a8",
    ]

    fig, axes = plt.subplots(1, 2, figsize=(14, 9),
                             gridspec_kw={"width_ratios": [1, 1], "wspace": 0.10})
    fig.patch.set_facecolor(BG)

    # ── Left panel: stacked female names next to each male name ───────────────
    ax = axes[0]
    ax.set_facecolor(BG)
    ax.set_xlim(-0.1, 1.05)
    ax.set_ylim(-0.5, len(top_male))
    ax.axis("off")

    ax.text(0.5, len(top_male) - 0.05,
            "One male name vs all female names combined",
            ha="center", va="bottom", color="#1a1a2a",
            fontsize=12, fontweight="bold")

    bar_h = 0.65
    for row_i, (mname, mcnt) in enumerate(reversed(top_male)):
        y = row_i
        color = GOSPEL_COLOR if mname in GOSPEL else MALE_COLOR

        # Male bar (full width normalised to mcnt)
        scale = 0.85 / max(c for _, c in top_male)
        mw = mcnt * scale

        ax.barh(y, mw, height=bar_h, left=0, color=color,
                align="center", zorder=3)
        ax.text(mw + 0.01, y, f"{mname}  {mcnt}",
                va="center", ha="left", color="#1a1a2a",
                fontsize=9, fontweight="bold")

        # Stacked female names that fit within mw
        cum = 0
        fi = 0
        for fname, fcnt in top_female:
            if cum >= mcnt:
                break
            take = min(fcnt, mcnt - cum)
            fw = take * scale
            fc = female_palette[fi % len(female_palette)]
            ax.barh(y, fw, height=bar_h * 0.4, left=cum * scale,
                    color=fc, align="center", zorder=4, alpha=0.95)
            cum += take
            fi += 1

    ax.text(0.0, -0.35,
            "Purple segments = female names stacked until they match the male name's board count",
            ha="left", va="center", color="#888899", fontsize=7.5, style="italic")

    # ── Right panel: the headline comparison (David vs top female names) ──────
    ax2 = axes[1]
    ax2.set_facecolor(BG)
    ax2.set_xlim(-0.2, 1.2)
    ax2.set_ylim(-1.0, 14.5)
    ax2.axis("off")

    # How many female names does David beat?
    david_cnt = male_counts["David"]
    john_cnt  = male_counts["John"]
    mark_cnt  = male_counts["Mark"]

    col_x   = 0.18   # left column: female names
    david_x = 0.72   # right column: David
    john_x  = 0.95

    bar_w = 0.22
    scale2 = 12.0 / david_cnt   # map david_cnt to full height

    # Draw David bar
    ax2.add_patch(mpatches.FancyBboxPatch(
        (david_x - bar_w / 2, 0), bar_w, david_cnt * scale2,
        boxstyle="round,pad=0.005", color=MALE_COLOR, zorder=3))
    ax2.text(david_x, david_cnt * scale2 + 0.3,
             f"David\n{david_cnt} boards",
             ha="center", va="bottom", color="#c0392b",
             fontsize=10, fontweight="bold")

    # Draw John bar (gospel)
    ax2.add_patch(mpatches.FancyBboxPatch(
        (john_x - bar_w / 2, 0), bar_w, john_cnt * scale2,
        boxstyle="round,pad=0.005", color=GOSPEL_COLOR, zorder=3))
    ax2.text(john_x, john_cnt * scale2 + 0.3,
             f"John\n{john_cnt} boards",
             ha="center", va="bottom", color=GOSPEL_COLOR,
             fontsize=10, fontweight="bold")

    # Stack female names in the left column
    cum_y = 0
    fi = 0
    for fname, fcnt in top_female:
        if cum_y >= david_cnt:
            break
        take = min(fcnt, david_cnt - cum_y)
        fh = take * scale2
        fc = female_palette[fi % len(female_palette)]
        ax2.add_patch(mpatches.FancyBboxPatch(
            (col_x - bar_w / 2, cum_y * scale2), bar_w, fh - 0.05,
            boxstyle="round,pad=0.005", color=fc, zorder=3))
        # Label if tall enough
        if fh > 0.4:
            ax2.text(col_x + bar_w / 2 + 0.02, cum_y * scale2 + fh / 2,
                     f"{fname} ({fcnt})", va="center", ha="left",
                     color="#bbbbcc", fontsize=7.5)
        cum_y += take
        fi += 1

    ax2.text(col_x, cum_y * scale2 + 0.3,
             f"Top {fi} female names\ncombined: {cum_y} boards",
             ha="center", va="bottom", color="#9090cc",
             fontsize=9, fontweight="bold")

    # Horizontal line at John's height
    ax2.plot([col_x - bar_w / 2 - 0.04, john_x + bar_w / 2 + 0.04],
             [john_cnt * scale2, john_cnt * scale2],
             color="#888899", lw=1.0, ls="--", zorder=2)
    female_at_john_level = sum(c for _, c in top_female
                               if sum(cc for _, cc in top_female[:top_female.index((_, c)) + 1]) <= john_cnt)

    # Title
    ax2.text(0.5, 14.0,
             f"David = top 12 female names",
             ha="center", va="center", color="#1a1a2a",
             fontsize=13, fontweight="bold")
    ax2.text(0.5, 13.4,
             f"John = top 7 female names",
             ha="center", va="center", color="#9090bb", fontsize=9.5)

    # ── Main title & footer ───────────────────────────────────────────────────
    fig.suptitle("More [Name]s than all [Female names] combined",
                 color="#1a1a2a", fontsize=16, fontweight="bold", y=0.98)
    fig.text(0.5, 0.01,
             "ASX-listed companies, March 2026  ·  Boards with 3+ members  ·  "
             "Each name counted once per board",
             ha="center", color="#888899", fontsize=8)

    plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close()
    print(f"Saved {OUTPUT_PATH}")


if __name__ == "__main__":
    draw()
