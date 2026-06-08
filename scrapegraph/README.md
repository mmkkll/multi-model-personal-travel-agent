# ScrapeGraphAI local research tools

A lightweight, local alternative to the full n8n multi-model workflow. These tools
do LLM-driven web research and extraction with a **single Gemini key** and **no extra
infrastructure** (no n8n, no Duffel, no Perplexity).

Use them when you want quick destination/activity research or robust page extraction
without standing up the full stack. For **real flight prices and transit routing**,
use the n8n workflow (see the [root README](../README.md)).

| Tool | What it does |
|---|---|
| `travel-research.py` | Web search (DuckDuckGo) → scrape + merge top-N results → structured travel research (places, activities, costs, tips, with sources). |
| `hotel-scraper-sg.py` | Resilient hotel extractor — name/price/rating/address from any hotel/booking page, markup-agnostic. |
| `article-extract-sg.py` | Robust article extraction (title/author/date/summary/key points); `--subject` returns a visual subject seed for an image generator. |
| `scrapegraph_lib.py` | Shared config (Gemini key loading + graph config). Not a CLI. |

## Why ScrapeGraphAI

[ScrapeGraphAI](https://github.com/ScrapeGraphAI/Scrapegraph-ai) (MIT) is LLM-driven
scraping: it fetches a page (optionally with a headless browser), feeds the content
to an LLM, and returns a **structured dict**. Because the LLM does the extraction,
the tools survive layout changes that would break CSS/regex scrapers.

## Setup

These tools have heavy dependencies (langchain + playwright). Install them in a
**dedicated virtualenv** so they don't pollute the rest of your environment:

```bash
python3 -m venv ~/.venv-scrapegraph
~/.venv-scrapegraph/bin/pip install -r scrapegraph/requirements.txt
~/.venv-scrapegraph/bin/playwright install chromium
```

Set your Gemini key (free tier is enough for personal use):

```bash
export GEMINI_API_KEY="your-gemini-key"   # or put GEMINI_API_KEY= in the repo .env
```

Get a key at https://aistudio.google.com/apikey. Optionally override the model with
`SCRAPEGRAPH_MODEL` (default `google_genai/gemini-2.5-flash-lite`).

## Usage

```bash
VENV=~/.venv-scrapegraph/bin/python3

# Destination research
$VENV scrapegraph/travel-research.py "3 days in Lisbon, what to do and where to eat" --results 5

# Hotel extraction from a booking page
$VENV scrapegraph/hotel-scraper-sg.py --url "https://www.booking.com/hotel/it/example.html" --json

# Article extraction (+ visual subject seed)
$VENV scrapegraph/article-extract-sg.py "https://example.com/destination-guide"
$VENV scrapegraph/article-extract-sg.py "https://example.com/destination-guide" --subject
```

All three also expose importable functions (`research`, `extract_hotel`,
`extract_article` / `extract_subject`) — see each file's docstring.

## Known limitations

- **SearchGraph is not used.** In scrapegraphai 1.x the built-in `SearchGraph`
  hardcodes Google as the search engine (which gets blocked) and does not pass the
  override to its nodes. `travel-research.py` runs the DuckDuckGo search itself and
  scrapes the resulting URLs with `SmartScraperMultiGraph`.
- **Anti-bot / JS-heavy pages** (e.g. Google Hotels, some airline SPAs) may return
  empty in headless mode. These tools shine on content-in-HTML pages (most hotel,
  booking, blog, news, and guide pages).
- **Python version**: scrapegraphai 1.x works on Python 3.9+. For 2.x you need 3.10+.
