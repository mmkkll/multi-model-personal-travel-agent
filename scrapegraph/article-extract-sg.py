#!/usr/bin/env python3
"""
article-extract-sg — robust article extraction via ScrapeGraphAI SmartScraperGraph.

An LLM extracts title/author/date/summary/key_points regardless of the HTML
structure — useful for JS-heavy pages or messy markup where regex stripping fails.
Handy for turning a destination article or a travel news piece into structured data.

Run with the dedicated venv interpreter, e.g.:
    ~/.venv-scrapegraph/bin/python3 scrapegraph/article-extract-sg.py "https://example.com/article"

CLI:
    article-extract-sg.py "https://example.com/article"
    article-extract-sg.py "..." --subject     # return ONLY a visual subject (image seed)
    article-extract-sg.py "..." --json

Import:
    from article_extract_sg import extract_article, extract_subject
"""
import sys, os, json, argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scrapegraph_lib as sgl

ARTICLE_PROMPT = (
    "Extract from this article page: title, author (if present), published_date (if present), "
    "summary (3-4 sentences), key_points (list of the main points), and topics (keywords). "
    "Only content actually present, do not invent."
)
SUBJECT_PROMPT = (
    "Read this article and produce ONE concrete visual subject for an editorial illustration "
    "(a scene with people/objects/places, no abstract concepts, no text, no logos, no detailed "
    'faces, no AI cliches). Return JSON {subject: "...", title: "..."}. In English.'
)


def extract_article(url: str, model: str = None) -> dict:
    """SmartScraperGraph -> dict {title, author, published_date, summary, key_points, topics}."""
    from scrapegraphai.graphs import SmartScraperGraph
    cfg = sgl.build_config(model=model)
    return SmartScraperGraph(prompt=ARTICLE_PROMPT, source=url, config=cfg).run()


def extract_subject(url: str, model: str = None) -> dict:
    """One visual subject seed for an image generator (extract + distill in one robust step)."""
    from scrapegraphai.graphs import SmartScraperGraph
    cfg = sgl.build_config(model=model)
    return SmartScraperGraph(prompt=SUBJECT_PROMPT, source=url, config=cfg).run()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url", help="article URL")
    ap.add_argument("--subject", action="store_true", help="return only a visual subject (image seed)")
    ap.add_argument("--model", default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    try:
        r = extract_subject(args.url, args.model) if args.subject else extract_article(args.url, args.model)
    except Exception as e:
        print(f"ERR: {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    print(json.dumps(r, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
