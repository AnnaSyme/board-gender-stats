"""
Collect Australian ASX company board member data.
Source: ASX via MarkitDigital API (public, no auth required)
"""

import csv
import json
import time
import os
import sys
import urllib.request
import urllib.error

# --- Config ---
ASX_COMPANIES_URL = "https://www.asx.com.au/asx/research/ASXListedCompanies.csv"
MARKITDIGITAL_URL = "https://asx.api.markitdigital.com/asx-research/1.0/companies/{ticker}/about"
OUTPUT_DIR = "data"
COMPANIES_FILE = os.path.join(OUTPUT_DIR, "asx_companies.csv")
BOARDS_FILE = os.path.join(OUTPUT_DIR, "boards_raw.json")
DIRECTORS_FILE = os.path.join(OUTPUT_DIR, "directors.csv")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://www.asx.com.au/",
}

# Delay between requests (seconds) to avoid rate limiting
REQUEST_DELAY = 0.5
# Max errors before stopping
MAX_ERRORS = 50


def fetch_url(url, retries=3):
    """Fetch a URL with retries. Returns bytes or None."""
    req = urllib.request.Request(url, headers=HEADERS)
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None  # Company not found, skip silently
            if e.code == 429:
                wait = 10 * (attempt + 1)
                print(f"  Rate limited, waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"  HTTP {e.code} for {url}")
                return None
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)
            else:
                print(f"  Error: {e}")
                return None
    return None


def get_asx_companies():
    """Download the ASX listed companies CSV."""
    print("Downloading ASX company list...")
    data = fetch_url(ASX_COMPANIES_URL)
    if not data:
        raise RuntimeError("Failed to download ASX company list")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(COMPANIES_FILE, "wb") as f:
        f.write(data)
    print(f"Saved to {COMPANIES_FILE}")


def load_companies():
    """Load companies from the saved CSV. Returns list of (ticker, name)."""
    companies = []
    with open(COMPANIES_FILE, "r", encoding="utf-8", errors="replace") as f:
        # ASX CSV has a header at line 3 (first 2 lines are metadata)
        reader = csv.reader(f)
        rows = list(reader)

    # Find the header row
    header_idx = None
    for i, row in enumerate(rows):
        if row and row[0].strip() == "Company name":
            header_idx = i
            break

    if header_idx is None:
        # Try first row
        header_idx = 0

    data_rows = rows[header_idx + 1:]
    for row in data_rows:
        if len(row) >= 2 and row[1].strip():
            name = row[0].strip()
            ticker = row[1].strip()
            if ticker and name:
                companies.append((ticker, name))

    print(f"Loaded {len(companies)} ASX companies")
    return companies


def parse_name(full_name):
    """
    Parse 'Mr John Smith' into (gender, first_name, last_name).
    Returns (gender, first_name, full_name_clean)
    gender: 'M', 'F', or 'U' (unknown)
    """
    name = full_name.strip()

    gender = "U"
    prefix = ""

    # Extract prefix
    prefixes_male = ["Mr ", "Mr. ", "Dr (Mr) "]
    prefixes_female = ["Ms ", "Ms. ", "Mrs ", "Mrs. ", "Miss "]
    prefixes_unknown = ["Dr ", "Dr. ", "Prof ", "Prof. ", "Hon "]

    for p in prefixes_male:
        if name.startswith(p):
            gender = "M"
            prefix = p
            name = name[len(p):]
            break

    if gender == "U":
        for p in prefixes_female:
            if name.startswith(p):
                gender = "F"
                prefix = p
                name = name[len(p):]
                break

    if gender == "U":
        for p in prefixes_unknown:
            if name.startswith(p):
                prefix = p
                name = name[len(p):]
                break

    # Extract first name (first word after prefix)
    parts = name.split()
    first_name = parts[0] if parts else name

    # Remove any trailing initials/qualifications from first name
    # e.g. "John P." -> "John"
    if len(first_name) <= 2 and len(parts) > 1:
        first_name = parts[1]  # skip single-letter initial

    return gender, first_name, name


