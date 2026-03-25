![Names vs Women](data/names_vs_women_lollipop.png)

**There are more Davids than women on 129 ASX-listed company boards.** On more than half of all ASX boards, a single male first name appears as often or more often than the total number of women combined.

Analysis of 1,819 ASX companies (March 2026): 77% of board seats are held by men, 18.5% by women, and 47.7% of companies have no women on their board at all. The gender gap is concentrated in the Materials (mining) sector, which makes up ~42% of all ASX listings.

**Inspiration**

This was inspired by [Deb Verhoeven's](https://bsky.app/profile/bestqualitycrab.bsky.social) work on _Daversity_ — the phenomenon of men who work mostly with other men without noticing. Her analysis of Australian research funding is well worth reading: [Australian Research: The Daversity Problem](https://debverhoeven.com/australian-research-daversity-problem-analysis-shows-many-men-work-mostly-men/).

**Data sources**

Board member data is fetched from the MarkitDigital API used by the ASX website — no API key required:
- Company list: `https://www.asx.com.au/asx/research/ASXListedCompanies.csv`
- Board data: `https://asx.api.markitdigital.com/asx-research/1.0/companies/{ticker}/about`

Gender is inferred from name prefixes (Mr/Sir/Lord → male; Ms/Mrs/Miss/Dame → female). People listed with titles like Dr or Prof. are classified as unknown (~4%).

**Usage**

```bash
# 1. Collect board data for all ~1,978 ASX companies (~20 min)
python3 collect_boards.py

# 2. Run gender analysis and "more names than women" report
python3 analyze_boards.py

# 3. Generate charts
python3 chart_names_vs_women.py
```

Requires Python 3 and `matplotlib` (`pip install matplotlib`). The collector uses only standard library modules.

**Files**

```
collect_boards.py           fetch board data from ASX / MarkitDigital API
analyze_boards.py           gender analysis + "more names than women" report
chart_names_vs_women.py     lollipop charts
data/
  asx_companies.csv                    ASX company list
  more_name_than_women_multi.csv       boards where a name appears 2+ times > all women
  more_name_than_women_all.csv         all boards where any name count > all women
  names_vs_women_lollipop.png          chart: top 20 names vs women (combined variants)
  names_comparison.png                 chart: before/after name combining
```

`boards_raw.json` and `directors.csv` are excluded from the repo — regenerate them by running `collect_boards.py`.
