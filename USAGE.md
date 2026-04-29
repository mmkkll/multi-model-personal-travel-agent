# Usage

## Sending queries

### Via Telegram (recommended)

Just send a natural-language message to your bot. Examples (any language):

```
Flights from London to Tokyo on 2026-12-10, 1 passenger
```
```
Train from Berlin to Munich on 2026-11-20
```
```
Voli da Roma a Madrid il 15 giugno 2026, business
```
```
Vuelo de Madrid a Buenos Aires 5 enero 2027, ida y vuelta
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
  -d '{"query":"Flights from Paris to New York on 2026-09-15, business"}' \
  --max-time 180 | jq
```

Response shape:

```json
{
  "gemini": "Hello, I'm your travel agent. For your business trip...",
  "perplexity": "### Flight options\nFor your trip from Paris (CDG)...",
  "openai": "Here's a curated itinerary for your trip...",
  "duffel": {
    "primary": "CDG",
    "recommendedOrigin": "CDG",
    "usedFallback": false,
    "note": "Direct flights available from CDG",
    "byOrigin": {
      "CDG": {
        "direct": [
          {
            "carrier": "Air France",
            "flight_number": "AF6",
            "stops": 0,
            "dep": "2026-09-15T10:30:00",
            "arr": "2026-09-15T13:00:00",
            "price": 642.50,
            "currency": "EUR"
          }
        ],
        "any": [...]
      },
      "ORY": {"direct": [], "any": [...]}
    }
  },
  "gmaps": {
    "routes": [
      {
        "duration": "27480s",
        "distance_km": 5837,
        "steps": [...]
      }
    ]
  }
}
```

## Query patterns

| Pattern | Example | Agent extracts |
|---|---|---|
| Single origin + destination + date | "Flights LHR to JFK 2026-12-01" | origin=LHR, dest=JFK, date=2026-12-01 |
| With return date | "London to NYC out 12/01 back 12/05" | + return_date=2026-12-05 |
| Origin via city name | "Flights from Berlin to Madrid Jul 10" | origin=BER (resolved from city) |
| Destination without airport | "Train to Lausanne next Friday" | dest=GVA (Lausanne has no airport, nearest IATA = Geneva) |
| Multiple passengers | "2 passengers Rome to Lisbon May 1" | passengers=2 |
| Ambiguous city | "Flight to Springfield" | The model picks the most likely (e.g., SGF for Springfield, MO) — disambiguate by adding country: "to Springfield, IL, USA" |
| Business/leisure context | "Business trip to..." or "Vacation in..." | hints LLMs (no params change) |

## Notion output

After processing, the agent saves a structured trip page to Notion. Default routing:

- **Confirmed business event** (you mentioned a panel/speech/conference, OR an existing business-work page matches) → page goes to `business/work`
- **Exploratory query** (no specific event mentioned) → page goes to `Inspirations`

Each Notion page includes (where data is available):

- ✈️ Flights — Duffel offers table with prices
- 🚆 Trains — Google Maps Routes alternatives with line names
- 🎯 Recommendation — synthesized from 3 LLMs
- 📋 TODO — derived from query intent + LLM suggestions
- 🔗 Booking links — direct links to airline/rail/booking sites
- 📊 Metadata — refresh timestamp, models queried, fallback used

## Voice messages

Send a Telegram voice note. The Claude Code session uses Whisper to transcribe locally, then processes the text. Replies can come back as voice (via ElevenLabs if configured) or text.

## Limitations

- **Free tier limits**: Gemini Flash has 15 RPM. If you query rapidly you'll hit `429 RESOURCE_EXHAUSTED`. Mitigation: use `gemini-flash-latest` (auto-routes to least loaded variant) or upgrade to Tier 1.
- **Duffel test mode**: includes "Duffel Airways" stub carrier and capped slot diversity. Use live mode for real prices.
- **Google Maps Routes**: covers public transit only. Doesn't include intercity bus operators outside major networks. Coverage of operators depends on their GTFS feeds — usually OK for major rail (Frecciarossa, ICE, TGV, Eurostar), partial for some regional carriers.
- **No booking**: this agent only researches. Actual booking happens via the airline/rail website.

