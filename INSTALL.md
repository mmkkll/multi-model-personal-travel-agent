# Installation Guide

Step-by-step setup for the Multi-Model Personal Travel Agent. Plan ~60-90 minutes for first-time setup.

## Prerequisites

- macOS, Linux, or WSL (Windows Subsystem for Linux)
- Node.js 20+
- Bun (for the Telegram channels plugin) — `curl -fsSL https://bun.sh/install | bash`
- A Telegram account
- A Notion account
- A credit card for: Duffel, Google Cloud (Routes API), OpenAI

---

## Step 1 — Telegram Bot

1. In Telegram, open chat with `@BotFather`.
2. Send `/newbot`, follow prompts to create your bot. Choose a unique username ending in `bot` (e.g., `mybot_personal_travel_bot`).
3. BotFather replies with your bot's API token. Save it as `TELEGRAM_BOT_TOKEN` in `.env`.
4. Send a message to your new bot from your personal Telegram account (any text).
5. Visit `https://api.telegram.org/bot<TOKEN>/getUpdates` in a browser. Find `"chat":{"id":<NUMBER>}` — that's your `TELEGRAM_CHAT_ID`. Save it.

---

## Step 2 — n8n self-hosted

```bash
# Install globally via npm
npm install -g n8n@latest

# Run on port 5678 (default)
n8n start
```

n8n UI opens at `http://localhost:5678`. Create the owner account on first launch.

For production / always-on, run n8n as a daemon:

**macOS** (launchd) — create `~/Library/LaunchAgents/com.local.n8n.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.local.n8n</string>
  <key>ProgramArguments</key>
  <array>
    <string>/opt/homebrew/bin/n8n</string>
    <string>start</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>/tmp/n8n.log</string>
  <key>StandardErrorPath</key><string>/tmp/n8n-err.log</string>
</dict>
</plist>
```

Load with `launchctl load ~/Library/LaunchAgents/com.local.n8n.plist`.

**Linux** (systemd): create `/etc/systemd/system/n8n.service` similarly.

---

## Step 3 — API keys

### Duffel (flight search)

1. Sign up at https://app.duffel.com/join.
2. Verify your business account (KYC, ~5 min).
3. Settings → API access tokens → Create token → **Live mode**, **Read & Write** scope.
4. Copy the `duffel_live_...` token to `DUFFEL_API_KEY`.

> **Permission caveat**: `POST /air/offer_requests` requires `air.offer_requests.create` permission. A "Read-only" token will fail with `insufficient_permissions`. Use Read & Write — even though we never book through the API, the search endpoint is technically a write operation.

> **Test mode**: tokens prefixed `duffel_test_` work with stub data ("Duffel Airways" fake carrier, capped slots). Useful for dev but not production.

### Google Maps Routes

1. Visit https://console.cloud.google.com.
2. Create a new project (or select existing).
3. APIs & Services → Library → search "Routes API" → Enable.
4. Credentials → Create Credentials → API Key.
5. (Recommended) Restrict the key: API restrictions = "Routes API".
6. Copy to `GOOGLE_MAPS_API_KEY`.

Free tier: $200/month covers ~40,000 Routes API requests.

### OpenAI

1. https://platform.openai.com/api-keys → Create new secret key.
2. Copy to `OPENAI_API_KEY`.

The workflow uses two OpenAI calls per query:
- `gpt-4o-mini` for parameter extraction (~$0.0001/call)
- `gpt-4o` for travel research (~$0.01-0.02/call)

### Google Gemini

1. https://aistudio.google.com/apikey → Create API key.
2. Copy to `GEMINI_API_KEY`.

Free tier covers personal use (15 RPM).

### Perplexity

1. https://www.perplexity.ai/settings/api → Generate API key.
2. Copy to `PERPLEXITY_API_KEY`.

---

## Step 4 — Notion workspace

### Create the integration

1. https://www.notion.so/my-integrations → New integration.
2. Name it (e.g., "Travel Agent").
3. Capabilities: Read content, Update content, Insert content.
4. Copy the **Internal Integration Token** to `NOTION_API_TOKEN`.

### Create the Travel structure

In your Notion workspace, create a parent page "Travel" with these sub-pages:

```
Travel/
├── 🌟 Inspirations              (exploratory ideas)
├── 📋 Planning                   (confirmed bookings being assembled)
├── ✈️ business/work              (confirmed work trips: speeches, panels, conferences)
├── 🧳 Ready to Travel            (personal trips, ready to depart)
└── 📦 Past trips                 (archive after return)
```

Right-click each page → "Connect to integration" → select your Travel Agent integration.

