# BIM Daily Intelligence Bot

![GitHub Actions](https://github.com/KillerFish5566/Serverless-RAG-Agent-POC/actions/workflows/daily_news.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.12%2B-blue)
![Gemini](https://img.shields.io/badge/AI-Google_Gemini_2.0-orange)
![License](https://img.shields.io/badge/License-MIT-green)

A serverless bot that collects BIM industry news daily, summarizes it with Google Gemini, and delivers a digest to LINE — automatically, at no infrastructure cost.

---

## Features

- **Zero-cost infrastructure** — runs entirely on GitHub Actions; no server to manage
- **Domain-weighted coverage** — prioritizes BIM × AI news, followed by BIM-MEP and general BIM
- **7-day freshness filter** — dual-layer date check ensures only recent articles are included
- **Automatic model fallback** — switches to a backup Gemini model if the primary hits rate limits
- **Failure alerts** — sends a LINE notification if the daily run fails

---

## How It Works

```
GitHub Actions (daily cron: UTC 22:30 = Taiwan 06:30)
        │
        ▼
Google News RSS ──► BIM × AI    (fetch 6) ┐
                    BIM-MEP     (fetch 4) ├─► Gemini 2.0 Flash ──► LINE Push
                    BIM General (fetch 3) ┘   (selects top 6 for digest)
```

### News Categories

| Category | Fetched | Displayed | Focus |
| :--- | :---: | :---: | :--- |
| **BIM × AI** | 6 | 3 | AI/ML applied to BIM, generative AI in AEC |
| **BIM-MEP** | 4 | 2 | MEP coordination, clash detection, M&E BIM |
| **BIM General** | 3 | 1 | OpenBIM, IFC, general BIM adoption |

---

## Tech Stack

| Component | Technology |
| :--- | :--- |
| Runtime | Python 3.12+ |
| AI Model | Google Gemini 2.0 Flash (primary), gemini-flash-latest (fallback) |
| News Source | Google News RSS |
| Orchestration | GitHub Actions (Ubuntu, serverless cron) |
| Messaging | LINE Messaging API |
| Secrets | GitHub Actions Secrets + `python-dotenv` for local dev |

---

## Setup

### 1. Clone & install

```bash
git clone https://github.com/KillerFish5566/Serverless-RAG-Agent-POC.git
cd Serverless-RAG-Agent-POC
pip install -r requirements.txt
```

### 2. Configure environment variables

Copy the template and fill in your credentials:

```bash
cp .env.example .env
```

| Variable | Where to get it |
| :--- | :--- |
| `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/app/apikey) |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Developers Console → Messaging API → Channel access token (long-lived) |
| `LINE_USER_ID` | Your personal LINE UID — starts with `U`, 33 characters |

For GitHub Actions, add the same three values under **Settings → Secrets and variables → Actions**.

### 3. Run locally

```bash
python main.py
```

### 4. Trigger manually on GitHub

Go to **Actions → Daily BIM Bot → Run workflow**.

---

## Configuration

All tunable parameters are grouped at the top of [`main.py`](main.py):

| Constant | Default | Description |
| :--- | :---: | :--- |
| `NEWS_FILTER_DAYS` | `7` | Only include articles published within this many days |
| `REQUEST_TIMEOUT` | `15` | Timeout in seconds for Google News RSS requests |
| `LINE_TIMEOUT` | `30` | Timeout in seconds for LINE API requests |
| `LLM_TEMPERATURE` | `0.75` | Gemini creativity (0 = precise, 1 = creative) |
| `CANDIDATE_MODELS` | see file | Gemini model priority list for automatic fallback |
| `NEWS_TOPICS` | see file | Search queries and fetch limits per category |

---

## Utilities

| Script | Purpose |
| :--- | :--- |
| `check_models.py` | List all Gemini models available for your API key |
| `test_line.py` | Diagnose LINE token validity and push connectivity |

> **Note:** `test_line.py` sends a real LINE message each time it runs and counts against your monthly quota (200 messages on the free plan). Run it only when diagnosing a connection issue.

---

## Known Limitations

- **LINE free plan:** limited to 200 push messages per month. Each daily run uses 1 message (plus 1 if a failure alert fires).
- **Gemini free tier:** subject to rate limits. The bot will automatically fall back to `gemini-flash-latest` if `gemini-2.0-flash` is exhausted.
- **Google News RSS:** no official API contract — query syntax and result format may change without notice.
- **Article links:** generated as Google `site:` search URLs rather than direct links, because Google News redirect URLs expire.

---

## Changelog

For the full version history, see [CHANGELOG.md](CHANGELOG.md).

---

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.
