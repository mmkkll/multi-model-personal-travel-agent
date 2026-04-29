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

## ✈️ VOLI REALI (Duffel — origin → destination DATE)

> Multi-origin search: tried FLR → BLQ → PSA → FCO → LIN.
> Result: <recommended origin> has direct flights.

### <recommended origin> → <destination> — N direct flights

| # | Carrier | Flight | Departure | Arrival | Duration | Price |
|---|---|---|---|---|---|---|
| 1 | ... | ... | 09:05 | 10:40 | 1h35 | €... |

### Origins checked (reference)

- FLR: 0 direct, cheapest 1-stop ITA AZ... €... 
- BLQ: 0 direct, ...
- ...

## 🚆 TRENI/TRANSIT (Google Maps Routes)

### Route A — VIA <hub> (recommended) ⭐
- Total duration · distance · transfer count
- Step-by-step transit lines

### Route B — VIA <hub>
...

### Route C — ...
...

## 🎯 RACCOMANDAZIONE FINALE

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

## 📊 Metadata ricerca

- Modelli interrogati: Gemini, Perplexity, OpenAI, Duffel multi-origin, Google Maps Routes
- Multi-origin fallback used: <yes/no, which origin>
- Refresh: <ISO timestamp>
```

## Template — Trip confirmed (after booking emails arrive)

```markdown
**Trip dates**: 2026-05-19 → 2026-05-21
**Type**: business
**Event**: HumanX Summit 2026
**Role**: panelist (panel "Beyond Tourism: Destinations as Engines of Innovation", 2026-05-20 11:00)

## 📅 Overview

- Mon 18/5 evening: arrival
- Tue 19/5: travel + check-in
- Wed 20/5: panel + summit
- Thu 21/5: departure

## ✈️ Voli

| Tratta | Carrier | Flight | Date | Time | Seat | Booking |
|---|---|---|---|---|---|---|
| FCO→GVA | ITA | AZ0576 | 19/5 | 09:05→10:40 | 12A | <PNR> |
| GVA→FCO | SWISS | LX1683 | 21/5 | 10:00→11:30 | 8C | <PNR> |

## 🚆 Treni

| Tratta | Treno | Date | Time | Posto | Booking |
|---|---|---|---|---|---|
| Firenze SMN → Roma Termini | Frecciarossa 9550 | 19/5 | 06:30→08:05 | 4D | <PNR> |
| ... | ... | ... | ... | ... | ... |

## 🏨 Hotel

### <hotel name> — Lausanne (2 notti, 19→21 May)
- Address: ...
- Confirmation: <booking ID>
- Price: €X total
- Notes: free Wi-Fi, breakfast included, ...

## 🚗 Auto a noleggio

(if applicable)

## 🍽️ Ristoranti

- Sun 18/5 dinner: <restaurant>, booked for 8pm, 4 persons, conf# ...
- Tue 20/5 lunch: panel networking lunch (provided by event)

## 🎫 Esperienze

(museums, tours, side activities)

## 📎 Documenti

(attached PDFs: boarding pass, hotel confirmation, contract)

## 📞 Contacts

- Event organizer: <name>, <email>, <phone>
- Co-panelists: ...
- Hotel concierge: ...
- Local taxi/transport: ...

## 📋 Da fare prima della partenza

- [ ] Boarding pass mobile (24h prima)
- [ ] Slides finali per panel
- [ ] Confirm participation in welcome dinner
- [ ] Print backup of confirmations
- [ ] Charge devices, pack adapters

## 📍 Note logistiche

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
- Total cost: €...
- Carriers used: ...
- Carbon footprint: ... (if you track this)
```

## Tips for prompt customization

When editing the LLM prompts in n8n to customize Notion output:

- Mention "save full output to Notion in the format described in `content-templates.md`" — the LLMs will follow if you cite the template.
- Use Notion's slash-command markdown shorthand (`---` for dividers, `>` for quotes, `>!` for callouts) — the Notion MCP `create-pages` and `update-page` tools accept enhanced markdown.
- For tables, use standard markdown table syntax — Notion renders them as Notion tables.
- For checkboxes, use `- [ ]` and `- [x]` — Notion renders them as checkable to-dos.
