#!/usr/bin/env python3
"""
travel-research — lightweight, local, multi-source travel research via ScrapeGraphAI.

This is an alternative to the full n8n multi-model workflow. Instead of orchestrating
3 LLMs + Duffel + Google Maps, it does a focused web research pass with a single
Gemini key and no extra infrastructure:

    web search (DuckDuckGo) -> scrape + merge the top-N results (one LLM pass) -> structured output

Use it when you want quick destination/activity research (what to do, where to eat,
practical tips, rough costs with sources) without standing up n8n, Duffel, etc.
For real flight prices and transit routing, use the n8n workflow (see ../README.md).

Run with the dedicated venv interpreter, e.g.:
    ~/.venv-scrapegraph/bin/python3 scrapegraph/travel-research.py "3 days in Trento in September"

CLI:
    travel-research.py "what to do for 3 days in Lisbon"
    travel-research.py "..." --results 5 --json
    travel-research.py "..." --model google_genai/gemini-2.5-flash   # model override

Import:
    from travel_research import research   # research(query, max_results) -> dict

Note: this script does NOT use ScrapeGraphAI's SearchGraph. In scrapegraphai 1.x the
SearchGraph hardcodes Google as the search engine (which gets blocked) and does not
pass the override down to its nodes. We run the DuckDuckGo search ourselves and then
scrape the resulting URLs with SmartScraperMultiGraph.
"""
import sys, os, json, argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scrapegraph_lib as sgl


def research(query: str, max_results: int = 5, model: str = None) -> dict:
    """Search the web (DuckDuckGo), scrape and merge the top-N results.

    Returns {query, sources, result}. Raises on total failure.
    """
    from scrapegraphai.utils.research_web import search_on_web
    from scrapegraphai.graphs import SmartScraperMultiGraph

    urls = search_on_web(query=query, search_engine="duckduckgo", max_results=max_results)
    urls = [u for u in (urls or []) if u and u.startswith("http")][:max_results]
    if not urls:
        raise RuntimeError("no search results (DuckDuckGo)")

    cfg = sgl.build_config(model=model)
    prompt = (
        f"{query}\n\n"
        "Extract a factual, structured travel-planner research summary: concrete "
        "places/activities, addresses or areas, costs/opening hours when present, "
        "practical tips. Only use information actually present on the pages; do not invent."
    )
    g = SmartScraperMultiGraph(prompt=prompt, source=urls, config=cfg)
    result = g.run()
    return {"query": query, "sources": urls, "result": result}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("query", nargs="+", help="travel research question")
    ap.add_argument("--results", type=int, default=5, help="top-N results to scrape (default 5)")
    ap.add_argument("--model", default=None, help="model override (e.g. google_genai/gemini-2.5-flash)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    q = " ".join(args.query).strip()
    try:
        r = research(q, max_results=args.results, model=args.model)
    except Exception as e:
        print(f"ERR: {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        print(r if isinstance(r, str) else json.dumps(r, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
