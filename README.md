# BIM Daily Intelligence Bot

![Status](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Gemini](https://img.shields.io/badge/AI-Google_Gemini_2.0-orange)
![License](https://img.shields.io/badge/License-MIT-green)

> **Enterprise Scenario Simulation:** A Serverless CI/CD pipeline that aggregates BIM industry news daily, summarizes it with an LLM, and delivers it straight to LINE — with a gyaru twist.

## 📖 Executive Summary

This project is a **Proof of Concept (POC)** for a lightweight, serverless **AI-Powered News Digest Bot**, focused on the Building Information Modeling (BIM) domain.

It runs entirely on **GitHub Actions** at 06:30 AM (Taiwan time) every day, scrapes BIM-related news from Google News RSS, generates a personality-driven summary via Google Gemini, and pushes it to LINE.

### 🎯 Value Proposition

- **Zero-Cost Infrastructure** — runs fully on GitHub Actions with no server to maintain
- **Fault Tolerance** — automatic model fallback handles API rate limits and outages
- **Domain-Focused** — coverage weighted toward BIM × AI, then BIM-MEP, then general BIM
- **Personality-Driven Output** — summaries written in a direct, opinionated gyaru tone rather than sterile AI prose

---

## 🏗️ Architecture & Engineering Decisions

### 🛠 Tech Stack

| Component | Technology | Details |
| :--- | :--- | :--- |
| **Core Runtime** | Python | 3.10+ |
| **AI Model** | Google Gemini | 2.0 Flash (primary), gemini-flash-latest (fallback) |
| **SDK** | Google GenAI SDK | `google-genai` official Python client |
| **News Source** | Google News RSS | No API key required; reliable on cloud runners |
| **Orchestration** | GitHub Actions | Ubuntu-latest, serverless cron job |
| **Messaging** | LINE Messaging API | RESTful push via `requests` |
| **Secrets** | GitHub Secrets + dotenv | `python-dotenv` for local dev |

### ⚙️ Data Flow

```
GitHub Actions (daily cron: UTC 22:30 = TW 06:30)
        │
        ▼
Google News RSS ──► scrape BIM × AI (6)  ┐
                    BIM-MEP        (4)  ├─► Gemini 2.0 Flash ──► LINE Push
                    BIM General    (3)  ┘   (selects top 6 for digest)
```

### 📰 News Coverage & Weights

| Category | Weight | Fetched | Displayed | Focus |
| :--- | :---: | :---: | :---: | :--- |
| **BIM × AI** | ⭐⭐⭐ | 6 | 3 | AI/ML applied to BIM, generative AI in AEC |
| **BIM-MEP** | ⭐⭐ | 4 | 2 | MEP coordination, clash detection, M&E BIM |
| **BIM General** | ⭐ | 3 | 1 | OpenBIM, IFC, general BIM adoption |

---

## 🚀 Setup

### 1. Clone & Install

```bash
git clone <your-repo-url>
cd <repo-folder>
pip install -r requirements.txt
```

### 2. Configure Secrets

Copy `.env` and fill in your keys:

```
GEMINI_API_KEY=          # Google AI Studio: https://aistudio.google.com/app/apikey
LINE_CHANNEL_ACCESS_TOKEN=   # LINE Developers Console > Messaging API > Channel access token
LINE_USER_ID=            # Your personal LINE UID (starts with U, 33 chars)
```

For GitHub Actions, add the same three values under **Settings → Secrets and variables → Actions**.

### 3. Run Locally

```bash
python main.py
```

### 4. Trigger Manually on GitHub

Go to **Actions → Daily BIM Bot → Run workflow**.

---

## 🔧 Utilities

| Script | Purpose |
| :--- | :--- |
| `check_models.py` | List all Gemini models available for your API key |
| `test_line.py` | Diagnose LINE token validity and push connectivity |

---

## 📋 Changelog

### v2.2.0 — 2026-04-30
- Added dual-layer date filtering to prevent stale articles in the digest
  - Layer 1: `when:7d` appended to all Google News RSS queries (filters at source)
  - Layer 2: `pubDate` parsing on each RSS item — articles older than 7 days are skipped
- `search_news()` now accepts a `days` parameter (default: 7) for easy tuning
- Log output now shows filtered article count per topic (e.g. `取得 5 則（過濾掉 2 則舊文章）`)

### v2.1.0 — 2026-04-28
- Reduced daily digest from 7 articles to 6 (BIM × AI: 3, BIM-MEP: 2, BIM General: 1)
- Increased RSS fetch pool to give Gemini more candidates to choose from: BIM × AI (6), BIM-MEP (4), BIM General (3)
- Simplified source line in digest: removed article title, now shows `📰 Source Name` only
- Switched article links from long Google News redirect URLs to Google `site:` search URLs — shorter, always clickable in LINE, and reliably surface the correct article
- Removed Markdown link formatting from output (LINE does not render Markdown; bare URLs auto-become clickable)

### v2.0.0 — 2026-04-28
- **Breaking:** Replaced DuckDuckGo search with Google News RSS (fixes silent failures on GitHub Actions runners where DuckDuckGo IPs are blocked)
- **Breaking:** News domain changed from international geopolitics/science to BIM industry coverage
- Added weighted topic distribution: BIM × AI (5) > BIM-MEP (3) > BIM General (2)
- Updated Gemini models: `gemini-1.5-pro-002` (deprecated) → `gemini-2.0-flash`; fallback updated to `gemini-flash-latest`
- Rewrote LLM prompt: gyaru-style personality, personal commentary, no boilerplate AI tone
- Raised generation temperature from 0.3 → 0.75 for more natural output
- Removed unused `line-bot-sdk` and `duckduckgo-search` dependencies
- Removed dead code and cleaned up unused imports
- Added `test_line.py` diagnostic utility
- Fixed `sys.stdout.reconfigure(encoding='utf-8')` for Windows compatibility

### v1.0.0 — 2024-xx-xx
- Initial release: international news (geopolitics, economics, science) via DuckDuckGo
- Gemini 1.5 Pro with Flash fallback
- LINE push via LINE Bot SDK v3
