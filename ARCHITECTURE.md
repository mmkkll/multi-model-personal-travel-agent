# Architecture

## Component matrix

| Component | Role | Process | Persistence |
|---|---|---|---|
| Telegram Bot API | User interface | external | none (24h queue) |
| Claude Code (CLI) | Orchestrator + Notion writer | local daemon | session logs |
| Telegram channels plugin (bun) | Bot polling + MCP bridge | child of claude --channels | `~/.claude/channels/telegram/` |
| n8n | Multi-model parallel research | local daemon (port 5678) | SQLite DB |
| Duffel API | Flight search | external HTTP | none |
| Google Maps Routes API | Transit routing | external HTTP | none |
| OpenAI / Gemini / Perplexity | Research LLMs | external HTTP | none |
| Notion API | Trip organization | external HTTP | Notion workspace |

## End-to-end flow — travel research query

```
┌──────────┐  text/voice    ┌─────────────────┐
│  User    │─────────────▶  │ Telegram server │
│ (mobile) │                └────────┬────────┘
└──────────┘                          │ getUpdates long-poll
                                      ▼
                         ┌────────────────────────────┐
                         │ bun server.ts              │
                         │ (Telegram channels plugin) │
                         └────────────┬───────────────┘
                                      │ MCP notifications/claude/channel
                                      ▼
                         ┌────────────────────────────┐
                         │ claude --channels session  │
                         │  • parses query intent     │
                         │  • calls n8n webhook       │
                         │  • formats Telegram reply  │
                         │  • creates Notion page     │
                         └────┬───────────────────┬───┘
                              │ HTTP POST         │ Notion API
                              ▼                   ▼
                  ┌──────────────────────┐  ┌──────────────┐
                  │ n8n webhook          │  │ Notion DB    │
                  │ /webhook/travel-     │  │ Travel pages │
                  │ agent                │  └──────────────┘
                  └──────────┬───────────┘
                             │
              ┌──────────────┴───────────────────────────┐
              │ Extract Params (OpenAI gpt-4o-mini, JSON)│
              │ → {origin_iata, destination_iata, dates} │
              └──────────────┬───────────────────────────┘
                             │
        ┌────────┬────────┬──┴──┬───────────┬──────────┐
        ▼        ▼        ▼     ▼           ▼          ▼
     Gemini  Perplex  OpenAI  Duffel     GMaps    (parallel)
                              multi-     Transit
                              origin     Routes
        │        │        │     │           │
        └────────┴────────┴─────┴───────────┘
                             │
                       Merge (5 inputs)
                             │
                       Format Results
                             │
                       JSON response ◀──── back to claude session
```

## Multi-model parallel design

The n8n workflow runs five independent HTTP nodes in parallel after the Extract Params step. This:

1. **Maximizes diversity** — each model has different training data, so consensus across 3+ sources is strong signal.
2. **Bounds latency** — total wall time = max(individual latencies), not sum. Typically 30-60s.
3. **Enables fallback** — if one source fails (`onError: continueRegularOutput` on every HTTP node), the others still produce useful output.
4. **Combines deterministic + probabilistic** — Duffel and GMaps return structured factual data; LLMs add strategic recommendations.

## Multi-origin fallback (Duffel)

The Duffel node is implemented as an n8n **Code node** (not HTTP) because it needs to loop through multiple origins:

```
primary origin from Extract Params (e.g., FLR)
    ↓
fallback chain: [primary, FLR, BLQ, PSA, FCO, LIN] (deduped)
    ↓
for each origin:
    POST /air/offer_requests
    filter offers where stops == 0 (direct flights only)
    keep top 5 by price
    ↓
output: {
  byOrigin: { FLR: {direct, any}, BLQ: {...}, ... },
  primary: "FLR",
  recommendedOrigin: "FCO",        // first in fallback with direct flights
  usedFallback: true,
  note: "No direct from FLR, fallback to FCO"
}
```

This handles the common case where a user's primary airport has no direct flights to a small destination — the agent automatically suggests nearby airports that do.

## Travel Document Organizer flow

A separate, periodic prompt-driven task (run every ~2 hours via cron):

```
┌─────────────────────────────────────────────────┐
│ Cron trigger (every 2h, e.g., :37 minute)        │
└────────────────────┬────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────┐
│ Search Gmail (last 3h):                         │
│   1. Booking confirmations (subject + sender)    │
│   2. Speaker/panel/conference invitations        │
└────────────────────┬────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────┐
│ For each email:                                 │
│   - Read full content                           │
│   - Classify: booking | signal-work |           │
│     signal-leisure | signal-ambiguous          │
│   - Extract: dates, destination, role,          │
│     organizer, contacts                         │
└────────────────────┬────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────┐
│ Match against Notion Travel pages:              │
│   - Inspirations / Planning / business-work /   │
│     Ready to Travel                             │
│   - Match by destination + date window ±3 days  │
└────────────────────┬────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────┐
│ Update Notion:                                  │
│   - Existing match: append details               │
│   - New booking: create in Planning              │
│   - New signal-work: create in business-work    │
│   - Ambiguous: ask user via Telegram, wait      │
└────────────────────┬────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────┐
│ Periodic housekeeping:                          │
│   - 48h pre-trip checklist (Planning)           │
│   - Auto-move on departure day                   │
│   - 5-7d advance notice for work trips          │
│   - Auto-archive past trips → Past trips         │
└─────────────────────────────────────────────────┘
```

See [`travel-organizer/`](./travel-organizer/) for the full prompt and operational notes.

## Storage / state

| Where | What | Backup recommendation |
|---|---|---|
| Notion | All trip data (the source of truth) | Notion's own version history + periodic export |
| `~/.n8n/database.sqlite` | Workflow definitions + execution history | Backup before any DB edits (see TROUBLESHOOTING.md) |
| `~/.claude/channels/telegram/access.json` | Allowlist | Keep in sync if you change devices |
| `.env` (your machine) | API keys | Store in password manager, never commit |

## Security notes

- All API keys live in `.env` or system environment — never in workflow JSON or git.
- Telegram bot's `access.json` enforces per-chat-id allowlist (DM policy). Anyone outside the allowlist is silently dropped.
- Duffel token: search-only is sufficient functionally, but Duffel's permission model requires `air.offer_requests.create` (a write scope). The workflow only calls search; never `/orders` or `/payments`.
- n8n self-hosted runs on `localhost:5678` by default — do NOT expose to the public internet without auth (n8n has built-in basic auth + JWT). For remote access use a tunnel (Tailscale, Cloudflare Tunnel, or SSH).

## Observability

Built-in:
- n8n: Executions tab shows full per-node input/output for every workflow run.
- Claude Code: `~/.claude/projects/<workspace>/<session>.jsonl` records the full conversation log including tool calls.
- Bun (Telegram plugin): polling logs at `process.stderr` if you redirect (see [`TROUBLESHOOTING.md`](./TROUBLESHOOTING.md) on capturing bun stderr).

Recommended additions for production:
- Prometheus exporter for n8n: https://docs.n8n.io/hosting/configuration/configuration-methods/
- OpenTelemetry hooks
- Structured logging (JSON) for Claude Code session logs