def is_board_member(title):
    """Return True if this role is a board-level role (not just management)."""
    title_lower = title.lower()
    board_keywords = [
        "director", "chair", "chairman", "chairwoman", "chairperson",
        "ceo", "chief executive", "managing director", "executive director",
    ]
    # Exclude pure management roles that aren't directors
    exclude_keywords = ["general manager", "investor relations", "company secretary"]
    for excl in exclude_keywords:
        if excl in title_lower:
            # But if they're also listed as director, keep them
            if "director" not in title_lower:
                return False
    for kw in board_keywords:
        if kw in title_lower:
            return True
    return False


def collect_board_data(companies, resume=True):
    """Fetch board data for all companies. Saves incrementally."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Load existing data if resuming
    existing = {}
    if resume and os.path.exists(BOARDS_FILE):
        with open(BOARDS_FILE, "r") as f:
            existing = json.load(f)
        print(f"Resuming: already have {len(existing)} companies")

    errors = 0
    processed = 0

    for i, (ticker, name) in enumerate(companies):
        if ticker in existing:
            continue

        if errors >= MAX_ERRORS:
            print(f"\nToo many errors ({errors}), stopping early.")
            break

        url = MARKITDIGITAL_URL.format(ticker=ticker)
        data = fetch_url(url)

        if data is None:
            existing[ticker] = {"error": True, "name": name}
        else:
            try:
                parsed = json.loads(data)
                company_data = parsed.get("data", {})
                directors = company_data.get("directors", [])
                existing[ticker] = {
                    "name": company_data.get("displayName", name),
                    "directors": directors,
                    "error": False,
                }
            except json.JSONDecodeError:
                existing[ticker] = {"error": True, "name": name}
                errors += 1

        processed += 1

        # Progress update every 50 companies
        if processed % 50 == 0:
            success = sum(1 for v in existing.values() if not v.get("error"))
            print(f"Progress: {i+1}/{len(companies)} companies | {success} with data | {errors} errors")
            # Save incrementally
            with open(BOARDS_FILE, "w") as f:
                json.dump(existing, f)

        time.sleep(REQUEST_DELAY)

    # Final save
    with open(BOARDS_FILE, "w") as f:
        json.dump(existing, f)

    success = sum(1 for v in existing.values() if not v.get("error"))
    print(f"\nDone! {len(existing)} companies total, {success} with board data")
    return existing


def export_directors_csv(boards_data):
    """Export a flat CSV of all directors."""
    rows = []
    for ticker, company in boards_data.items():
        if company.get("error"):
            continue
        company_name = company.get("name", ticker)
        for d in company.get("directors", []):
            raw_name = d.get("name", "")
            title = d.get("title", "")
            if not raw_name:
                continue

            gender, first_name, clean_name = parse_name(raw_name)
            board_member = is_board_member(title)

            rows.append({
                "ticker": ticker,
                "company": company_name,
                "raw_name": raw_name,
                "clean_name": clean_name,
                "first_name": first_name,
                "title": title,
                "gender": gender,
                "is_board": board_member,
            })

    if not rows:
        print("No director data to export")
        return

    with open(DIRECTORS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    total = len(rows)
    board_only = sum(1 for r in rows if r["is_board"])
    women = sum(1 for r in rows if r["gender"] == "F")
    men = sum(1 for r in rows if r["gender"] == "M")
    print(f"\nExported {total} people ({board_only} board-level)")
    print(f"Gender: {men} men ({men*100//total}%), {women} women ({women*100//total}%)")
    print(f"Saved to {DIRECTORS_FILE}")


if __name__ == "__main__":
    # Step 1: Get company list
    if not os.path.exists(COMPANIES_FILE):
        get_asx_companies()

    companies = load_companies()

    # Optional: limit to first N companies for testing
    if "--test" in sys.argv:
        companies = companies[:20]
        print(f"TEST MODE: using first {len(companies)} companies")

    # Step 2: Collect board data
    print(f"\nCollecting board data for {len(companies)} companies...")
    print("This will take a while. Press Ctrl+C to pause (progress is saved).\n")
    boards = collect_board_data(companies)

    # Step 3: Export flat CSV
    export_directors_csv(boards)
