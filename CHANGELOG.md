# Changelog

All notable changes to this project are documented here.  
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [2.3.0] — 2026-04-30

### Added
- `LICENSE` file (MIT)
- `.env.example` template so new users know which environment variables are required
- `pyproject.toml` project metadata (name, version, Python requirement, dependencies, repo URL)
- GitHub Actions: `timeout-minutes: 10` on the job to prevent runaway executions
- GitHub Actions: `permissions: contents: read` (least-privilege principle)
- GitHub Actions: failure-notification step — sends a LINE message if the bot crashes

### Changed
- `main.py`: all tunable parameters (`NEWS_FILTER_DAYS`, `REQUEST_TIMEOUT`, `LLM_TEMPERATURE`, model list, topic list) moved to a dedicated **Settings block** at the top of the file for easier maintenance
- `main.py`: added type hints to all functions (`-> list[str]`, `-> str | None`, `-> bool`, etc.)
- `main.py`: `send_line_push()` now returns `bool`; `main()` calls `sys.exit(1)` on LINE push failure so GitHub Actions marks the run as failed
- `requirements.txt`: switched from loose lower-bound pins (`>=`) to exact version locks (`==`) for reproducible installs
- `README.md`: corrected Python version badge and Tech Stack table from `3.10+` → `3.12+`
- `README.md`: Setup section now references `.env.example` instead of inline variable list
- `.gitignore`: expanded with standard Python entries (`__pycache__/`, `.venv/`, `.pytest_cache/`, build artifacts, IDE folders, OS files)

### Removed
- `LINE_API_INFO` constant from `main.py` — was defined but never used (dead code)

---

## [2.2.0] — 2026-04-30

### Added
- Dual-layer date filter to prevent stale articles appearing in the digest
  - Layer 1: `when:7d` appended to all Google News RSS queries (filters at source)
  - Layer 2: `pubDate` field parsed per RSS item — articles older than 7 days are skipped
- `parse_pub_date()` utility function for RSS date string parsing
- `search_news()` now accepts a configurable `days` parameter (default: `7`)
- Log output now reports filtered article count per topic

---

## [2.1.0] — 2026-04-28

### Changed
- Reduced daily digest from 7 articles to 6 (BIM × AI: 3, BIM-MEP: 2, BIM General: 1)
- Increased RSS fetch pool to give Gemini more candidates: BIM × AI (6), BIM-MEP (4), BIM General (3)
- Simplified source line in digest: removed redundant article title, now shows `📰 Source Name` only
- Switched article links from long Google News redirect URLs to `site:` Google Search URLs — shorter, reliably clickable in LINE

### Removed
- Markdown link formatting from LLM output (LINE does not render Markdown; bare URLs auto-become tappable)

---

## [2.0.0] — 2026-04-28

### Added
- Weighted topic distribution across three BIM categories
- `test_line.py` diagnostic utility for LINE token and connectivity checks
- Gyaru-style persona prompt for more natural, personality-driven output

### Changed
- **Breaking:** Replaced DuckDuckGo search with Google News RSS (fixes silent failures on GitHub Actions runners)
- **Breaking:** News domain changed from international geopolitics/science to BIM industry
- Gemini primary model: `gemini-1.5-pro-002` (deprecated) → `gemini-2.0-flash`
- Gemini fallback model updated to `gemini-flash-latest`
- Generation temperature raised from `0.3` → `0.75`

### Removed
- `line-bot-sdk` dependency (replaced with direct `requests` calls)
- `duckduckgo-search` dependency
- Dead code and unused imports

### Fixed
- `sys.stdout.reconfigure(encoding='utf-8')` added for Windows terminal compatibility

---

## [1.0.0] — 2024

### Added
- Initial release: international news digest (geopolitics, economics, science) via DuckDuckGo
- Gemini 1.5 Pro with Flash fallback
- LINE push delivery via LINE Bot SDK v3
