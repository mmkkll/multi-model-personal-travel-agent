# Notion Travel Structure

The agent uses 5 Notion pages to organize the trip lifecycle:

```
Travel/                                  (root parent — your choice of name)
├── 🌟 Inspirations                       (NOTION_TRAVEL_INSPIRATIONS_ID)
├── 📋 Planning                            (NOTION_TRAVEL_PLANNING_ID)
├── ✈️ business/work                       (NOTION_TRAVEL_BUSINESS_WORK_ID)
├── 🧳 Ready to Travel                     (NOTION_TRAVEL_READY_ID)
└── 📦 Past trips                          (NOTION_TRAVEL_PAST_TRIPS_ID)
```

## Lifecycle

```
                                                          ┌────────────────┐
                                                          │ 🌟 Inspirations │
                                                          │ (exploratory)   │
                                                          └────────┬────────┘
                                                                   │ user starts booking
                                                                   ▼
                                          ┌──────────────────────────────────────┐
   ┌─────────────────────┐                │      📋 Planning                       │
   │ booking confirmation │ ─────────────▶│ (assembling: flights, hotels, ...)    │
   │ email arrives        │                └──┬──────────────────────────────┬───┘
   └─────────────────────┘                   │                              │
                                              │ classification: WORK         │ classification: LEISURE
                                              ▼                              ▼
                                    ┌──────────────────┐         ┌──────────────────────┐
   ┌──────────────────┐             │ ✈️ business/work │         │ 🧳 Ready to Travel    │
   │ speaker invitation│ ──────────▶│ (talks, panels,   │         │ (personal trips,     │
   │ email arrives    │             │  conferences)     │         │  ready to depart)    │
   └──────────────────┘             └─────────┬─────────┘         └──────────┬─────────┘
                                              │                              │
                                              │   trip end date < today     │
                                              ▼                              ▼
                                          ┌────────────────────────────┐
                                          │ 📦 Past trips                │
                                          │ (auto-archived)             │
                                          └────────────────────────────┘
```

## How the agent classifies WORK vs LEISURE

When parsing emails or query intent:

- **WORK** if any of: speaker invitation, panel/keynote/conference role, advisory board, comitato, workshop teacher, business meeting, sender is a company/conference/university, the email mentions a confirmed event you're attending in a professional capacity.
- **LEISURE** if any of: vacation, social event, family wedding, personal celebration, sender is a personal contact.
- **AMBIGUOUS** if unclear (e.g., a conference where you're attending as paying audience, a weekend retreat that mixes networking + leisure). The agent will ask you via Telegram before creating the page.

## Page content template

Every trip page (regardless of folder) follows this structure. Sections appear only if data is available.

```markdown
**Date**: 2026-05-19 → 2026-05-21
**Type**: business | leisure
**Source**: <how the trip was created — email forward, query, manual>

## 📍 Geography
Brief context: city, region, nearest airports, transit hubs.

## ✈️ Flights
| # | Carrier | Flight | Route | Stops | Departure | Arrival | Price |
|---|---|---|---|---|---|---|---|
| 1 | <Carrier> | <FlightNum> | <ORIGIN>→<DEST> | direct | <Dep> | <Arr> | <Price> |

(Multi-origin fallback: if no direct flights from primary airport, alternatives shown.)

## 🚆 Trains / Transit
- Route A: 7h38min via Zürich HB (Frecciarossa+EC150+IC1)
- Route B: 8h01min via Lugano (RE80+IC2+IC5)
- Route C: ...

## 🏨 Hotels
For each: name, address, check-in/out, booking code, price, link.

## 🚗 Car rentals
Company, pickup/return, dates, booking code.

## 🍽️ Restaurants
Name, address, date/time, persons, booking code.

## 🎫 Experiences
Tours, museums, activities, tickets.

## 📎 Documents
Boarding passes, vouchers, contracts (PDF uploads).

## 🎯 Raccomandazione finale
Synthesis from 3 LLMs: best mix of options, decision rationale.

## 📋 TODO
- [ ] Decide departure date
- [ ] Book transportation
- [ ] Verify EHL travel discount code
- [ ] ...

## 🔗 Booking links
Direct links to airline, rail, hotel websites.

## 📊 Metadata
- Models queried: Gemini, Perplexity, OpenAI, Duffel, Google Maps
- Refresh date: 2026-04-29
- Multi-origin fallback used: <primary> → <recommended>  (or "no fallback needed")
```

## Optional database properties

If you upgrade the Travel pages to a Notion database (instead of plain pages), useful properties:

| Property | Type | Use |
|---|---|---|
| Title | Title | trip name |
| Status | Select | Inspiration / Planning / Confirmed / Departed / Past |
| Trip type | Select | business / leisure / hybrid |
| Origin | Text | departure city |
| Destination | Text | arrival city |
| Dates | Date (range) | start → end |
| Total cost | Number | budget tracking |
| Conference/Event | Text | event name (for work trips) |
| Role | Select | speaker / panelist / moderator / attendee |
| Booking status | Multi-select | flights ✓ / hotel ✓ / train ✗ / car ✗ |
| Documents | Files | attachments |
| Pre-trip checklist | Checkbox | done/not |

The agent currently uses plain pages, but the prompt is designed to work with either format — adapt the `notion-create-pages` calls to set properties when you migrate.

## Folder vs database choice

- **Folder of pages** (current): simpler, easier visual browsing, no schema constraint.
- **Database with views**: gallery of trips, filter by date/type/status, calendar view of departures.

Recommendation: start with folder, migrate to database once you have 20+ trips.
