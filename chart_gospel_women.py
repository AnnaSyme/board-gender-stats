"""
Gospel names chart — two outputs:
  chart_gospel_men.png    : gospel names + representative other men in same range
  chart_gospel_women.png  : same men + top women's names in purple

Gospel names (John, Mark, Matthew, Luke) are identified with bold y-axis labels.
Legend: Men's names / Women's names only.
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, FancyBboxPatch as _FBP

from name_combos import MALE_COMBOS, FEMALE_COMBOS, canonical, load_combined

DATA_DIR     = "data"
BG           = "white"
MALE_COLOR   = "#3a6fd8"
FEMALE_COLOR = "#7b4fa0"
GOSPEL = {"John", "Mark", "Matthew", "Luke"}


def load():
    return load_combined(DATA_DIR)


def build_rows(counts, gender_map):
    fiona_c = counts["Fiona"]

    # All male names with combined count >= Fiona's count, sorted descending
    all_men = sorted(
        [n for n in counts
         if gender_map[n].most_common(1)[0][0] == "M"
         and counts[n] >= fiona_c],
        key=lambda n: -counts[n],
    )

    # All women with combined count >= Fiona's count
    women = sorted(
        [n for n in counts
         if gender_map[n].most_common(1)[0][0] == "F"
         and counts[n] >= fiona_c],
        key=lambda n: -counts[n],
    )

    return all_men, women


def draw(ax, names, counts, gospel_set, male_color, female_color,
         female_names_set, max_x, label):
    y      = range(len(names))
    vals   = [counts[n] for n in names]
    colors = [female_color if n in female_names_set else male_color for n in names]

    bars = ax.barh(list(y), vals, color=colors, height=0.65, zorder=3)
    ax.invert_yaxis()

    # Y-axis labels — bold for gospel names
    ax.set_yticks(list(y))
    labels = ax.set_yticklabels(names, fontsize=10, color="#1a1a2a")
    for tick, name in zip(ax.get_yticklabels(), names):
        if name in gospel_set:
            tick.set_fontweight("bold")

    # No section divider — names are sorted by count, men and women interleaved

    ax.xaxis.grid(True, color="#e8e8ee", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_edgecolor("#cccccc")
    ax.tick_params(colors="#777788")
    ax.set_xlabel("Board seats", color="#777788", fontsize=9)
    ax.set_xlim(0, max_x)

    # Value labels
    for i, v in enumerate(vals):
        ax.text(v + max_x * 0.01, i, str(v),
                va="center", color="#111111", fontsize=8.5, fontweight="bold")

    # Legend
    entries = [Patch(facecolor=male_color, label="Men's names")]
    if any(n in female_names_set for n in names):
        entries.append(Patch(facecolor=female_color, label="Women's names"))
    ax.legend(handles=entries, loc="lower right",
              facecolor="white", edgecolor="#cccccc",
              labelcolor="#1a1a2a", fontsize=9)

    # Gospel annotation
    ax.text(max_x * 0.98, -0.7,
            "Bold = gospel name",
            ha="right", va="top", color="#888899", fontsize=8, style="italic")


def save_chart(output_path, names, counts, gospel_set, female_names_set, title):
    max_x = max(counts[n] for n in names) * 1.2

    fig, ax = plt.subplots(figsize=(10, max(5, len(names) * 0.42)))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    draw(ax, names, counts, gospel_set, MALE_COLOR, FEMALE_COLOR,
         female_names_set, max_x, title)

    fig.suptitle(title, color="#1a1a2a", fontsize=13, fontweight="bold", y=1.01)
    fig.text(0.5, -0.01,
             "ASX-listed companies, March 2026  ·  Boards with 3+ members",
             ha="center", color="#888899", fontsize=8)

    plt.tight_layout()
    fig.add_artist(_FBP(
        (0.01, 0.01), 0.98, 0.98,
        boxstyle="round,pad=0.0", linewidth=1.2, linestyle=":",
        edgecolor="#aaaaaa", facecolor="none",
        transform=fig.transFigure, clip_on=False, zorder=10,
    ))
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close()
    print(f"Saved {output_path}")


if __name__ == "__main__":
    counts, gender_map = load()
    all_men, women = build_rows(counts, gender_map)
    female_names_set = set(women)

    # Chart 1: men only
    save_chart(
        os.path.join(DATA_DIR, "chart_gospel_men.png"),
        all_men, counts, GOSPEL, set(),
        "Gospel names among men on ASX boards",
    )

    # Chart 2: men + women interleaved by count
    combined = sorted(all_men + women, key=lambda n: -counts[n])
    save_chart(
        os.path.join(DATA_DIR, "chart_gospel_women.png"),
        combined, counts, GOSPEL, female_names_set,
        "Gospel names vs top women's names on ASX boards",
    )