## Customization

### Change default origins (FALLBACK_CHAIN)

The shipped fallback chain `FLR, BLQ, PSA, FCO, LIN` is a sample regional cluster. To customize for your region:

1. **In the `Extract Params` node prompt** — n8n UI → open the node → edit `jsonBody`. Update the IATA mapping rules to match your region:

   ```
   REGOLE IATA:
   - London -> LHR (default), LGW/STN if specified
   - New York -> JFK (default), LGA, EWR if specified
   - Tokyo -> HND (default), NRT if specified
   - ...
   ```

2. **In the `Duffel Flights` Code node** — search for `FALLBACK_CHAIN` and update:

   ```javascript
   const FALLBACK_CHAIN = ['LHR', 'LGW', 'STN', 'LTN', 'MAN'];   // UK
   const FALLBACK_CHAIN = ['JFK', 'LGA', 'EWR', 'BWI', 'BOS'];   // US East Coast
   const FALLBACK_CHAIN = ['FRA', 'MUC', 'ZRH', 'VIE', 'BER'];   // DACH
   const FALLBACK_CHAIN = ['MAD', 'BCN', 'LIS', 'OPO', 'AGP'];   // Iberia
   ```

The agent always tries the user-specified primary origin first, then iterates through the fallback chain to find direct flights.

### Adjust LLM prompts

Each of the 3 LLM nodes (Gemini, Perplexity, OpenAI) has its own prompt embedded in the `jsonBody` parameter. Customize tone, length, focus areas:

- "always include sustainability rating"
- "prefer airlines with vegetarian meal options"
- "mention frequent-flyer alliance benefits (Star Alliance / SkyTeam / Oneworld)"
- "include carbon footprint estimates"
- "always reply in Spanish" (or any language)

### Add a 4th LLM

Duplicate one of the LLM HTTP nodes, point it at a new provider:
- **Anthropic Claude**: `https://api.anthropic.com/v1/messages`
- **Mistral**: `https://api.mistral.ai/v1/chat/completions`
- **DeepSeek**: `https://api.deepseek.com/chat/completions`
- **Together AI**: `https://api.together.xyz/v1/chat/completions`

Wire it into the Merge node (bump `numberInputs` to 6) and update the Format Results JS to include the new key.

### Add hotel search

Duffel's `/stays` API supports hotel search. Add a 6th node "Duffel Stays" that runs in parallel:

```
POST https://api.duffel.com/stays/search
Headers: Authorization: Bearer ${DUFFEL_API_KEY}, Duffel-Version: v2
Body: {
  "data": {
    "location": {"radius": 10, "geographic_coordinates": {...}},
    "check_in_date": "2026-12-01",
    "check_out_date": "2026-12-03",
    "guests": [{"type": "adult"}, {"type": "adult"}]
  }
}
```

Or for chain-specific (e.g., Marriott Bonvoy, Hilton Honors): use their respective APIs (Marriott Direct Booking API, Hilton Connect API — both partnership-only).

### Add restaurant search

Google Places API "nearbysearch" works well for restaurants near the destination. Add an HTTP node parallel to GMaps Transit. Combine in the Format Results JS.

### Change default language

The `Extract Params` prompt is in English by default but accepts queries in any language. To change the *prompt language itself*:

1. Open the `Extract Params` node in n8n UI.
2. Edit the prompt text in `jsonBody` — translate the rules and examples to your language.
3. Update the LLM research prompts (Gemini, Perplexity, OpenAI) to respond in your preferred language.

The agent will work fine in any language as long as Extract Params can parse the query and the LLMs can respond.
