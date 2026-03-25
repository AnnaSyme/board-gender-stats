"""
Generate lollipop chart: male first names that outnumber women on ASX boards.
Produces two files:
  data/names_vs_women_lollipop.png   — combined name variants
  data/names_comparison.png          — before/after side-by-side comparison

Requires: matplotlib
  pip install matplotlib
"""

import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from collections import Counter

DATA_DIR = "data"
BOARDS_FILE = f"{DATA_DIR}/boards_raw.json"

WOMEN_PREFIXES = {"Ms", "Mrs", "Miss", "Madam", "Dame"}
MEN_PREFIXES   = {"Mr", "Sir", "Lord", "Master"}

# Map name variants to a single canonical display name.
# Names intentionally kept separate: Anthony/Tony, James/Jim,
# Geoff/Jeffrey, Michael/Mick, Marc/Mark.
NAME_GROUPS = {
    "Christopher": "Christopher", "Chris": "Christopher",
    "Greg": "Greg",               "Gregory": "Greg",
    "Stephen": "Stephen",         "Steven": "Stephen",    "Steve": "Stephen",
    "Matthew": "Matthew",         "Matt": "Matthew",
    "Timothy": "Timothy",         "Tim": "Timothy",
    "Nicholas": "Nicholas",       "Nick": "Nicholas",     "Nicolas": "Nicholas",
    "Philip": "Philip",           "Phillip": "Philip",    "Phil": "Philip",
    "Alexander": "Alexander",     "Alex": "Alexander",
    "Alan": "Alan",               "Allan": "Alan",
    "Benjamin": "Ben",            "Ben": "Ben",
    "Daniel": "Daniel",           "Dan": "Daniel",        "Danny": "Daniel",
    "Robert": "Robert",           "Rob": "Robert",        "Bob": "Robert",
    "William": "William",         "Bill": "William",      "Will": "William",
    "Graham": "Graham",           "Graeme": "Graham",
    "Jonathan": "Jonathan",       "Jon": "Jonathan",      "Jonathon": "Jonathan",
    "Gary": "Gary",               "Garry": "Gary",
    "Russell": "Russell",         "Russel": "Russell",
    "Stuart": "Stuart",           "Stewart": "Stuart",
    "Brian": "Brian",             "Bryan": "Brian",
    "Neil": "Neil",               "Neal": "Neil",
    "Patrick": "Patrick",         "Pat": "Patrick",
    "Peter": "Peter",             "Pete": "Peter",
    "Andrew": "Andrew",           "Andy": "Andrew",
    "David": "David",             "Dave": "David",
    "Richard": "Richard",         "Rick": "Richard",
    "Thomas": "Thomas",           "Tom": "Thomas",        "Tommy": "Thomas",
    "Geoff": "Geoff",             "Geoffrey": "Geoff",
    "Jeffrey": "Jeffrey",         "Jeff": "Jeffrey",
}


def canonical(name, use_combine=True):
    if use_combine:
        return NAME_GROUPS.get(name, name)
    return name


def compute_name_beats(boards, use_combine=True):
    """
    For each company board, find canonical male first names whose count
    exceeds the total number of women on that board.
    Returns Counter: name -> number of boards where it beats women.
    """
    name_beats = Counter()
    for ticker, info in boards.items():
        if info.get("error"):
            continue
        directors = info.get("directors", [])
        if len(directors) < 3:
            continue

        women_count = sum(
            1 for d in directors
            if d.get("name", "").split()[0] in WOMEN_PREFIXES
        )

        male_first = []
        for d in directors:
            parts = d.get("name", "").strip().split()
            if parts and parts[0] in MEN_PREFIXES and len(parts) >= 2:
                male_first.append(canonical(parts[1], use_combine))

        name_counts = Counter(male_first)
        seen = set()
        for name, count in name_counts.items():
            if count > women_count and name not in seen:
                name_beats[name] += 1
                seen.add(name)
    return name_beats