### Get page IDs

For each page, copy its URL and extract the 32-character ID (the last segment, with or without dashes):
```
https://www.notion.so/Inspirations-31ac93b9555e81068bcac0b5c4798b1a
                                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                    that's the page ID
```

Save IDs to `.env`:
```
NOTION_TRAVEL_INSPIRATIONS_ID=31ac93b9555e81068bcac0b5c4798b1a
NOTION_TRAVEL_PLANNING_ID=...
NOTION_TRAVEL_BUSINESS_WORK_ID=...
NOTION_TRAVEL_READY_ID=...
NOTION_TRAVEL_PAST_TRIPS_ID=...
```

See [`notion/travel-structure.md`](./notion/travel-structure.md) for the full content template per page.

---

## Step 5 — Import n8n workflow

1. Open n8n UI at `http://localhost:5678`.
2. Top-right ⋮ → "Import from File" → select `n8n/travel-agent-workflow.json`.
3. Open the imported workflow. **Set environment variables** in n8n:
   - Settings (gear icon, top-right) → Variables (or use n8n's `Environments`)
   - For each `{{ $env.XXX }}` placeholder in HTTP nodes, set the corresponding env var.
   - Alternative: pass them as system environment when starting n8n.
4. Click "Active" toggle (top-right) to enable the webhook.
5. Test with curl:
   ```bash
   curl -X POST "http://localhost:5678/webhook/travel-agent" \
     -H "Content-Type: application/json" \
     -d '{"query":"Voli Firenze Roma 10 giugno 2026"}'
   ```
   Expect a JSON with keys `gemini`, `perplexity`, `openai`, `duffel`, `gmaps`.

---

## Step 6 — Claude Code with Telegram channels plugin

1. Install Claude Code: https://docs.claude.com/en/docs/claude-code (`curl -fsSL claude.ai/install.sh | bash`).
2. Install the Telegram channels plugin from the official marketplace:
   ```bash
   claude plugin marketplace add anthropics/claude-plugins-official
   claude plugin install telegram@claude-plugins-official
   ```
3. Configure the bot token: edit `~/.claude/channels/telegram/.env`:
   ```
   TELEGRAM_BOT_TOKEN=<your token>
   ```
4. Configure the allowlist: edit `~/.claude/channels/telegram/access.json`:
   ```json
   {
     "dmPolicy": "allowlist",
     "allowFrom": ["<YOUR_TELEGRAM_CHAT_ID>"],
     "groups": {},
     "pending": {}
   }
   ```
5. Enable the plugin in your project's `.claude/settings.json`:
   ```json
   {
     "enabledPlugins": {
       "telegram@claude-plugins-official": true
     }
   }
   ```
6. Start a Claude Code session listening for Telegram inbound:
   ```bash
   claude --channels "plugin:telegram@claude-plugins-official" --dangerously-skip-permissions
   ```

   For an always-on background session, see [`telegram-bot/setup.md`](./telegram-bot/setup.md).

7. Send a Telegram message to your bot — Claude should respond.

---

## Step 7 — Test end-to-end

From Telegram, send:
> "Voli e treni da Firenze a Lausanne 19 maggio 2026, business, 1 passeggero"

The Claude Code session will:
1. Receive the inbound via the Telegram channels plugin.
2. Call the n8n webhook `/webhook/travel-agent`.
3. Receive the 5-source JSON response.
4. Synthesize a Telegram-friendly summary.
5. Save the full report to a new Notion page under business/work (for confirmed business events) or Inspirations (for exploratory).
6. Reply on Telegram.

See [`USAGE.md`](./USAGE.md) for example queries and expected outputs.

---

## Step 8 — (Optional) Travel Document Organizer

Set up the periodic Gmail scanner that organizes booking confirmations and speaker invitations into Notion. See [`travel-organizer/README.md`](./travel-organizer/README.md).

---

## Troubleshooting

If anything doesn't work, see [`TROUBLESHOOTING.md`](./TROUBLESHOOTING.md). Common issues:

- **n8n webhook returns 404** → workflow not activated. Click "Active" toggle.
- **`Channel notifications skipped: ...is from inline`** in Claude debug log → don't pass `--plugin-dir` flag, let Claude resolve via `enabledPlugins`.
- **Duffel returns `insufficient_permissions`** → token is read-only. Generate Read & Write token.
- **Gemini returns 503 UNAVAILABLE** → use `gemini-flash-latest` alias instead of pinning a specific version.
- **All 5 nodes return empty** → check `Extract Params` node first; may need `OPENAI_API_KEY` env var.
