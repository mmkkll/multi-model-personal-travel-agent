#!/usr/bin/env python3
"""
scrapegraph_lib — shared config for the ScrapeGraphAI travel-research tools.

ScrapeGraphAI is LLM-driven scraping: it fetches a page (optionally with a
headless browser), feeds the content to an LLM, and returns a structured dict.

These tools are meant to run inside a DEDICATED virtualenv, to keep the heavy
dependencies (langchain + playwright) isolated from the rest of your system:

    python3 -m venv ~/.venv-scrapegraph
    ~/.venv-scrapegraph/bin/pip install -r scrapegraph/requirements.txt
    ~/.venv-scrapegraph/bin/playwright install chromium

LLM = Google Gemini. Set the GEMINI_API_KEY environment variable (or put it in a
.env file at the repo root). Default model: gemini-2.5-flash-lite (cheap, fast).
Override with the SCRAPEGRAPH_MODEL environment variable.
"""
import os
import re
import warnings
from pathlib import Path

# Silence cosmetic FutureWarnings from pinned google-* deps on Python 3.9.
warnings.filterwarnings("ignore")
os.environ.setdefault("PYTHONWARNINGS", "ignore")

DEFAULT_MODEL = os.environ.get("SCRAPEGRAPH_MODEL", "google_genai/gemini-2.5-flash-lite")


def gemini_key() -> str:
    """Return GEMINI_API_KEY from the environment, or from a local .env file.

    Lookup order:
      1. GEMINI_API_KEY environment variable
      2. .env in the current working directory
      3. .env at the repository root (parent of this file's directory)
    """
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if key:
        return key
    candidates = [Path.cwd() / ".env", Path(__file__).resolve().parent.parent / ".env"]
    for p in candidates:
        if p.is_file():
            m = re.search(r'^\s*GEMINI_API_KEY\s*=\s*"?([^"\n]+?)"?\s*$', p.read_text(), re.M)
            if m and m.group(1).strip():
                return m.group(1).strip()
    raise RuntimeError(
        "GEMINI_API_KEY not set. Export it (export GEMINI_API_KEY=...) "
        "or add it to a .env file. Get a key at https://aistudio.google.com/apikey"
    )


def build_config(model: str = None, headless: bool = True, verbose: bool = False,
                 max_results: int = None, extra: dict = None) -> dict:
    """Build the graph_config dict for SmartScraperGraph / SmartScraperMultiGraph."""
    cfg = {
        "llm": {"api_key": gemini_key(), "model": model or DEFAULT_MODEL},
        "headless": headless,
        "verbose": verbose,
    }
    if max_results is not None:
        cfg["max_results"] = max_results
    if extra:
        cfg.update(extra)
    return cfg
