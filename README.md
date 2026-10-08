# Japan Internship Hunter 🇯🇵

A lightweight, beginner-friendly internship **lead discovery** tool for international students seeking internships in Japan.

## Features
- Searches public Google News RSS results for Japanese and English internship-related queries
- Deduplicates headlines and ranks them with explainable keyword scoring
- Exports a spreadsheet-ready CSV (`output/internship_leads.csv`)
- Runs on GitHub Actions manually or on a weekly schedule
- Uses Python standard library only; no API key and no paid service required

> **Important:** These are **unverified leads**, not confirmed open vacancies. News search may include articles, expired postings and unrelated items. Always visit an employer's official hiring page to verify dates, eligibility and application procedures. Do not enter personal data on suspicious sites.

## Quick start (Mac / Windows / Linux)

Install [Python 3](https://www.python.org/downloads/) and run:

```bash
python3 hunter.py
```

On Windows, you might use `py hunter.py` instead. Open `output/internship_leads.csv` with Excel or Google Sheets.

## Customize

Edit `QUERIES` in `hunter.py` to change target jobs, locations, graduation years and industries. Edit `KEYWORDS` to change relevance scoring. Scores are **rules-based**, not machine-learning or LLM inference.

## Run on GitHub

1. Create a GitHub repository and upload these files, including `.github/workflows/hunter.yml`.
2. Open **Actions** → **Internship Hunter** → **Run workflow**.
3. Download the `internship-leads` artifact from the completed workflow run.
4. The workflow is also scheduled for Fridays at 09:00 Japan time. Scheduled runs can be delayed or disabled due to inactivity; GitHub Actions is not a guaranteed notification service.

## Roadmap
- [x] RSS lead collection
- [x] Relevance ranking and CSV export
- [x] GitHub Actions automation
- [ ] Extract and verify employer's original job posting
- [ ] Confirm application deadlines and eligibility
- [ ] Add optional LLM-based semantic ranking and Chinese summaries
- [ ] Build a small web dashboard

## Skills demonstrated
Python, data collection, RSS/XML parsing, ranking rules, CSV export, GitHub Actions, documentation and source verification.

*Educational project; not affiliated with Google News or any recruiting company.*
