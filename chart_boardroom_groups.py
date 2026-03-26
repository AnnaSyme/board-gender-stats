"""
Boardroom Groups Chart — ASX board seats as 36 chairs around a table.
Named groups: Gospels, David+Michael, Peter+Andrew, etc.
One chair = Matthew+Mark+Luke+John (the Gospels).
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
OUTPUT_PATH = os.path.join(DATA_DIR, "chart_boardroom_groups.png")

N_CHAIRS = 36
TABLE_R  = 0.88
CHAIR_R  = 1.32
SCALE    = 0.090   # slightly smaller to fit 36 chairs snugly

# ── Group definitions ─────────────────────────────────────────────────────────

# Map first_name → group key
NAME_TO_GROUP = {}
for n in ["Matthew", "Matt", "Mark", "Luke", "John", "Jon"]:
    NAME_TO_GROUP[n] = "gospels"
for n in ["David", "Dave", "Michael", "Mike", "Mick"]:
    NAME_TO_GROUP[n] = "david_michael"
for n in ["Peter", "Pete", "Andrew", "Andy"]:
    NAME_TO_GROUP[n] = "peter_andrew"
for n in ["Paul", "James", "Jim", "Jamie"]:
    NAME_TO_GROUP[n] = "paul_james"
for n in ["Stephen", "Steven", "Steve", "Ian", "Anthony", "Tony"]:
    NAME_TO_GROUP[n] = "stephen_ian_anthony"
for n in ["Robert", "Rob", "Bob", "Richard", "Rick", "Rich"]:
    NAME_TO_GROUP[n] = "robert_richard"
for n in ["Simon", "Philip", "Phillip", "Phil", "Thomas", "Tom"]:
    NAME_TO_GROUP[n] = "simon_philip_thomas"

# Interleave single-chair groups with multi-chair groups so they spread
# around the arc rather than clustering at the bottom.
ORDER = [
    "women",
    "david_michael",
    "paul_james",
    "gospels",
    "robert_richard",
    "peter_andrew",
    "simon_philip_thomas",
    "stephen_ian_anthony",
    "other_men",
]

COLORS = {
    "women":               "#7b4fa0",
    "david_michael":       "#c0392b",
    "gospels":             "#e07020",
    "peter_andrew":        "#c8970a",
    "paul_james":          "#1a7fa0",
    "stephen_ian_anthony": "#2e6dc4",
    "robert_richard":      "#28a068",
    "simon_philip_thomas": "#b07030",
    "other_men":           "#ddddee",
}

LABELS = {
    "women":               "Women",
    "david_michael":       "Davids &\nMichaels",
    "gospels":             "Matthews, Marks,\nLukes & Johns",
    "peter_andrew":        "Peters &\nAndrews",
    "paul_james":          "Pauls &\nJames",
    "stephen_ian_anthony": "Stephens, Ians\n& Anthonys",
    "robert_richard":      "Roberts &\nRichards",
    "simon_philip_thomas": "Simons, Philips\n& Thomases",
    "other_men":           "Other men",
}


def load_counts():
    by_company = defaultdict(list)
    with open(os.path.join(DATA_DIR, "directors.csv"), newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["is_board"] == "True":
                by_company[row["ticker"]].append(row)

    all_d = [m for members in by_company.values()
             if len(members) >= 3 for m in members]

    cats = {k: 0 for k in ORDER}
    for d in all_d:
        if d["gender"] == "F":
            cats["women"] += 1
        elif d["gender"] == "M":
            group = NAME_TO_GROUP.get(d["first_name"])
            if group:
                cats[group] += 1
            else:
                cats["other_men"] += 1
        else:
            cats["other_men"] += 1

    return cats, len(all_d)


def proportional_chairs(cats, total, n=N_CHAIRS):
    raw = {k: cats[k] / total * n for k in ORDER}
    floored = {k: int(v) for k, v in raw.items()}
    deficit = n - sum(floored.values())
    by_frac = sorted(ORDER, key=lambda k: raw[k] - floored[k], reverse=True)
    for k in by_frac[:deficit]:
        floored[k] += 1
    return floored


def draw_chart():
    cats, total = load_counts()
    chair_counts = proportional_chairs(cats, total)

    print("Chair allocation:")
    for k in ORDER:
        pct = cats[k] / total * 100
        print(f"  {k:25} {cats[k]:5} directors ({pct:4.1f}%)  → {chair_counts[k]} chair(s)")

    # Build colour list
    chair_colors = []
    for cat in ORDER:
        chair_colors.extend([COLORS[cat]] * chair_counts[cat])

    BG = "white"
    fig, ax = plt.subplots(figsize=(12, 12))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_aspect("equal")
    ax.set_xlim(-3.2, 3.2)
    ax.set_ylim(-2.8, 3.2)
    ax.axis("off")

    # ── Table ─────────────────────────────────────────────────────────────────
    ax.add_patch(Circle((0, 0), TABLE_R, facecolor="white",
                         edgecolor="#888899", linewidth=2.5, zorder=2))
    ax.text(0, 0.15, f"{total:,}", ha="center", va="center",
            color="#444466", fontsize=15, fontweight="bold", zorder=10)
    ax.text(0, -0.18, "board\nseats", ha="center", va="center",
            color="#666688", fontsize=9, linespacing=1.5, zorder=10)

    # ── Chairs ────────────────────────────────────────────────────────────────
    for i, color in enumerate(chair_colors):
        a = np.radians(90 - i * 360 / N_CHAIRS)
        ax.add_patch(Circle((CHAIR_R * np.cos(a), CHAIR_R * np.sin(a)),
                             SCALE, fill=False, edgecolor=color, linewidth=7.5, zorder=5))

    # ── Annotations — with label spreading ────────────────────────────────────
    # Collect natural positions first
    ann_data = []
    for cat in ORDER:
        if chair_counts[cat] == 0:
            continue
        indices = [i for i, c in enumerate(chair_colors) if c == COLORS[cat]]
        mid = indices[len(indices) // 2]
        chair_angle = np.radians(90 - mid * 360 / N_CHAIRS)
        cx = CHAIR_R * np.cos(chair_angle)
        cy = CHAIR_R * np.sin(chair_angle)
        n_dir = cats[cat]
        pct = n_dir / total * 100
        label = f"{LABELS[cat]}\n{n_dir:,}  ({pct:.0f}%)"
        base_r = CHAIR_R + (0.62 if chair_counts[cat] == 1 else 0.78)
        ann_data.append({
            "cat": cat,
            "chair_angle": chair_angle,
            "label_angle": chair_angle,
            "cx": cx, "cy": cy,
            "label_r": base_r,
            "label": label,
        })

    # Iteratively spread label angles so no two are closer than MIN_GAP
    MIN_GAP = np.radians(20)
    for _ in range(80):
        moved = False
        for i in range(len(ann_data)):
            for j in range(i + 1, len(ann_data)):
                diff = ann_data[i]["label_angle"] - ann_data[j]["label_angle"]
                if abs(diff) < MIN_GAP:
                    push = (MIN_GAP - abs(diff)) / 2 + 1e-6
                    if diff >= 0:
                        ann_data[i]["label_angle"] += push
                        ann_data[j]["label_angle"] -= push
                    else:
                        ann_data[i]["label_angle"] -= push
                        ann_data[j]["label_angle"] += push
                    moved = True
        if not moved:
            break

    for ann in ann_data:
        la = ann["label_angle"]
        lr = ann["label_r"]
        lx = lr * np.cos(la)
        ly = lr * np.sin(la)
        ax.annotate(
            ann["label"],
            xy=(ann["cx"], ann["cy"]), xytext=(lx, ly),
            ha="center", va="center",
            color="#1a1a2a", fontsize=8, fontweight="bold",
            linespacing=1.5,
            arrowprops=dict(arrowstyle="->", color="#888899", lw=1.0),
        )

    # ── Title ─────────────────────────────────────────────────────────────────
    ax.text(0, 3.05, "A seat at the table",
            ha="center", va="center", color="#1a1a2a",
            fontsize=13, fontweight="bold")
    ax.text(0, 2.78,
            "Every ASX board seat, represented as 36 chairs",
            ha="center", va="center", color="#9090bb", fontsize=9.5)

    # ── Footer ────────────────────────────────────────────────────────────────
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
    plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close()
    print(f"\nSaved {OUTPUT_PATH}")


if __name__ == "__main__":
    draw_chart()
