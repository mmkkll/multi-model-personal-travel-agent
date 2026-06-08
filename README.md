# Multi-Model Personal Travel Agent

> AI-powered travel research with real flight prices and transit routing.

A self-hosted travel assistant that combines **5 data sources in parallel** (3 LLMs + Duffel flight API + Google Maps Routes) to plan business and leisure trips, and automatically organizes booking confirmations and speaker invitations into a structured Notion workspace.

> **Two research modes.** The full **n8n multi-model workflow** gives you real flight
> prices (Duffel) and transit routing (Google Maps) alongside 3-LLM synthesis. A newer,
> **lightweight local mode** ([`scrapegraph/`](./scrapegraph/)) does destination research
> and page extraction with a single Gemini key and **no extra infrastructure** — handy
> for quick "what to do / where to eat" research without standing up n8n + Duffel.
> Pick either; they're independent. See [Two research modes](#two-research-modes).

## What it does

### 1. Travel research

Send a natural-language query via Telegram or HTTP webhook:

> "Flights from London to Tokyo on 2026-12-10, return 2026-12-17, business class, 2 passengers"

> "Train from Berlin to Munich on 2026-11-20"

> "Voli da Roma a Barcellona il 15 giugno 2026"  *(any language)*

Get back:
- **Real flight options with prices** from Duffel (300+ airlines including LCC: Ryanair, easyJet, Vueling, Wizz, etc.)
- **Multi-origin fallback**: if no direct flights from your primary airport, the agent searches alternative origins for direct routes (e.g., LHR → LGW → STN → LTN → MAN, or any chain you configure)
- **Transit/train routes** from Google Maps Routes API (intercity rail, subway, bus, light rail)
- **Synthesis from 3 LLMs** (Gemini, Perplexity, OpenAI) — strategic recommendations, hotel/restaurant suggestions, packing advice

### 2. Travel document organizer

Periodically scans Gmail for:
- **Booking confirmations** (flights, trains, hotels, car rentals, restaurants, tours)
- **Indirect signals** of upcoming trips (panel invitations, speaker confirmations, conference programs)

Then:
- Classifies each trip as **work / leisure / ambiguous**
- Matches against existing Notion travel pages (Inspirations / Planning / business-work / Ready to Travel)
- Creates or updates the Notion page with structured sections (✈️ Flights, 🚆 Trains, 🏨 Hotels, 🚗 Car rentals, 🍽️ Restaurants, 🎫 Experiences, 📎 Documents)
- Auto-archives past trips
- Sends 48h pre-trip checklists and 5-7 day advance notices for work trips

## Architecture (high-level)

```
┌─────────────────┐
│ Telegram bot    │◄─── User query
└────────┬────────┘
         │ via Claude Code channels plugin
         ▼
┌─────────────────────────────────────────────────────┐
│ Claude Code session (orchestrator)                  │
│ - Receives Telegram inbound                         │
│ - Calls n8n webhook for travel research             │
│ - Synthesizes response                              │
│ - Replies via Telegram with summary                 │
│ - Saves full result to Notion                       │
└────────┬────────────────────────────────────────────┘
         │ HTTP POST /webhook/travel-agent
         ▼
┌─────────────────────────────────────────────────────┐
│ n8n workflow "travel-agent"                         │
│                                                     │
│  Webhook → Extract Params (gpt-4o-mini, JSON mode)  │
│              ↓                                      │
│       ┌──────┴──────┬────────┬──────────┬───────┐   │
│       ▼             ▼        ▼          ▼       ▼   │
│    Gemini      Perplexity  OpenAI   Duffel   GMaps  │
│   (research) (research) (research) (multi-  (transit│
│                                    origin)   routes)│
│       └──────┬──────┴────────┴──────────┴───────┘   │
│              ▼                                      │
│           Merge (5 inputs)                          │
│              ↓                                      │
│         Format Results                              │
│              ↓                                      │
│         JSON response                               │
└─────────────────────────────────────────────────────┘
```

## Quick start

**Fast path (local mode, ~10 min):** just destination research, one Gemini key, no n8n.

```bash
python3 -m venv ~/.venv-scrapegraph
~/.venv-scrapegraph/bin/pip install -r scrapegraph/requirements.txt
~/.venv-scrapegraph/bin/playwright install chromium
export GEMINI_API_KEY="your-gemini-key"
~/.venv-scrapegraph/bin/python3 scrapegraph/travel-research.py "3 days in Lisbon, what to do" --results 5
```

See [`scrapegraph/README.md`](./scrapegraph/README.md) for the local tools.

**Full path (n8n multi-model, ~90-120 min):** real flight prices + transit + Telegram bot + Notion.

1. Read [`INSTALL.md`](./INSTALL.md) for full setup (Telegram bot, API keys, n8n, Notion).
2. Configure your `.env` from `.env.example`.
3. Import `n8n/travel-agent-workflow.json` into your n8n instance.
4. Activate the Telegram channels plugin in Claude Code.
5. Send a test query to your bot — examples in [`USAGE.md`](./USAGE.md).

