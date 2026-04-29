# Usage

## Sending queries

### Via Telegram (recommended)

Just send a natural-language message to your bot. Examples:

```
Voli Firenze Roma 10 giugno 2026, 1 passeggero
```
```
Voli e treni da Bologna a Berlino 5 maggio 2026 ritorno 7 maggio, business
```
```
Solo treni da Milano a Parigi 14 giugno 2026
```

The agent will:
1. Send a typing indicator
2. Process for ~30-60s (5 parallel API calls)
3. Reply with a Telegram-formatted summary
4. Save full report to a Notion page (linked in reply)

### Via curl (testing/automation)

```bash
curl -X POST "http://localhost:5678/webhook/travel-agent" \
  -H "Content-Type: application/json" \
  -d '{"query":"Voli e treni da Firenze a Lausanne 19 maggio 2026, business"}' \
  --max-time 180 | jq
```

Response shape:

```json
{
  "gemini": "Buongiorno...",
  "perplexity": "### Opzioni Voli...",
  "openai": "Per il tuo viaggio...",
  "duffel": {
    "primary": "FLR",
    "recommendedOrigin": "FCO",
    "usedFallback": true,
    "note": "Nessun volo diretto da FLR, fallback su FCO",
    "byOrigin": {
      "FLR": {"direct": [], "any": [...]},
      "BLQ": {"direct": [], "any": [...]},
      "PSA": {"direct": [], "any": [...]},
      "FCO": {"direct": [
        {
          "carrier": "ITA Airways",
          "flight_number": "AZ0576",
          "stops": 0,
          "dep": "2026-05-19T09:05:00",
          "arr": "2026-05-19T10:40:00",
          "price": 302.28,
          "currency": "EUR"
        }
      ], "any": [...]},
      "LIN": {"direct": [], "any": [...]}
    }
  },
  "gmaps": {
    "routes": [
      {
        "duration": "27480s",
        "distance_km": 766,
        "steps": [
          {
            "vehicle": "HEAVY_RAIL",
            "line": "FR",
            "from": "Firenze SMN",
            "to": "Bologna Centrale"
          },
          ...
        ]
      }
    ]
  }
}
```

## Query patterns

| Pattern | Example | Agent extracts |
|---|---|---|
| Single origin + destination + date | "Voli FLR a BCN 10 giugno" | origin=FLR, dest=BCN, date=2026-06-10 |
| With return date | "Voli FLR-BCN andata 10/6 ritorno 12/6" | + return_date=2026-06-12 |
| Origin via city name | "Voli da Firenze a Lausanne 19/5/2026" | origin=FLR (Firenze→FLR resolved) |
| Destination without airport | "Voli a Lausanne" | dest=GVA (Lausanne has no airport, nearest IATA = Geneva) |
| Multiple passengers | "2 passeggeri Roma Madrid 1 luglio" | passengers=2 |
| Business/leisure context | "Viaggio business..." or "vacanza..." | hints LLMs (no params change) |

## Notion output

After processing, the agent saves a structured trip page to Notion. Default routing:

- **Confirmed business event** (you mentioned a panel/speech/conference, OR an existing business-work page matches) → page goes to `business/work`
- **Exploratory query** (no specific event mentioned) → page goes to `Inspirations`

Each Notion page includes (where data is available):

- ✈️ Voli — Duffel offers table with prices
- 🚆 Treni — Google Maps Routes alternatives with line names
- 🎯 Raccomandazione finale — synthesized from 3 LLMs
- 📋 TODO — derived from query intent + LLM suggestions
- 🔗 Booking links — direct links to airline/rail/booking sites
- 📊 Metadata — refresh timestamp, models queried, fallback used

## Voice messages

Send a Telegram voice note. The Claude Code session uses Whisper to transcribe locally, then processes the text. Replies can come back as voice (via ElevenLabs if configured) or text.

## Limitations

- **Free tier limits**: Gemini 2.5 Flash has 15 RPM. If you query rapidly you'll hit `429 RESOURCE_EXHAUSTED`. Mitigation: switch to `gemini-flash-latest` (auto-routes to least loaded variant) or a paid tier.
- **Duffel test mode**: includes "Duffel Airways" stub carrier and capped slot diversity. Use live mode for real prices.
- **Google Maps Routes**: covers public transit only. Doesn't include intercity bus operators outside major networks. Italian high-speed rail (Frecciarossa, Italo) coverage depends on operator GTFS feeds — usually OK for Frecciarossa, partial for Italo.
- **No booking**: this agent only researches. Actual booking happens via the airline/rail website.
- **Origin defaults**: the workflow's Extract Params prompt assumes Italian users. To customize default origins, edit the prompt inside the `Extract Params` node in n8n.

## Customization

### Change default origins

Edit the `Extract Params` node's prompt in n8n. The default fallback chain is `[FLR, BLQ, PSA, FCO, LIN]`. Change to your own preference (e.g., `[LHR, LGW, STN, LTN, MAN]` for UK users).

The fallback chain is also hardcoded in the `Duffel Flights` Code node — search for `FALLBACK_CHAIN` constant.

### Adjust LLM prompts

Each of the 3 LLM nodes (Gemini, Perplexity, OpenAI) has its own prompt embedded in the `jsonBody` parameter. Customize tone, length, focus areas (e.g., add "always include sustainability rating" or "prefer airlines with vegetarian meal options").

### Add a 4th LLM

Duplicate one of the LLM HTTP nodes, point it at a new provider (Anthropic Claude, Mistral, etc.). Wire it into the Merge node (bump `numberInputs` to 6) and update the Format Results JS to include the new key.

### Add hotel search

Duffel's `/stays` API also supports hotel search. You can add a 6th node "Duffel Stays" that runs in parallel for hotel inventory.
