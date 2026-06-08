# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [1.1.0] — 2026-06-08

### Added
- **Local research mode** ([`scrapegraph/`](./scrapegraph/)) — a lightweight alternative
  to the full n8n multi-model workflow, using [ScrapeGraphAI](https://github.com/ScrapeGraphAI/Scrapegraph-ai)
  (MIT) with a single Gemini key and no extra infrastructure:
  - `travel-research.py` — DuckDuckGo web search → scrape + merge top-N results
    (`SmartScraperMultiGraph`) → structured destination research (places, activities,
    costs, tips, with sources).
  - `hotel-scraper-sg.py` — markup-agnostic hotel extractor (name/price/rating/address)
    that survives layout changes, for any hotel/booking page.
  - `article-extract-sg.py` — robust article extraction (title/author/date/summary/key
    points); `--subject` returns a visual subject seed for an image generator.
  - `scrapegraph_lib.py` — shared Gemini key + graph config; reads `GEMINI_API_KEY` from
    env or `.env`, model override via `SCRAPEGRAPH_MODEL`.
  - `requirements.txt` + setup notes for a dedicated virtualenv.
- **Weather helper** ([`weather/weather-forecast.mjs`](./weather/)) — free Open-Meteo
  forecast (≤16 days) / climatology (>16 days), no API key. Adapt activities to weather
  and add packing hints.
- README **"Two research modes"** comparison + repository layout; INSTALL section for the
  local venv; USAGE + TROUBLESHOOTING entries for the new tools.

### Notes
- The two modes are independent: local mode for quick, infra-free research; the n8n
  workflow when you need real flight prices (Duffel) and transit routing (Google Maps).
- `travel-research.py` deliberately does **not** use ScrapeGraphAI's `SearchGraph`
  (in 1.x it hardcodes a Google search that gets blocked and ignores the override); the
  DuckDuckGo search is run directly and the URLs scraped with `SmartScraperMultiGraph`.

## [1.0.1] — 2026-05-01

### Changed
- **Booking detection whitelist extended** in `travel-organizer/organizer-prompt.md` — Gmail search query now matches more car-rental brands and Italian receipt subjects. Added to subject keywords: `voucher`, `autonoleggio`. Added to from-list: `drivalia`, `budget`, `alamo`, `enterprise`, `thrifty`, `dollar` (joining the existing `hertz`, `europcar`, `avis`, `centauro`, `goldcar`, `firefly`, `sixt`).

### Reasoning
- Real-world miss: a Centauro "Voucher di conferma della prenotazione …" email did not match the prior subject filter because the keyword `voucher` was missing. Whitelist hardened based on observed misses.
- The Italian word "autonoleggio" (car rental) is common in Italian booking flows and was missing.
- Drivalia (Italian car rental brand, ex Goldcar/Locauto group) and the Big-5 US chains (Budget, Alamo, Enterprise, Thrifty, Dollar) are common enough on international trips to warrant inclusion.

## [1.0.0] — 2026-04-29

### Added
- Initial release: Multi-Model Personal Travel Agent.
- Self-hosted travel research that combines Gemini, Perplexity, OpenAI, Duffel multi-origin flight search, and Google Maps Routes (transit) — all in parallel, in a single n8n workflow.
- Telegram bot interface (long-polling, no webhook → no 60s response constraint).
- Travel Document Organizer: cron prompt that scans Gmail for booking confirmations and speaker invitations, classifies trips work vs leisure, files them into a Notion workspace (Inspirations → Planning → Business/Work → Past trips).
- MIT licensed.
