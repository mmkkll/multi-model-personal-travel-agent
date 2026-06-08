# Weather forecast helper

A small, dependency-free Node script for trip weather. Backend: [Open-Meteo](https://open-meteo.com)
— **free, no API key**.

Tiered behavior by date range:
- **≤ 16 days** from now → daily forecast (high accuracy)
- **> 16 days** → climatology fallback (historical mean for the same calendar dates
  over the last ~10 years)

Use it to adapt activity suggestions to the weather (outdoor on sunny days, indoor on
rainy ones) and to add a packing hint to a trip plan.

## Usage

```bash
node weather/weather-forecast.mjs --city "Madrid" --start 2026-05-10 --end 2026-05-15
node weather/weather-forecast.mjs --city "Tokyo"  --start 2026-09-01 --end 2026-09-07 --json
node weather/weather-forecast.mjs --lat 40.4 --lon -3.7 --start 2026-05-10 --end 2026-05-15
```

- `--city` is geocoded via Open-Meteo's geocoding API; or pass `--lat`/`--lon` directly.
- `--json` prints the raw structured result.
- Requires Node.js 18+ (uses the global `fetch`).

> Forecasts beyond ~7 days are indicative; treat anything past T-7 days as a trend,
> not a precise prediction.
