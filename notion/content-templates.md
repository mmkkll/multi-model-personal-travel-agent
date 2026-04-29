# Notion Page Content Templates

Reference templates for the trip pages the agent creates. Use these when manually creating pages or when customizing the agent's prompts.

## Template — Travel research result (created by `/travel-agent` query)

```markdown
**Date target**: <user-specified or default 30 days out>
**Type**: business | leisure
**Source**: Multi-Model Travel Agent (n8n workflow) — refreshed YYYY-MM-DD

## 📍 Geography

Brief context about the destination's airport / station situation.
- Closest airport: ...
- Alternative hub: ...

## ✈️ REAL FLIGHTS (Duffel — origin → destination DATE)

> Multi-origin search: tried <primary> → <fallback 1> → <fallback 2> → ...
> Result: <recommended origin> has direct flights.

### <recommended origin> → <destination> — N direct flights

| # | Carrier | Flight | Departure | Arrival | Duration | Price |
|---|---|---|---|---|---|---|
| 1 | ... | ... | 09:05 | 10:40 | 1h35 | €... |

### Origins checked (reference)

- <ORIGIN_1>: N direct, cheapest 1-stop <Carrier> <FlightNum> <price>
- <ORIGIN_2>: N direct, ...
- ...

## 🚆 TRAINS / TRANSIT (Google Maps Routes)

### Route A — VIA <hub> (recommended) ⭐
- Total duration · distance · transfer count
- Step-by-step transit lines

### Route B — VIA <hub>
...

### Route C — ...
...

## 🎯 FINAL RECOMMENDATION

Synthesis of 3 LLM outputs:
- Best Star Alliance: ...
- Best budget: ...
- Best train: ...

## 📋 TODO

- [ ] Decide departure date
- [ ] Decide return date
- [ ] Choose mode (flight / train / mix)
- [ ] Book transportation
- [ ] Verify discount codes (e.g., conference travel discount)

## 🔗 Booking links

- [Carrier 1](https://...) · [Carrier 2](https://...) · ...

## 📊 Search metadata

- Models queried: Gemini, Perplexity, OpenAI, Duffel multi-origin, Google Maps Routes
- Multi-origin fallback used: <yes/no, which origin>
- Refresh: <ISO timestamp>
```

## Template — Trip confirmed (after booking emails arrive)

```markdown
**Trip dates**: 2026-09-15 → 2026-09-18
**Type**: business
**Event**: <Conference / Summit name>
**Role**: <speaker / panelist / attendee> (event details + time)

## 📅 Overview

- Day 1 evening: arrival + welcome dinner
- Day 2: travel + check-in
- Day 3: main event
- Day 4: departure

## ✈️ Flights

| Route | Carrier | Flight | Date | Time | Seat | Booking |
|---|---|---|---|---|---|---|
| <ORIGIN>→<DEST> | <Carrier> | <FlightNum> | <Date> | <Departure→Arrival> | <Seat> | <PNR> |
| <DEST>→<ORIGIN> | <Carrier> | <FlightNum> | <Date> | <Departure→Arrival> | <Seat> | <PNR> |

## 🚆 Trains

| Route | Train | Date | Time | Seat | Booking |
|---|---|---|---|---|---|
| <Station A> → <Station B> | <Train name/number> | <Date> | <Departure→Arrival> | <Seat> | <PNR> |

## 🏨 Hotels

### <hotel name> — <city> (N nights)
- Address: ...
- Confirmation: <booking ID>
- Price: <amount> <currency> total
- Notes: free Wi-Fi, breakfast included, ...

## 🚗 Car rentals

(if applicable)

## 🍽️ Restaurants

- Sun 18/5 dinner: <restaurant>, booked for 8pm, 4 persons, conf# ...
- Tue 20/5 lunch: panel networking lunch (provided by event)

## 🎫 Experiences

(museums, tours, side activities)

## 📎 Documents

(attached PDFs: boarding pass, hotel confirmation, contract)

## 📞 Contacts

- Event organizer: <name>, <email>, <phone>
- Co-panelists: ...
- Hotel concierge: ...
- Local taxi/transport: ...

## 📋 Pre-departure TODO

- [ ] Boarding pass mobile (24h prima)
- [ ] Slides finali per panel
- [ ] Confirm participation in welcome dinner
- [ ] Print backup of confirmations
- [ ] Charge devices, pack adapters

## 📍 Logistics notes

- Transit time airport ↔ city center
- Local SIM / eSIM / Wi-Fi info
- Currency, payment methods
- Time zone
- Plug type
```

## Template — Past trip (auto-archived)

After the trip end date passes, the agent moves the page to `📦 Past trips` and (optionally) appends a brief summary:

```markdown
## ✅ Trip completed

- Departed: 2026-05-19
- Returned: 2026-05-21
- Status: <success | partial issues | cancelled>

## 📝 Post-trip notes

(filled in manually if relevant: feedback on hotel, restaurants worth remembering, contacts to follow up with, expenses summary)

## 📊 Travel statistics

- Total distance: ...km
- Total cost: <currency> ...
- Carriers used: ...
- Carbon footprint: ... (if you track this)
```

## Tips for prompt customization

When editing the LLM prompts in n8n to customize Notion output:

- Mention "save full output to Notion in the format described in `content-templates.md`" — the LLMs will follow if you cite the template.
- Use Notion's slash-command markdown shorthand (`---` for dividers, `>` for quotes, `>!` for callouts) — the Notion MCP `create-pages` and `update-page` tools accept enhanced markdown.
- For tables, use standard markdown table syntax — Notion renders them as Notion tables.
- For checkboxes, use `- [ ]` and `- [x]` — Notion renders them as checkable to-dos.
