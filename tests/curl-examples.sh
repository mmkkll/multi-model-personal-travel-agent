#!/bin/bash
# Quick test queries for the Multi-Model Personal Travel Agent
# Usage: bash tests/curl-examples.sh
#
# Set N8N_BASE_URL in env or pass as first arg.

set -e

N8N="${N8N_BASE_URL:-${1:-http://localhost:5678}}"
WEBHOOK="${N8N}/webhook/travel-agent"

echo "=== Test 1 — Domestic short-haul ==="
curl -s -X POST "$WEBHOOK" \
  -H "Content-Type: application/json" \
  -d '{"query":"Flights London to Edinburgh on 2026-12-01, 1 passenger"}' \
  --max-time 180 | jq '{
    gemini_len: (.gemini // "" | length),
    perplexity_len: (.perplexity // "" | length),
    openai_len: (.openai // "" | length),
    duffel_recommended: .duffel.recommendedOrigin,
    duffel_used_fallback: .duffel.usedFallback,
    duffel_top_offer: .duffel.byOrigin[.duffel.recommendedOrigin].direct[0],
    gmaps_routes_count: (.gmaps.routes // [] | length)
  }'

echo
echo "=== Test 2 — Multi-origin fallback (no direct from primary) ==="
curl -s -X POST "$WEBHOOK" \
  -H "Content-Type: application/json" \
  -d '{"query":"Flights and trains from a small city to a major hub on 2026-12-15, business"}' \
  --max-time 180 | jq '{
    duffel_primary: .duffel.primary,
    duffel_recommended: .duffel.recommendedOrigin,
    duffel_used_fallback: .duffel.usedFallback,
    duffel_origins_with_directs: [.duffel.byOrigin | to_entries[] | select(.value.direct | length > 0) | .key],
    gmaps_first_route_duration: .gmaps.routes[0].duration
  }'

echo
echo "=== Test 3 — International long-haul (disambiguation case) ==="
curl -s -X POST "$WEBHOOK" \
  -H "Content-Type: application/json" \
  -d '{"query":"Flights from New York to Tokyo on 2026-12-20, return 2026-12-27, business class"}' \
  --max-time 180 | jq '{
    duffel_recommended: .duffel.recommendedOrigin,
    duffel_top_carriers: [.duffel.byOrigin[.duffel.recommendedOrigin].direct[].carrier] | unique,
    gmaps_routes_count: (.gmaps.routes // [] | length)
  }'

echo
echo "=== Test 4 — European cross-border with LCC ==="
curl -s -X POST "$WEBHOOK" \
  -H "Content-Type: application/json" \
  -d '{"query":"Flights Berlin to Madrid 2026-09-15 ritorno 2026-09-17"}' \
  --max-time 180 | jq '{
    duffel_recommended: .duffel.recommendedOrigin,
    duffel_carriers: [.duffel.byOrigin[.duffel.recommendedOrigin].any[].carrier] | unique,
    duffel_cheapest: .duffel.byOrigin[.duffel.recommendedOrigin].any[0]
  }'

echo
echo "=== Test 5 — Pure transit (train) ==="
curl -s -X POST "$WEBHOOK" \
  -H "Content-Type: application/json" \
  -d '{"query":"Train from Paris to Brussels on 2026-11-10 morning"}' \
  --max-time 180 | jq '{
    gmaps_routes: [.gmaps.routes[] | {duration, distance_km, transit_lines: [.steps[].line]}],
    duffel_note: .duffel.note
  }'