def draw_lollipop(ax, top20, title):
    names  = [t[0] for t in top20][::-1]
    counts = [t[1] for t in top20][::-1]
    y = range(len(names))
    max_c = max(counts)
    colors = [plt.cm.YlOrRd(0.3 + 0.7 * c / max_c) for c in counts]

    for yi, count, color in zip(y, counts, colors):
        ax.hlines(yi, 0, count, colors="#444455", linewidth=1.5, zorder=1)
        ax.scatter(count, yi, color=color, s=100, zorder=3)
        ax.text(count + 0.8, yi, str(count), va="center", ha="left",
                color="#dddddd", fontsize=9, fontweight="bold")

    ax.set_yticks(list(y))
    ax.set_yticklabels(names, fontsize=10, color="#ccccdd")
    ax.set_xlim(0, max(counts) + 14)
    ax.set_title(title, color="white", fontsize=11, fontweight="bold", pad=10)
    ax.set_xlabel("Boards where name outnumbers all women",
                  color="#aaaacc", fontsize=8, labelpad=8)
    ax.xaxis.grid(True, color="#222233", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(colors="#aaaacc", which="both")
    for spine in ax.spines.values():
        spine.set_edgecolor("#333344")
    ax.set_facecolor("#0f1117")


def save_lollipop(top20, output_path):
    """Single lollipop chart (combined names)."""
    names  = [t[0] for t in top20][::-1]
    counts = [t[1] for t in top20][::-1]
    y = range(len(names))
    max_c = max(counts)
    colors = [plt.cm.YlOrRd(0.3 + 0.7 * c / max_c) for c in counts]

    fig, ax = plt.subplots(figsize=(10, 8))
    fig.patch.set_facecolor("#0f1117")
    ax.set_facecolor("#0f1117")

    for yi, count, color in zip(y, counts, colors):
        ax.hlines(yi, 0, count, colors="#444455", linewidth=1.5, zorder=1)
        ax.scatter(count, yi, color=color, s=120, zorder=3)
        ax.text(count + 0.8, yi, str(count), va="center", ha="left",
                color="#dddddd", fontsize=10, fontweight="bold")

    ax.set_yticks(list(y))
    ax.set_yticklabels(names, fontsize=11, color="#ccccdd")
    ax.set_xlabel(
        "Number of ASX boards where this name outnumbers all women combined",
        color="#aaaacc", fontsize=10, labelpad=12,
    )
    ax.set_xlim(0, max(counts) + 12)
    ax.set_title(
        '"More [Name]s Than Women"\nASX-listed company boards, March 2026',
        color="white", fontsize=14, fontweight="bold", pad=16,
    )
    fig.text(
        0.5, 0.01,
        "Boards where a single male first name appears more times than the "
        "total number of women on that board.",
        ha="center", color="#888899", fontsize=9,
    )
    ax.xaxis.grid(True, color="#222233", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(colors="#aaaacc", which="both")
    for spine in ax.spines.values():
        spine.set_edgecolor("#333344")

    plt.tight_layout(rect=[0, 0.04, 1, 1])
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="#0f1117")
    plt.close()
    print(f"Saved {output_path}")


def save_comparison(old_top, new_top, output_path):
    """Side-by-side before/after chart."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))
    fig.patch.set_facecolor("#0f1117")
    draw_lollipop(ax1, old_top, "Before — name variants separate")
    draw_lollipop(ax2, new_top, "After — name variants combined")
    fig.suptitle(
        '"More [Name]s Than Women" — ASX Board Analysis, March 2026',
        color="white", fontsize=14, fontweight="bold", y=1.01,
    )
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="#0f1117")
    plt.close()
    print(f"Saved {output_path}")


if __name__ == "__main__":
    import os
    if not os.path.exists(BOARDS_FILE):
        print(f"ERROR: {BOARDS_FILE} not found. Run collect_boards.py first.")
        exit(1)

    print("Loading board data...")
    with open(BOARDS_FILE) as f:
        boards = json.load(f)

    print("Computing name beats (combined)...")
    combined_beats = compute_name_beats(boards, use_combine=True)
    new_top = combined_beats.most_common(20)

    print("Computing name beats (separate)...")
    raw_beats = compute_name_beats(boards, use_combine=False)
    old_top = raw_beats.most_common(20)

    save_lollipop(new_top, f"{DATA_DIR}/names_vs_women_lollipop.png")
    save_comparison(old_top, new_top, f"{DATA_DIR}/names_comparison.png")

    print("\nTop 20 (combined):")
    for name, count in new_top:
        print(f"  {name:<15} {count}")
