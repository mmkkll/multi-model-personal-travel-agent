# Multi-Model Personal Travel Agent

> AI-powered travel research with real flight prices and transit routing.

A self-hosted travel assistant that combines **5 data sources in parallel** (3 LLMs + Duffel flight API + Google Maps Routes) to plan business and leisure trips, and automatically organizes booking confirmations and speaker invitations into a structured Notion workspace.

## What it does

### 1. Travel research

Send a natural-language query via Telegram or HTTP webhook:

> "Voli e treni da Firenze a Lausanne 19 maggio 2026, business, 1 passeggero"

Get back:
- **Real flight options with prices** from Duffel (300+ airlines including LCC: Ryanair, Vueling, easyJet, etc.)
- **Multi-origin fallback**: if no direct flights from your primary airport, the agent searches alternative origins (e.g., FLR → BLQ → PSA → FCO → LIN) for direct routes
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

1. Read [`INSTALL.md`](./INSTALL.md) for full setup (Telegram bot, API keys, n8n, Notion).
2. Configure your `.env` from `.env.example`.
3. Import `n8n/travel-agent-workflow.json` into your n8n instance.
4. Activate the Telegram channels plugin in Claude Code.
5. Send a test query to your bot: "Voli Firenze Roma 10 giugno 2026".

## Components

| Component | Purpose | Where |
|---|---|---|
| Claude Code (CLI) | Orchestrator: Telegram bot interface, Notion sync, prompt-driven workflows | https://docs.claude.com/en/docs/claude-code |
| n8n (self-hosted) | Multi-model parallel orchestration of LLMs and APIs | https://n8n.io |
| Telegram Bot API | User interface (chat, voice notes, attachments) | https://core.telegram.org/bots |
| Duffel API | Real flight inventory (300+ airlines) | https://duffel.com |
| Google Maps Routes API | Transit routing (trains, buses, subways) | https://developers.google.com/maps/documentation/routes |
| OpenAI API | LLM research + JSON parameter extraction | https://platform.openai.com |
| Google Gemini API | LLM research (Star Alliance hub awareness) | https://ai.google.dev |
| Perplexity API | LLM research (web-grounded answers) | https://docs.perplexity.ai |
| Notion API | Trip organization workspace | https://developers.notion.com |

## Cost estimate (personal use, ~20 trips/month)

| Service | Volume | Cost |
|---|---|---|
| Duffel (search-only, no bookings) | 100 searches | ~$0.50/month |
| Google Maps Routes | 20 transit queries | $0 (free tier $200/mo) |
| OpenAI gpt-4o-mini (Extract Params) | 20 calls | ~$0.10/month |
| OpenAI gpt-4o (research) | 20 calls × 2k tokens | ~$0.40/month |
| Gemini 2.5 Flash | 20 calls | $0 (free tier) |
| Perplexity sonar | 20 calls | ~$0.20/month |
| Notion API | unlimited | $0 |
| Telegram Bot API | unlimited | $0 |
| **Total** | | **~$1-2/month** |

## License

MIT. See [LICENSE](./LICENSE).

## Status

⚠️ Pre-1.0 / personal-use grade. Production deployments should:
- Add error handling around webhook timeouts (n8n LLM calls can take 30-60s)
- Implement search rate-limiting (Duffel has search:book ratio constraints)
- Add observability (Prometheus/OpenTelemetry hooks for n8n)
- Consider OAuth flow for shared Notion workspaces

PRs welcome.
