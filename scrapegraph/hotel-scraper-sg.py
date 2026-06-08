#!/usr/bin/env python3
"""
hotel-scraper-sg — resilient hotel extractor via ScrapeGraphAI SmartScraperGraph.

An LLM extracts name/price/rating/address regardless of the page markup, so it
survives layout changes and works on any hotel/booking page. This is more robust
than scraping with brittle CSS/aria-label selectors.

Run with the dedicated venv interpreter, e.g.:
    ~/.venv-scrapegraph/bin/python3 scrapegraph/hotel-scraper-sg.py --url "https://www.booking.com/hotel/..."

Heads-up: heavily JS-driven, anti-bot pages (e.g. Google Hotels) may not load
date-specific prices in headless mode. The resilience pays off most on direct
hotel/booking pages where the content is in the HTML.

CLI:
    hotel-scraper-sg.py --url "https://www.booking.com/hotel/it/...html"
    hotel-scraper-sg.py --city "Milan" --hotels "Hotel A,Hotel B" [--checkin 2026-09-04 --checkout 2026-09-05]
    hotel-scraper-sg.py --url "..." --json

Import:
    from hotel_scraper_sg import extract_hotel   # extract_hotel(url) -> dict
"""
import sys, os, json, argparse, urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scrapegraph_lib as sgl

PROMPT = (
    "Extract the hotels on this page. For EACH hotel return: name, price (with currency, "
    "if present), rating/stars, address, and a short note. Only use data actually present "
    "on the page, do not invent. If it is a single-hotel page, return just that one."
)


def google_hotels_url(city: str, term: str) -> str:
    return (f"https://www.google.com/travel/hotels/{urllib.parse.quote(city)}"
            f"?q={urllib.parse.quote(term + ' hotel ' + city)}&hl=en&curr=EUR")


def extract_hotel(url: str, model: str = None) -> dict:
    """SmartScraperGraph over a hotel/booking page -> structured dict. Raises on failure."""
    from scrapegraphai.graphs import SmartScraperGraph
    cfg = sgl.build_config(model=model)
    return SmartScraperGraph(prompt=PROMPT, source=url, config=cfg).run()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", help="hotel/booking page URL to extract")
    ap.add_argument("--city", help="city (with --hotels, builds a Google Hotels URL)")
    ap.add_argument("--hotels", help="comma-separated hotel names (with --city)")
    ap.add_argument("--checkin", help="YYYY-MM-DD (informational)")
    ap.add_argument("--checkout", help="YYYY-MM-DD (informational)")
    ap.add_argument("--model", default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    targets = []  # (label, url)
    if args.url:
        targets.append((args.url, args.url))
    elif args.city and args.hotels:
        for h in [x.strip() for x in args.hotels.split(",") if x.strip()]:
            targets.append((h, google_hotels_url(args.city, h)))
    else:
        ap.error("provide --url, or --city + --hotels")

    out = []
    for label, url in targets:
        try:
            data = extract_hotel(url, model=args.model)
            out.append({"target": label, "url": url, "data": data})
        except Exception as e:
            out.append({"target": label, "url": url, "error": f"{type(e).__name__}: {e}"})

    result = out[0] if len(out) == 1 else out
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
