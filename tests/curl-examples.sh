#!/bin/bash
# Quick test queries for the Multi-Model Personal Travel Agent
# Usage: bash tests/curl-examples.sh
#
# Set N8N_BASE_URL in env or pass as first arg.

set -e

N8N="${N8N_BASE_URL:-${1:-http://localhost:5678}}"
WEBHOOK="${N8N}/webhook/travel-agent"

echo "=== Test 1 — Italy domestic (Florence to Rome) ==="
curl -s -X POST "$WEBHOOK" \
  -H "Content-Type: application/json" \
  -d '{"query":"Voli Firenze Roma 10 giugno 2026, 1 passeggero"}' \
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
echo "=== Test 2 — Multi-origin fallback (Italy to Lausanne, no airport) ==="
curl -s -X POST "$WEBHOOK" \
  -H "Content-Type: application/json" \
  -d '{"query":"Voli e treni da Firenze a Lausanne 19 maggio 2026, business, 1 passeggero"}' \
  --max-time 180 | jq '{
    duffel_primary: .duffel.primary,
    duffel_recommended: .duffel.recommendedOrigin,
    duffel_used_fallback: .duffel.usedFallback,
    duffel_origins_with_directs: [.duffel.byOrigin | to_entries[] | select(.value.direct | length > 0) | .key],
    gmaps_first_route_duration: .gmaps.routes[0].duration
  }'

echo
echo "=== Test 3 — International (Munich, Germany — disambiguation Monaco vs Munich) ==="
curl -s -X POST "$WEBHOOK" \
  -H "Content-Type: application/json" \
  -d '{"query":"Voli da Firenze a Monaco di Baviera (Munich, Germania) il 15 giugno 2026 ritorno 17 giugno"}' \
  --max-time 180 | jq '{
    duffel_recommended: .duffel.recommendedOrigin,
    duffel_top_carriers: [.duffel.byOrigin[.duffel.recommendedOrigin].direct[].carrier] | unique,
    gmaps_routes: [.gmaps.routes[] | {duration, distance_km, transit_lines: [.steps[].line]}]
  }'

echo
echo "=== Test 4 — Spain (Barcelona) ==="
curl -s -X POST "$WEBHOOK" \
  -H "Content-Type: application/json" \
  -d '{"query":"Voli FLR a BCN 16 giugno 2026 ritorno 17 giugno, business"}' \
  --max-time 180 | jq '{
    duffel_recommended: .duffel.recommendedOrigin,
    duffel_carriers_with_lcc: [.duffel.byOrigin[.duffel.recommendedOrigin].any[].carrier] | unique,
    duffel_cheapest: .duffel.byOrigin[.duffel.recommendedOrigin].any[0]
  }'
