"""
Shared name-combination logic for all ASX board charts.

Variant names are merged into a single canonical label so that
e.g. "Dave" and "David" are counted together as "David".

Usage:
    from name_combos import canonical, load_combined
"""
import csv
import os
from collections import Counter, defaultdict

# ── Combination dictionaries ──────────────────────────────────────────────────

MALE_COMBOS = {
    "David":       ["David", "Dave"],
    "Michael":     ["Michael", "Mike", "Mick"],
    "John":        ["John", "Jon"],
    "Stephen":     ["Stephen", "Steven", "Steve"],
    "James":       ["James", "Jim", "Jamie"],
    "Christopher": ["Christopher", "Chris"],
    "Matthew":     ["Matthew", "Matt"],
    "Timothy":     ["Timothy", "Tim"],
    "Philip":      ["Philip", "Phillip", "Phil"],
    "Peter":       ["Peter", "Pete"],
    "Andrew":      ["Andrew", "Andy"],
    "Gregory":     ["Gregory", "Greg"],
    "Geoffrey":    ["Geoffrey", "Geoff"],
}

FEMALE_COMBOS = {
    "Kate":      ["Kate", "Katherine", "Kathryn", "Kathy", "Katie"],
    "Sarah":     ["Sarah", "Sara"],
    "Anne":      ["Anne", "Anna", "Ann", "Annie"],
    "Jennifer":  ["Jennifer", "Jenny"],
    "Christine": ["Christine", "Christina"],
    "Susan":     ["Susan", "Sue"],
}

# ── Reverse lookup: raw variant → canonical name ──────────────────────────────

_VARIANT_MAP: dict[str, str] = {}
for _canonical, _variants in {**MALE_COMBOS, **FEMALE_COMBOS}.items():
    for _v in _variants:
        _VARIANT_MAP[_v] = _canonical


def canonical(name: str) -> str:
    """Return the canonical name for a variant, or the name itself if standalone."""
    return _VARIANT_MAP.get(name, name)


def load_combined(data_dir: str):
    """
    Load directors.csv and return (counts, gender_map) with name variants merged.

    counts     : Counter  — canonical_name → total board seats
    gender_map : defaultdict(Counter) — canonical_name → {"M": n, "F": n, "U": n}
    """
    counts     = Counter()
    gender_map = defaultdict(Counter)

    with open(os.path.join(data_dir, "directors.csv"), newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["is_board"] == "True":
                name = canonical(row["first_name"])
                counts[name] += 1
                gender_map[name][row["gender"]] += 1

    return counts, gender_map
