# Installation Guide

Step-by-step setup for the Multi-Model Personal Travel Agent. Plan ~90-120 minutes for first-time setup including all API account verifications.

## Table of contents

1. [Prerequisites](#prerequisites)
2. [Telegram Bot setup](#1--telegram-bot)
3. [n8n self-hosted](#2--n8n-self-hosted)
4. [API keys — detailed setup per provider](#3--api-keys)
   - [Duffel (flights)](#31-duffel--flight-search)
   - [Google Maps Platform — Routes API](#32-google-maps-platform--routes-api)
   - [OpenAI](#33-openai)
   - [Google Gemini](#34-google-gemini)
   - [Perplexity](#35-perplexity)
   - [Notion](#36-notion)
5. [Notion workspace structure](#4--notion-workspace)
6. [Import the n8n workflow](#5--import-n8n-workflow)
7. [Claude Code + Telegram channels plugin](#6--claude-code-with-telegram-channels-plugin)
8. [Test end-to-end](#7--test-end-to-end)
9. [Optional: Document Organizer cron](#8--optional-travel-document-organizer)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

| Item | Why | How to check / install |
|---|---|---|
| **macOS, Linux, or WSL** | n8n + Claude Code support these | `uname -a` |
| **Node.js 20+** | Required by n8n and most CLI tooling | `node --version` → install via [nodejs.org](https://nodejs.org) or `brew install node` |
| **Bun runtime** | The Telegram channels plugin runs on Bun | `bun --version` → `curl -fsSL https://bun.sh/install \| bash` |
| **Claude Code CLI** | The orchestrator runs as a Claude Code session | `claude --version` → `curl -fsSL claude.ai/install.sh \| bash` |
| **A credit card** | Required for Duffel + Google Cloud (free tier still requires billing enabled) | — |
| **Telegram account** | For the bot interface | — |
| **Notion account** | For trip organization | — |

> **Permissions note**: this guide assumes you can install software in your home directory and create LaunchAgents (macOS) or systemd units (Linux). No root/sudo required for the agent itself, but `pmset` adjustments (recommended) need sudo on macOS.

---

## 1 — Telegram Bot

### 1.1 Create the bot

1. Open Telegram, find user **@BotFather** (verified, blue checkmark).
2. Start a chat. Send: `/newbot`
3. BotFather asks for:
   - **Bot name** (display name shown to users): pick something memorable, e.g., "My Travel Agent"
   - **Bot username**: must end in `bot`, e.g., `mytravelagent_personal_bot`. Must be unique across Telegram.
4. BotFather replies with the **API token**, format `123456789:AAEa1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q`.
5. **Save this token** as `TELEGRAM_BOT_TOKEN` in your `.env`.

### 1.2 (Optional but recommended) Polish the bot

Still chatting with @BotFather:
- `/setdescription` — describe what the bot does (visible in chat info)
- `/setabouttext` — short bio (visible in profile)
- `/setuserpic` — profile picture
- `/setcommands` — register commands (e.g., `/start`, `/help`, `/travel`)
- `/setprivacy` — for groups: choose `Disable` so the bot sees all messages, or `Enable` (default) so it only sees `/commands` and replies/mentions

### 1.3 Get your personal Telegram chat ID

The bot must know which chat IDs are allowed. To get yours:

1. Open a chat with your new bot (search by username).
2. Send any message (e.g., "hi").
3. Open in browser:
   ```
   https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
   ```
4. JSON response contains:
   ```json
   {"ok": true, "result": [{
     "update_id": ...,
     "message": {
       "message_id": ...,
       "from": {"id": <YOUR_USER_ID>, "first_name": "...", ...},
       "chat": {"id": <YOUR_CHAT_ID>, "type": "private", ...},
       "date": ...,
       "text": "hi"
     }
   }]}
   ```
5. Copy `chat.id` (positive integer). Save as `TELEGRAM_CHAT_ID`.

> If `result` is empty: send another message in your bot chat, then refresh the URL. Telegram caches updates for 24h.

### 1.4 (Optional) Test with curl

```bash
curl -X POST "https://api.telegram.org/bot<TOKEN>/sendMessage" \
  -d "chat_id=<YOUR_CHAT_ID>" \
  -d "text=hello from API"
```

If you receive the message, the token + chat ID are correct.

---

## 2 — n8n self-hosted

### 2.1 Install

```bash
# Global npm install
npm install -g n8n@latest

# Verify
n8n --version
```

### 2.2 Run

```bash
n8n start
```

Visit `http://localhost:5678`. First-launch setup:
1. Create owner account (email + password — local, never shared externally).
2. n8n shows the dashboard.

> The default port is `5678`. Change with `N8N_PORT=8080 n8n start` or set in `~/.n8n/config`.

### 2.3 Production: always-on daemon

#### macOS — LaunchAgent

Create `~/Library/LaunchAgents/com.local.n8n.plist`:

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
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key><string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
    <key>HOME</key><string>/Users/YOU</string>
    <!-- API keys for n8n env-resolved expressions -->
    <key>OPENAI_API_KEY</key><string>your-openai-key</string>
    <key>GEMINI_API_KEY</key><string>your-gemini-key</string>
    <key>GOOGLE_MAPS_API_KEY</key><string>your-gmaps-key</string>
    <key>DUFFEL_API_KEY</key><string>your-duffel-key</string>
    <key>PERPLEXITY_API_KEY</key><string>your-perplexity-key</string>
  </dict>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>/tmp/n8n.log</string>
  <key>StandardErrorPath</key><string>/tmp/n8n-err.log</string>
</dict>
</plist>
```

Replace `YOU` with your username. Then:
```bash
launchctl bootstrap "gui/$(id -u)" ~/Library/LaunchAgents/com.local.n8n.plist
```

> Verify with `launchctl list | grep n8n`. To see logs: `tail -f /tmp/n8n.log`.

#### Linux — systemd

Create `/etc/systemd/system/n8n.service`:

```ini
[Unit]
Description=n8n
After=network.target

[Service]
Type=simple
User=YOU
ExecStart=/usr/bin/n8n start
Environment="OPENAI_API_KEY=your-openai-key"
Environment="GEMINI_API_KEY=your-gemini-key"
Environment="GOOGLE_MAPS_API_KEY=your-gmaps-key"
Environment="DUFFEL_API_KEY=your-duffel-key"
Environment="PERPLEXITY_API_KEY=your-perplexity-key"
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now n8n
journalctl -u n8n -f   # logs
```

### 2.4 Security

- **Never expose n8n to the public internet** without authentication. By default it binds to `0.0.0.0:5678` accessible via LAN.
- For local-only: set `N8N_HOST=127.0.0.1`.
- For remote access (your other devices): use a tunnel — Tailscale, Cloudflare Tunnel, ngrok, or SSH port-forward. Avoid plain port-forwarding.
- Enable n8n's built-in basic auth: `N8N_BASIC_AUTH_ACTIVE=true N8N_BASIC_AUTH_USER=user N8N_BASIC_AUTH_PASSWORD=...`

---

## 3 — API keys

### 3.1 Duffel — flight search

Duffel provides access to 300+ airlines including low-cost carriers (Ryanair, easyJet, Vueling, Wizz, etc.) via a single REST API.

#### Sign up

1. Go to https://app.duffel.com/join.
2. Provide email + password. Verify via email link.
3. **Account verification (KYC)** is required to access **Live mode**:
   - Settings → Organization → fill in business name, address, billing details.
   - Add a payment method (credit card). Duffel charges per confirmed order, not per search.
   - Verification typically completes in 5-30 minutes.

#### Token modes

Duffel has two completely separate environments:

| Mode | Token prefix | Data | Use when |
|---|---|---|---|
| **Test** | `duffel_test_` | Stub airlines + fake offers ("Duffel Airways" carrier appears in results) | Development, integration testing |
| **Live** | `duffel_live_` | Real airlines, real prices, real schedules | Production |

For real research, you need **Live mode**.

#### Token permissions (CRITICAL)

Duffel uses scope-based permissions. The travel agent calls `POST /air/offer_requests` (search) — this is a **write** operation in Duffel's model because it creates a search resource on their side.

When creating a token:
- **Required scope**: `air.offer_requests.create` + `air.offers.read` (or simply "Read & Write" in Duffel's preset selector)
- **NOT sufficient**: "Read-only" — will return `insufficient_permissions` error

Recommended: select "Read & Write" preset. Even though the agent never books through the API (no calls to `/orders` or `/payments`), the search endpoint requires write scope.

#### Generate the token

1. Settings → API access tokens → **Create token**.
2. Choose:
   - **Mode**: Live
   - **Scope**: Read & Write
   - **Name**: e.g., "travel-agent"
3. Copy the token immediately — it's shown only once.
4. Save as `DUFFEL_API_KEY` in `.env`.

#### Pricing

Duffel pricing (as of 2026):
- **Search**: free up to a 1500:1 search-to-booking ratio. Excess searches: $0.005 each.
- **Confirmed order**: $3.00
- **Managed content**: 1% of order value
- **Paid ancillary**: $2.00

For personal research (search only, no bookings via API): expect **~$0.05-$0.50/month** for typical volumes.

#### Test your token

```bash
curl -s -X POST "https://api.duffel.com/air/offer_requests" \
  -H "Authorization: Bearer $DUFFEL_API_KEY" \
  -H "Duffel-Version: v2" \
  -H "Content-Type: application/json" \
  -d '{"data":{"slices":[{"origin":"LHR","destination":"JFK","departure_date":"2026-12-01"}],"passengers":[{"type":"adult"}],"cabin_class":"economy"}}' | jq '.data.offers | length'
```

Expected: a number > 0 (count of offers). If you get an `errors` array, see [Troubleshooting](./TROUBLESHOOTING.md).

---

### 3.2 Google Maps Platform — Routes API

Used for transit routing (trains, buses, subways, light rail, intercity rail).

#### Project setup

1. Go to https://console.cloud.google.com.
2. **Create or select a project**:
   - Top dropdown → "New Project" → name it (e.g., "travel-agent")
   - Or select an existing project
3. Make sure **billing is enabled** for the project: Billing → Link a billing account. Required even for free-tier usage.

#### Enable the API

1. APIs & Services → Library.
2. Search for "Routes API".
3. Click → **Enable**.

> The legacy "Directions API" is different. We use the newer "Routes API" (v2 endpoints). Both can be enabled; the workflow uses Routes API.

#### Create the API key

1. APIs & Services → Credentials → **Create credentials** → API key.
2. The key appears in a popup, format `AIzaSy[33 chars]`. Copy it.
3. Save as `GOOGLE_MAPS_API_KEY` in `.env`.

#### Restrict the key (security best practice)

Click the key in the credentials list → Edit:

- **Application restrictions**:
  - For local development: "None" or "IP addresses" (your home IP)
  - For server deployment: "IP addresses" (server IP)
  - For client-side use (NOT this case): "HTTP referrers" or "Android/iOS"
- **API restrictions**: select **Restrict key** → check only "Routes API". This prevents abuse if leaked.

#### Pricing

Routes API pricing (as of 2026):
- **Compute Routes (basic)**: $0.005 per request, **first 10k requests/month free**
- **Compute Routes (advanced)**: $0.010 per request

The travel agent uses basic routes (transit mode), so personal use stays within free tier. Cloud Console gives **$200 monthly credit** that covers ~40,000 Routes API calls.

#### Test your key

```bash
curl -s -X POST "https://routes.googleapis.com/directions/v2:computeRoutes" \
  -H "Content-Type: application/json" \
  -H "X-Goog-Api-Key: $GOOGLE_MAPS_API_KEY" \
  -H "X-Goog-FieldMask: routes.duration,routes.distanceMeters" \
  -d '{
    "origin":{"address":"Paris, France"},
    "destination":{"address":"Brussels, Belgium"},
    "travelMode":"TRANSIT",
    "transitPreferences":{"allowedTravelModes":["TRAIN","RAIL"],"routingPreference":"FEWER_TRANSFERS"},
    "departureTime":"2026-12-01T08:00:00Z"
  }' | jq
```

Expected: a JSON with a `routes` array. If you get `403 PERMISSION_DENIED`, verify Routes API is enabled and billing is active.

---

### 3.3 OpenAI

Used for:
- **Extract Params** node (`gpt-4o-mini`, JSON mode) — parses natural-language travel queries into structured params
- **OpenAI research** node (`gpt-4o`) — strategic travel recommendations

#### Sign up

1. Go to https://platform.openai.com/signup.
2. Verify email + phone number.
3. Add a payment method: Settings → Billing → add credit card. Required even for paid usage; OpenAI no longer offers a free tier.

#### Generate API key

1. https://platform.openai.com/api-keys → **Create new secret key**
2. Choose:
   - **Type**: "User" key (tied to your account) or "Project" key (tied to a project — recommended for separation)
   - **Permissions**: "All" (read + write) — required for chat completions
   - **Name**: e.g., "travel-agent"
3. Copy the key immediately — shown only once. Format: `sk-proj-[long string]` or `sk-[long string]`.
4. Save as `OPENAI_API_KEY` in `.env`.

#### Set usage limits (recommended)

Go to Settings → Limits:
- **Hard limit** (monthly cap): set to a comfortable budget, e.g., $20/month for personal use.
- **Soft limit**: alerts at $10/month.

This prevents runaway costs from buggy loops.

#### Pricing (as of 2026)

| Model | Input | Output | Travel agent use |
|---|---|---|---|
| `gpt-4o-mini` | $0.15 / 1M tokens | $0.60 / 1M tokens | Extract Params (~$0.0001/query) |
| `gpt-4o` | $2.50 / 1M tokens | $10.00 / 1M tokens | Research node (~$0.01-0.02/query) |

Per query cost: ~$0.02. For 100 queries/month: **~$2**.

#### Test your key

```bash
curl -s "https://api.openai.com/v1/chat/completions" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"Say hello in 3 words"}]}' | jq -r '.choices[0].message.content'
```

Expected: 3 words. If `401 invalid_api_key`, recheck your key.

---

### 3.4 Google Gemini

Used as one of the 3 LLM research models.

#### Sign up

1. Go to https://aistudio.google.com.
2. Sign in with a Google account.
3. Accept Terms of Service.

#### Generate API key

1. https://aistudio.google.com/apikey → **Create API key**.
2. Choose:
   - **In existing project**: pick a Google Cloud project (the same one you used for Routes API works fine)
   - **In new project**: AI Studio creates one for you
3. Copy the key (format `AIzaSy[33 chars]`).
4. Save as `GEMINI_API_KEY` in `.env`.

#### Pricing & rate limits (as of 2026)

| Tier | Free | Tier 1 (paid) |
|---|---|---|
| Models available | gemini-1.5-flash, gemini-2.5-flash, gemini-flash-latest, etc. | All |
| RPM | 15 (gemini-2.5-flash) / 5 (gemini-2.5-pro) | 1000+ |
| Daily limit | 1,500 requests/day | None |
| Cost | $0 | Per-token pricing varies |

For personal use, **free tier is sufficient**. The workflow uses `gemini-flash-latest` which auto-routes to whichever variant is least loaded — handles 503 outages gracefully.

#### Pinned vs alias models

| Model | Stability |
|---|---|
| `gemini-2.5-flash` | Pinned, may return `503 UNAVAILABLE` during demand spikes |
| `gemini-flash-latest` | Auto-aliases to current best — recommended |
| `gemini-2.5-pro` | More capable, higher latency, lower RPM |

The workflow uses `gemini-flash-latest`. If you want pro-quality output, swap in the URL inside the Gemini node.

#### Test your key

```bash
curl -s -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key=$GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Say hello in 3 words"}]}]}' | jq -r '.candidates[0].content.parts[0].text'
```

Expected: 3 words. If `400 INVALID_ARGUMENT`, check the model name. If `403 PERMISSION_DENIED`, the key isn't authorized for the Generative Language API — regenerate.

---

### 3.5 Perplexity

Used as the third LLM research model. Provides web-grounded answers with citations.

#### Sign up

1. Go to https://www.perplexity.ai → Sign up (Google or email).
2. Subscribe to **Pro** ($20/month) for API access. As of 2026, the free tier doesn't include API keys.
3. (Alternative) Pay-as-you-go: https://www.perplexity.ai/settings/api lets you fund credits without subscription.

#### Generate API key

1. https://www.perplexity.ai/settings/api → **Generate**.
2. Copy the key (format `pplx-[long string]`).
3. Save as `PERPLEXITY_API_KEY` in `.env`.

#### Models

The workflow uses `sonar` (general) by default. Other options:
- `sonar` — fast, web-grounded, default
- `sonar-pro` — more comprehensive answers, longer context
- `sonar-reasoning` — chain-of-thought, good for complex queries
- `sonar-deep-research` — extensive research, slower

#### Pricing (as of 2026)

- `sonar`: $1 / 1M input tokens, $1 / 1M output tokens
- `sonar-pro`: $3 / 1M input, $15 / 1M output
- Plus search fee: ~$0.005 per request

For personal use (~50 queries/month): **~$0.50/month**.

#### Test your key

```bash
curl -s "https://api.perplexity.ai/chat/completions" \
  -H "Authorization: Bearer $PERPLEXITY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"sonar","messages":[{"role":"user","content":"Say hello in 3 words"}]}' | jq -r '.choices[0].message.content'
```

Expected: 3 words. If `401`, recheck the key.

---

### 3.6 Notion

Used to store all trip data (the source of truth for the agent).

#### Create the integration

1. Go to https://www.notion.so/my-integrations → **+ New integration**.
2. Set:
   - **Name**: "Travel Agent" (or any descriptive name)
   - **Type**: "Internal" (private, used only by you)
   - **Associated workspace**: select yours
3. **Capabilities** (CRITICAL — set all required):
   - ☑ Read content
   - ☑ Update content
   - ☑ Insert content
   - User capabilities: ☑ Read user information including email addresses
4. Submit → Notion shows the **Internal Integration Token** (format `secret_[long string]` or `ntn_[long string]`).
5. Save as `NOTION_API_TOKEN` in `.env`.

#### Connect the integration to your Travel pages

By default, integrations have access to NO pages. You must explicitly grant access:

1. In Notion, navigate to your **Travel** parent page (or wherever you want trip pages).
2. Top-right `⋮` (three dots) → Connections (or "Add connections" in newer UI).
3. Find your "Travel Agent" integration → Connect.

> Granting access to a parent page automatically grants access to all sub-pages. So connect once at the top level.

#### Test your token

```bash
curl -s "https://api.notion.com/v1/users/me" \
  -H "Authorization: Bearer $NOTION_API_TOKEN" \
  -H "Notion-Version: 2022-06-28" | jq
```

Expected: JSON with `bot.workspace_name`. If `401 unauthorized`, recheck token.

To verify a specific page is accessible:
```bash
PAGE_ID=your-page-id-here
curl -s "https://api.notion.com/v1/pages/$PAGE_ID" \
  -H "Authorization: Bearer $NOTION_API_TOKEN" \
  -H "Notion-Version: 2022-06-28" | jq '.id, .properties.title'
```

If `404 object_not_found`, the integration doesn't have access to that page. Re-do the "Connections" step.

---

## 4 — Notion workspace

### 4.1 Create the Travel structure

In your workspace, create a parent page named "Travel" (or your preferred name).

Inside Travel, create 5 sub-pages:

```
Travel/
├── 🌟 Inspirations
├── 📋 Planning
├── ✈️ business/work
├── 🧳 Ready to Travel
└── 📦 Past trips
```

For each, you can use a different emoji icon (set via Notion's icon picker). The names above are the conventional defaults — adapt to your language/style.

### 4.2 Connect the integration

(See section 3.6 above.) Right-click the parent "Travel" page → Connections → Add → "Travel Agent".

### 4.3 Get the page IDs

For each of the 5 pages, copy its URL and extract the 32-char hex ID:

```
https://www.notion.so/yourworkspace/Inspirations-31ac93b9555e81068bcac0b5c4798b1a
                                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                                this part = page ID
```

The 32-char string at the end (after the last hyphen) is the ID. Notion accepts it with or without dashes (UUID format) for API calls.

Save in `.env`:
```
NOTION_TRAVEL_INSPIRATIONS_ID=31ac93b9555e81068bcac0b5c4798b1a
NOTION_TRAVEL_PLANNING_ID=...
NOTION_TRAVEL_BUSINESS_WORK_ID=...
NOTION_TRAVEL_READY_ID=...
NOTION_TRAVEL_PAST_TRIPS_ID=...
```

> See [`notion/travel-structure.md`](./notion/travel-structure.md) for the full lifecycle (when trips move from one folder to another) and [`notion/content-templates.md`](./notion/content-templates.md) for the page content schema.

---

## 5 — Import n8n workflow

### 5.1 Import

1. Open n8n at `http://localhost:5678`.
2. Top-right `⋮` → "Import from File".
3. Select `n8n/travel-agent-workflow.json` from this repo.
4. Confirm. n8n creates a new workflow named `travel-agent-multi-model` with 10 nodes.

### 5.2 Configure environment variables

The workflow's HTTP nodes reference env vars like `{{ $env.OPENAI_API_KEY }}`. Set these in the environment where n8n runs:

#### Option A: System environment (recommended for production)

If n8n runs as a LaunchAgent/systemd unit, set env vars in the unit file (see section 2.3 above).

#### Option B: n8n's `.env` file

Create `~/.n8n/.env`:
```
OPENAI_API_KEY=...
GEMINI_API_KEY=...
GOOGLE_MAPS_API_KEY=...
DUFFEL_API_KEY=...
PERPLEXITY_API_KEY=...
```

Restart n8n. It picks up `.env` automatically.

#### Option C: n8n's UI Variables (interactive testing)

Settings (gear icon) → Variables → add each.

### 5.3 Activate the workflow

In the workflow editor, click the **Active** toggle (top-right). The webhook URL becomes live.

### 5.4 Test the webhook

```bash
curl -s -X POST "http://localhost:5678/webhook/travel-agent" \
  -H "Content-Type: application/json" \
  -d '{"query":"Flights from London to Paris on 2026-12-01"}' \
  --max-time 180 | jq 'keys'
```

Expected output:
```json
["duffel", "gemini", "gmaps", "openai", "perplexity"]
```

If the response is empty or `404`, see [Troubleshooting](./TROUBLESHOOTING.md).

---

## 6 — Claude Code with Telegram channels plugin

### 6.1 Install the plugin

```bash
# Add the official marketplace (if not already)
claude plugin marketplace add anthropics/claude-plugins-official

# Install the telegram plugin
claude plugin install telegram@claude-plugins-official
```

### 6.2 Configure plugin secrets

The plugin reads `~/.claude/channels/telegram/.env`:

```bash
mkdir -p ~/.claude/channels/telegram
cat > ~/.claude/channels/telegram/.env <<EOF
TELEGRAM_BOT_TOKEN=<your bot token>
EOF
chmod 600 ~/.claude/channels/telegram/.env
```

### 6.3 Configure access control

Copy `telegram-bot/access.json.example` from this repo:

```bash
cp telegram-bot/access.json.example ~/.claude/channels/telegram/access.json
# Edit: replace REPLACE_WITH_YOUR_TELEGRAM_CHAT_ID with your actual chat ID
nano ~/.claude/channels/telegram/access.json
```

The result should look like:
```json
{
  "dmPolicy": "allowlist",
  "allowFrom": ["123456789"],
  "groups": {},
  "pending": {}
}
```

> Anyone NOT in `allowFrom` is silently dropped.

### 6.4 Enable the plugin

Edit `~/.claude/settings.json` (create if missing):
```json
{
  "enabledPlugins": {
    "telegram@claude-plugins-official": true
  }
}
```

Also enable in your project-level settings (where you'll start the channels session) — `<project>/.claude/settings.json`:
```json
{
  "enabledPlugins": {
    "telegram@claude-plugins-official": true
  }
}
```

### 6.5 Start the channels session

Quick start (interactive testing):
```bash
claude --channels "plugin:telegram@claude-plugins-official" \
  --dangerously-skip-permissions \
  --debug-file /tmp/claude-channels-debug.log \
  --debug api,channels,mcp,plugin
```

> ⚠️ **Critical**: do NOT add `--plugin-dir`. It loads the plugin as `inline` source which mismatches the channel argument's expected source `claude-plugins-official`, silently dropping inbound notifications. See [Troubleshooting](./TROUBLESHOOTING.md).

For an always-on background session via LaunchAgent (macOS) or systemd (Linux), see [`telegram-bot/setup.md`](./telegram-bot/setup.md).

### 6.6 Verify the channel registration

```bash
grep "Channel notifications" /tmp/claude-channels-debug.log | tail
```

You want to see:
```
[DEBUG] MCP server "plugin:telegram:telegram": Channel notifications registered
```

NOT:
```
[DEBUG] MCP server "plugin:telegram:telegram": Channel notifications skipped: ...is from inline
```

If you see `skipped`, your invocation has `--plugin-dir`. Remove it.

---

## 7 — Test end-to-end

From your phone, send a message to the bot:

> "Train from Berlin to Munich on 2026-12-15, 1 passenger"

The Claude Code session should:
1. Receive the inbound (debug log shows `notifications/claude/channel`)
2. Call the n8n webhook `POST /webhook/travel-agent`
3. Receive the 5-source JSON
4. Synthesize a Telegram-friendly summary
5. Reply to your chat with the summary
6. Save the full report to a Notion page (link included in reply)

If any step fails, check:
- n8n Executions tab (live workflow runs with per-node input/output)
- `/tmp/claude-channels-debug.log` (Claude session debug)
- Notion page (was it created?)

See [`USAGE.md`](./USAGE.md) for example queries.

---

## 8 — (Optional) Travel Document Organizer

Set up the periodic Gmail scanner that organizes booking confirmations and speaker invitations into Notion. See [`travel-organizer/README.md`](./travel-organizer/README.md) for full setup.

This requires:
- Gmail MCP enabled in your Claude Code session (claude.ai built-in connector)
- Notion MCP enabled (this is automatic if you have the Notion integration)
- A cron-like scheduler — Claude Code's built-in `CronCreate` tool, or your own (cron, launchd, systemd timers)

---

## Troubleshooting

If anything doesn't work end-to-end, see [`TROUBLESHOOTING.md`](./TROUBLESHOOTING.md). Quick reference for the most common issues:

| Symptom | Likely cause | Fix |
|---|---|---|
| n8n webhook returns 404 | Workflow not activated | Click "Active" toggle in workflow editor |
| `Channel notifications skipped: ...is from inline` | Wrong invocation | Remove `--plugin-dir` from claude --channels command |
| Duffel `insufficient_permissions` | Read-only token | Generate Read & Write token |
| Gemini `503 UNAVAILABLE` | Pinned to overloaded model | Use `gemini-flash-latest` alias |
| All 5 nodes return empty | `Extract Params` failed | Check OpenAI key + n8n env vars |
| Telegram silence after sending message | Bot consumed but Claude didn't process | Check debug log, may need bootstrap |
| Notion 404 on page | Integration not connected to that page | Re-do Connections step |
