# Japan Internship Hunter 🇯🇵 — V2

A transparent, beginner-friendly internship **lead discovery & triage** tool for international students in Japan. **It does not confirm whether a job is actually open or whether you are eligible.**

## Target profile

- **Locations:** Tokyo and Kanagawa (including Yokohama/Kawasaki)
- **Industries:** consulting, IT/AI, trading companies (商社)
- **Languages:** Japanese, English, or Chinese (only mark a language when the headline explicitly mentions it)
- **Timeframe:** published within the last 30 days for high-priority candidates

## What changed from V1?

- Uses focused Google News RSS queries; prioritizes recent information, deduplicates titles.
- Categorizes possible internship recruitment vs reporting/events/other.
- Flags Tokyo/Kanagawa and industries **only when evident from title**, not from search keywords alone.
- Separates historical results from current leads.
- Keeps a transparent rule-based score; does **not** pretend it is AI or proof of eligibility.
- Includes **optional LLM enrichment** through OpenAI's API; by default it uses **no model and costs nothing**.
- Does **not** invent direct application links. News URL is a discovery/source URL only.

## Quick start

Requires **Python 3.10+**, no pip dependencies:

```bash
python hunter.py
```

Offline replay of your V1 CSV:

```bash
python hunter.py --input internship_leads.csv --today 2026-10-08
```

Output folder (CSV files open in Excel):

| File | What it contains |
| --- | --- |
| `output/all_leads.csv` | Every deduplicated lead and reason for its classification |
| `output/priority_review.csv` | Recent, on-topic titles that **might** be recruiting; still unverified |
| `output/needs_review.csv` | Unclear candidates needing manual inspection |
| `output/summary.json` | Counts and generation date |

The column `url` is an RSS article/source link, **not** necessarily a direct application page. `application_url` is intentionally blank until independently verified. Always open the source and locate the official company application page, then verify **deadline, eligibility, visa requirements, location, language, and job status** before applying.

## GitHub Actions

Go to **Actions → Internship Hunter V2 → Run workflow**, choose `main`, run, then download artifact `internship-hunter-v2-results` from the run Summary. A Friday 09:00 JST weekly schedule is also configured; scheduling may be delayed or disabled due to GitHub policies. No email notifications of the leads are configured.

## Optional model-assisted analysis (may cost money)

If you want model-generated notes on up to 20 high-priority titles, set a repository secret called `OPENAI_API_KEY` under **Settings → Secrets and variables → Actions → New repository secret**. Do not put your key in code or a CSV. The model name is controlled by `OPENAI_MODEL` in the workflow. It only sees title, source, and date; this does not verify the listing. API pricing and availability can change; the model's output may be wrong. If you do not set the key, all rule-based functions still work.

## Quality and limitations

Google News RSS is a **news index**, not a live job-board API. Some queries return outdated posts or irrelevant results, even with `when:30d`. Published date is not application deadline. Missing a location/industry in the title does **not** mean that posting is unsuitable; it remains in the raw review table. Scoring is explainable heuristics, not probability. No scraping of login-required sites; do not send candidate personal data to the model.

## Testing

```bash
python -m unittest discover -s tests -v
```

## Roadmap

- Verified employer job-board sources and applicant links; link verification with permission and rate limits.
- Optional structured AI classification based on official job descriptions with evidence citations.
- Personal profile relevance and human verification workflow.
- Simple public web dashboard for the portfolio.
