"""
Analyze Australian ASX board data.
Finds companies where a single male first name appears more times than all women combined.
Ranks results by the excess (e.g. "5 more Jeffs than women").
"""

import csv
import json
import os
from collections import defaultdict, Counter

DATA_DIR = "data"
DIRECTORS_FILE = os.path.join(DATA_DIR, "directors.csv")
BOARDS_FILE = os.path.join(DATA_DIR, "boards_raw.json")


def load_directors(board_only=True):
    """Load directors CSV. Returns list of dicts."""
    rows = []
    with open(DIRECTORS_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if board_only and row["is_board"] != "True":
                continue
            rows.append(row)
    return rows


def analyze_name_vs_women(directors, min_name_count=2):
    """
    For each company, find cases where a single male name appears >= total women on board.
    Returns list of dicts sorted by excess (name_count - women_count) descending.

    min_name_count: minimum times a name must appear to be reported
    """
    # Group by company
    by_company = defaultdict(list)
    for d in directors:
        by_company[d["ticker"]].append(d)

    results = []

    for ticker, members in by_company.items():
        company_name = members[0]["company"]
        total = len(members)
        if total < 2:
            continue

        women = [m for m in members if m["gender"] == "F"]
        men = [m for m in members if m["gender"] == "M"]
        unknown = [m for m in members if m["gender"] == "U"]

        women_count = len(women)

        # Count occurrences of each male first name
        male_name_counts = Counter(m["first_name"] for m in men)

        # Find names that appear more than the total women count
        for name, count in male_name_counts.items():
            if count > women_count and count >= min_name_count:
                excess = count - women_count
                results.append({
                    "ticker": ticker,
                    "company": company_name,
                    "name": name,
                    "name_count": count,
                    "women_count": women_count,
                    "excess": excess,
                    "total_board": total,
                    "men_count": len(men),
                    "unknown_count": len(unknown),
                    "women_names": ", ".join(
                        f"{w['first_name']} {w['clean_name'].split()[-1] if len(w['clean_name'].split()) > 1 else ''}"
                        for w in women
                    ) if women else "(none)",
                    "all_men_with_name": ", ".join(
                        f"{m['clean_name']}" for m in men if m["first_name"] == name
                    ),
                })

    # Sort by excess descending, then name_count descending
    results.sort(key=lambda x: (-x["excess"], -x["name_count"], x["company"]))
    return results


def analyze_any_name_more_than_women(directors):
    """
    For each company, find the single male name that most exceeds the total women count.
    One row per company (the "winning" name).
    Catches both multi-name cases (2x John > 1 woman) and 0-women cases.
    """
    by_company = defaultdict(list)
    for d in directors:
        by_company[d["ticker"]].append(d)

    results = []

    for ticker, members in by_company.items():
        company_name = members[0]["company"]
        total = len(members)
        if total < 3:  # Skip very small boards
            continue

        women = [m for m in members if m["gender"] == "F"]
        men = [m for m in members if m["gender"] == "M"]

        women_count = len(women)

        # Count occurrences of each male first name
        male_name_counts = Counter(m["first_name"] for m in men)

        # Find the name with the highest excess over women count
        best = None
        for name, count in male_name_counts.items():
            if count > women_count:
                excess = count - women_count
                if best is None or excess > best["excess"] or (
                    excess == best["excess"] and count > best["name_count"]
                ):
                    best = {
                        "ticker": ticker,
                        "company": company_name,
                        "name": name,
                        "name_count": count,
                        "women_count": women_count,
                        "excess": excess,
                        "total_board": total,
                        "men_count": len(men),
                        "unknown_count": total - len(men) - women_count,
                        "all_men_with_name": ", ".join(
                            m["clean_name"] for m in men if m["first_name"] == name
                        ),
                        "women_names": ", ".join(
                            w["clean_name"] for w in women
                        ) if women else "(none)",
                        "all_board_names": " | ".join(
                            f"{m['first_name']} {m['clean_name'].split()[-1] if len(m['clean_name'].split()) > 1 else ''} ({'F' if m['gender']=='F' else 'M' if m['gender']=='M' else '?'})"
                            for m in members
                        ),
                    }
        if best:
            results.append(best)

    results.sort(key=lambda x: (-x["excess"], -x["name_count"]))
    return results


def print_report(results, title, limit=100):
    """Print a formatted report."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}")
    print(f"Total boards found: {len(results)}")
    print()

    for i, r in enumerate(results[:limit], 1):
        excess_str = f"+{r['excess']}" if r['excess'] > 0 else str(r['excess'])
        print(
            f"{i:3}. {r['company']} ({r['ticker']}) — "
            f"{r['name_count']}x {r['name']} vs {r['women_count']} women "
            f"(excess: {excess_str})"
        )
        print(f"     Board: {r['total_board']} total | {r['men_count']} men | {r['women_count']} women")
        print(f"     {r['name']}s: {r['all_men_with_name']}")
        if r['women_names'] != "(none)":
            print(f"     Women: {r['women_names']}")
        else:
            print(f"     Women: (none)")
        print()


def summary_stats(directors):
    """Print overall summary statistics."""
    total = len(directors)
    women = sum(1 for d in directors if d["gender"] == "F")
    men = sum(1 for d in directors if d["gender"] == "M")
    unknown = sum(1 for d in directors if d["gender"] == "U")

    companies = set(d["ticker"] for d in directors)
    women_zero = set()
    by_company = defaultdict(list)
    for d in directors:
        by_company[d["ticker"]].append(d)
    for ticker, members in by_company.items():
        if not any(m["gender"] == "F" for m in members):
            women_zero.add(ticker)

    # Most common male names
    male_names = Counter(d["first_name"] for d in directors if d["gender"] == "M")

    print(f"\n{'='*80}")
    print(f"  SUMMARY STATISTICS")
    print(f"{'='*80}")
    print(f"Companies with board data: {len(companies)}")
    print(f"Total board positions: {total}")
    print(f"  Men:     {men:5} ({men*100//total if total else 0}%)")
    print(f"  Women:   {women:5} ({women*100//total if total else 0}%)")
    print(f"  Unknown: {unknown:5} ({unknown*100//total if total else 0}%)")
    print(f"\nCompanies with NO women on board: {len(women_zero)} ({len(women_zero)*100//len(companies) if companies else 0}%)")
    print(f"\nTop 20 male first names:")
    for name, count in male_names.most_common(20):
        print(f"  {name:15} {count}")


def save_results_csv(results, filename):
    """Save results to CSV."""
    if not results:
        return
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    print(f"Saved to {filepath}")


if __name__ == "__main__":
    if not os.path.exists(DIRECTORS_FILE):
        print(f"ERROR: {DIRECTORS_FILE} not found. Run collect_boards.py first.")
        exit(1)

    print("Loading directors data...")
    directors = load_directors(board_only=True)
    print(f"Loaded {len(directors)} board positions")

    # Summary stats
    summary_stats(directors)

    # Main analysis: boards where a name appears more than total women
    print("\n\nRunning 'more Xs than women' analysis...")
    results = analyze_any_name_more_than_women(directors)

    # Report 1: Cases where a name appears 2+ times and exceeds women (the interesting ones)
    multi_results = [r for r in results if r["name_count"] >= 2]
    print_report(
        multi_results,
        "BOARDS WHERE A MALE NAME APPEARS 2+ TIMES AND OUTNUMBERS ALL WOMEN",
        limit=50
    )
    save_results_csv(multi_results, "more_name_than_women_multi.csv")

    # Report 2: ALL cases including boards with 0 women where even 1 man beats the count
    print_report(
        results,
        "ALL BOARDS WHERE ANY MALE NAME COUNT EXCEEDS TOTAL WOMEN (sorted by excess)",
        limit=100
    )
    save_results_csv(results, "more_name_than_women_all.csv")

    print("\n\nDone! Results saved to data/ directory.")
