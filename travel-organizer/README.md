# Travel Document Organizer

A periodic Claude Code task that scans your Gmail inbox for booking confirmations and speaker invitations, then organizes them into your Notion travel workspace.

## What it does

Runs every 2 hours (configurable). For each run:

1. **Search Gmail** for the last 3 hours: booking confirmations + indirect signals of upcoming trips (panel/speech invitations).
2. **Extract** structured data: dates, destination, role, organizer, contacts.
3. **Classify** each trip as `work` / `leisure` / `ambiguous`.
4. **Match** against existing Notion travel pages.
5. **Update or create** the Notion page with structured booking sections.
6. **Periodic housekeeping**:
   - 48h pre-trip checklist (for upcoming trips in `Planning`)
   - Auto-move on departure day (Planning → business/work for work trips, Planning → Ready to Travel for personal)
   - 5-7 day advance notice for work trips (slide deck reminder, prep TODOs)
   - Auto-archive past trips → `📦 Past trips`

## Architecture

The Document Organizer is implemented as a **Claude Code prompt** (not an n8n workflow) because it requires:
- Reading & writing Notion pages with structured content (Notion MCP tools)
- Reading Gmail with rich filters and content extraction (Gmail MCP tools)
- Multi-step reasoning (classification, matching, conditional updates)

Run it via cron in a Claude Code session that has Telegram channels + Notion + Gmail MCPs configured.

## Setup

### 1. Required MCPs in your Claude session

Make sure your Claude Code session can access:
- **Gmail MCP** (built-in claude.ai connector) — search and read emails
- **Notion MCP** — create, update, fetch, move pages
- **Telegram channels plugin** — for asking ambiguous classifications + sending summaries

### 2. Define the cron job

In your channels session (the same one running the Telegram bot), schedule the prompt every 2 hours:

```javascript
// Use Claude Code's CronCreate tool, or your own cron infrastructure
{
  cron: "37 */2 * * *",   // every 2 hours at :37 (offset from email-monitor cron if you have one)
  prompt: "<contents of organizer-prompt.md>"
}
```

You can also run it manually for testing:

```
On Telegram, send:
"Run travel organizer"

The Claude session executes the prompt and reports back.
```

### 3. The prompt

The full 11-step prompt is in [`organizer-prompt.md`](./organizer-prompt.md). It expects the Notion page IDs as environment variables (or hardcoded — see template).

## Email patterns recognized

### Booking confirmations (Category 1)
- Subject contains: `confirmation`, `conferma`, `booking`, `reservation`, `prenotazione`, `itinerary`, `e-ticket`, `receipt`, `boarding`
- OR sender is one of: `trenitalia`, `italotreno`, `lufthansa`, `swiss`, `ita-airways`, `vueling`, `ryanair`, `easyjet`, `booking.com`, `marriott`, `expedia`, `hotels.com`, `hertz`, `europcar`, `avis`, `thefork`, `opentable`, `getyourguide`, `viator`, `airbnb`, etc.

Customize the airline/hotel sender list in the prompt to match your usual providers.

### Speaker/event signals (Category 2)
- Subject contains: `panel`, `speech`, `talk`, `keynote`, `speaker`, `intervento`, `partecipazione`, `invito`, `invitation`, `conference`, `forum`, `summit`, `retreat`, `workshop`, `webinar`, `programma`, `agenda`
- Filter out: newsletters, auto-promotional senders (`noreply*`, `notification*`)

## Output / actions

For each email processed:

- **Booking + matched existing page** → append details to existing page (e.g., add a flight to ✈️ Flights table)
- **Booking + no match** → create new page in `Planning`
- **Signal-WORK + no match** → create new page in `business/work`
- **Signal-LEISURE + no match** → create new page in `Planning` (will auto-move to Ready to Travel on departure day)
- **Signal-AMBIGUOUS** → ask via Telegram: "Business or Leisure? (B/L)" — wait for reply before creating

Telegram summary sent only if at least one email was processed (skip if 0 actionable to avoid noise).

## Customization

### Skip specific senders
Add `-from:noreply@example.com` to the Gmail query in the prompt.

### Add new airline / hotel patterns
Edit the `from:(...)` list in the prompt's Gmail query.

### Change classification rules
Edit the WORK / LEISURE / AMBIGUOUS criteria in the prompt's Step 2.

### Change schedule
Modify the cron expression (default `37 */2 * * *`). Examples:
- Hourly: `7 * * * *`
- Twice daily: `7 9,17 * * *`
- Weekdays only: `7 9-19/2 * * 1-5`

## Limitations

- Currently scans **Gmail only**. Adding iCloud, Outlook, etc. requires additional MCP integrations.
- The classification heuristics are tuned for typical patterns of professional travel (speaker invitations, conference confirmations, business hotel bookings). Adjust the prompt's WORK/LEISURE/AMBIGUOUS criteria if your travel patterns differ (e.g., heavy leisure traveler, family bookings on shared inboxes).
- Date extraction relies on email text; ambiguous date formats (e.g., 1/2/2026 = Jan 2 or Feb 1?) may misclassify.
- The prompt is in **Italian** by default (subject keywords, Telegram messages). Translate if needed.
