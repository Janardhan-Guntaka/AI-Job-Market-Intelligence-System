# Contributing to CareerOps AI

Thank you for your interest in contributing! This project is open source and welcomes contributions from developers, students, and job seekers.

## Ways to Contribute

- 🐛 **Bug reports** — open a GitHub issue
- 🌐 **New job portal** — add a scraper following the guide below
- 🤖 **Improve AI matching** — enhance the RAG pipeline
- 🎨 **Frontend** — improve UI components or add new pages
- 📖 **Documentation** — fix or improve docs

---

## Adding a New Job Portal Scraper

Every scraper must:
1. Extend `BasePortalScraper` in `server/app/services/scraper.py`
2. Implement the `_fetch()` method
3. Return `List[ScrapedJob]` — use the `ScrapedJob` dataclass
4. Set a unique `name` class attribute (used as the `source` field in DB)
5. Set `source_url` on each job to the canonical job posting URL (dedup key)

### Template

```python
class MyPortalScraper(BasePortalScraper):
    name = "myportal"
    API_URL = "https://myportal.com/api/jobs"

    def _fetch(self) -> List[ScrapedJob]:
        logger.info("[myportal] fetching jobs …")
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(self.API_URL)
            resp.raise_for_status()
            raw_jobs = resp.json().get("jobs", [])

        results = []
        for raw in raw_jobs:
            title = raw.get("title", "Unknown")
            desc = clean_html(raw.get("description", ""))
            url = raw.get("url", "")
            if not url:
                continue  # skip jobs with no canonical URL

            results.append(ScrapedJob(
                title=title,
                company=raw.get("company", "Unknown"),
                location=raw.get("location", "Worldwide"),
                remote="Remote",
                category=raw.get("category", "Software Engineering"),
                description=desc,
                source=self.name,
                source_url=url,
                apply_url=url,
                skills=extract_skills_from_text(desc),
                experience_level=infer_experience_level(title, desc),
                posted_date=parse_date(raw.get("date", "")),
            ))
        logger.info("[myportal] fetched %d jobs", len(results))
        return results
```

Then add it to the `ALL_SCRAPERS` list at the bottom of `scraper.py`:

```python
ALL_SCRAPERS: List[BasePortalScraper] = [
    RemotiveScraper(),
    RemoteOKScraper(),
    JobicyScraper(),
    WeWorkRemotelyScraper(),
    AdzunaScraper(),
    MyPortalScraper(),  # ← add here
]
```

### Rules for Scrapers
- Use only **free, public APIs or RSS feeds** — no scraping with authentication bypass
- Respect `robots.txt` and API rate limits
- Add appropriate `User-Agent` headers
- Handle errors gracefully (the `BasePortalScraper.fetch()` wrapper catches exceptions)
- Set realistic timeouts

---

## Code Standards

- Python: follow PEP 8, run `flake8 server/` before submitting
- JavaScript/React: functional components, hooks, no class components
- All new services must have `try/except` blocks with logging
- No hardcoded credentials — use `.env` / environment variables

## Pull Request Process

1. Fork the repo and create a feature branch
2. Write/update tests for your changes
3. Run `pytest tests/` — all tests must pass
4. Submit a PR with a clear description

---

## Development Setup

```bash
# Backend
cd server
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd client
npm install
npm run dev
```