## Components

| Component | Purpose | Where |
|---|---|---|
| Claude Code (CLI) | Orchestrator: Telegram bot interface, Notion sync, prompt-driven workflows | https://docs.claude.com/en/docs/claude-code |
| n8n (self-hosted) | Multi-model parallel orchestration of LLMs and APIs | https://n8n.io |
| Telegram Bot API | User interface (chat, voice notes, attachments) | https://core.telegram.org/bots |
| Duffel API | Real flight inventory (300+ airlines including LCC) | https://duffel.com |
| Google Maps Routes API | Transit routing (trains, buses, subways) | https://developers.google.com/maps/documentation/routes |
| OpenAI API | LLM research + JSON parameter extraction | https://platform.openai.com |
| Google Gemini API | LLM research (multi-modal capable) | https://ai.google.dev |
| Perplexity API | LLM research (web-grounded answers) | https://docs.perplexity.ai |
| Notion API | Trip organization workspace | https://developers.notion.com |
| ScrapeGraphAI (local mode) | LLM-driven web research + page extraction, single Gemini key | https://github.com/ScrapeGraphAI/Scrapegraph-ai |
| Open-Meteo (weather) | Free trip weather forecast / climatology, no API key | https://open-meteo.com |

## Two research modes

The two modes are fully independent — set up whichever fits.

| | **n8n multi-model** (full) | **Local mode** ([`scrapegraph/`](./scrapegraph/)) |
|---|---|---|
| Flight prices | ✅ Duffel (real, 300+ airlines) | ❌ |
| Transit routing | ✅ Google Maps Routes | ❌ |
| LLM synthesis | 3 LLMs in parallel (Gemini + Perplexity + OpenAI) | 1 LLM (Gemini) over scraped web results |
| Destination research | ✅ | ✅ (DuckDuckGo search → scrape + merge) |
| Hotel / article extraction | — | ✅ markup-agnostic |
| Infra needed | n8n + 5 API keys | just a Python venv + 1 Gemini key |
| Best for | full trip planning with prices | quick research, no infra |

Start with local mode if you just want fast destination research; add the n8n
workflow when you need real flight prices and transit routes. Setup for each:
[`scrapegraph/README.md`](./scrapegraph/README.md) and [`INSTALL.md`](./INSTALL.md).

## Repository layout

```
.
├── n8n/                  # multi-model workflow (import into n8n)
├── scrapegraph/          # lightweight local research tools (Python + Gemini)
├── weather/              # Open-Meteo forecast helper (Node, no key)
├── notion/               # Notion workspace structure + content templates
├── telegram-bot/         # bot setup + access allowlist example
├── travel-organizer/     # Gmail→Notion organizer prompt + notes
├── tests/                # curl examples + expected outputs
└── *.md                  # README, INSTALL, USAGE, ARCHITECTURE, TROUBLESHOOTING, CHANGELOG
```

## Cost estimate (personal use, ~50 queries/month)

| Service | Volume | Cost |
|---|---|---|
| Duffel (search-only, no bookings via API) | 250 searches | ~$0.50/month |
| Google Maps Routes | 50 transit queries | $0 (free tier $200/mo, ~10k requests free) |
| OpenAI gpt-4o-mini (Extract Params) | 50 calls | ~$0.10/month |
| OpenAI gpt-4o (research) | 50 calls × 2k tokens | ~$1/month |
| Gemini Flash | 50 calls | $0 (free tier) |
| Perplexity sonar | 50 calls | ~$0.50/month |
| Notion API | unlimited | $0 |
| Telegram Bot API | unlimited | $0 |
| **Total (n8n mode)** | | **~$2-3/month** |

Local mode is cheaper still: Gemini Flash-Lite free tier + Open-Meteo (no key) →
effectively **$0/month** for personal-volume research.

## License

MIT. See [LICENSE](./LICENSE).

## Status

⚠️ Pre-1.0 / personal-use grade. Production deployments should:
- Add error handling around webhook timeouts (n8n LLM calls can take 30-60s)
- Implement search rate-limiting (Duffel has search:book ratio constraints)
- Add observability (Prometheus/OpenTelemetry hooks for n8n)
- Consider OAuth flow for shared Notion workspaces

PRs welcome.

## Customization

The shipped workflow includes a default fallback chain `FLR, BLQ, PSA, FCO, LIN` (sample regional cluster). Customize for your region:

- **UK**: `LHR, LGW, STN, LTN, MAN`
- **US East Coast**: `JFK, LGA, EWR, BWI, BOS`
- **DACH**: `FRA, MUC, ZRH, VIE, BER`
- **Iberia**: `MAD, BCN, LIS, OPO, AGP`

Edit the prompt in the `Extract Params` node (n8n UI). The Code node `Duffel Flights` also has a `FALLBACK_CHAIN` constant — update it to match.

See [`USAGE.md`](./USAGE.md) for more customization patterns (custom LLM prompts, adding a 4th model, hotel search, etc.).
