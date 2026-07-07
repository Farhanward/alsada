# -*- coding: utf-8 -*-
"""Generic AL-SADA GEO reputation booster (entity-agnostic).

Designed to run once daily just AFTER the Gemini free-tier quota reset (midnight
Pacific), so the measurement always runs with a fresh quota instead of hitting 429.

The target entity is selected purely by environment, so the SAME script boosts
CarbonFlow or byfatmalens (or any future entity):
  ALSADA_CONFIG_DIR / DATA_DIR / REPORTS_DIR / GENERATED_DIR  -> which entity
  ALSADA_BOOST_HOST            -> site host for IndexNow (default carbonflows.store)
  ALSADA_BOOST_INDEXNOW_KEY    -> IndexNow key hosted at /<key>.txt
  ALSADA_BOOST_URLS            -> comma-separated URLs to submit (default: homepage)

Each run performs REAL, honest actions (no score faking):
  IndexNow (recrawl) -> generate (refresh assets) -> radar -> probe (gemini) ->
  append {ts, entity, overall, sov} to <REPORTS_DIR>/reputation_history.jsonl.
Score is read straight from the DB (robust) — not scraped from markdown.
"""
from __future__ import annotations

import datetime
import json
import os
import subprocess
import sys
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # run `python tools/geo_boost.py` from any cwd

from alsada.config import REPORTS_DIR, load_client
from alsada import db
from alsada.score import aggregate
HOST = os.environ.get("ALSADA_BOOST_HOST", "www.carbonflows.store")
KEY = os.environ.get("ALSADA_BOOST_INDEXNOW_KEY", "cf3ab927d4e11b2a9f7c85d6e40821fc")
URLS = [u.strip() for u in os.environ.get("ALSADA_BOOST_URLS", f"https://{HOST}/").split(",") if u.strip()]
HISTORY = REPORTS_DIR / "reputation_history.jsonl"
ENDPOINTS = ["https://api.indexnow.org/indexnow", "https://www.bing.com/indexnow", "https://yandex.com/indexnow"]


def log(m: str) -> None:
    print(f"[{datetime.datetime.now():%H:%M:%S}] {m}", flush=True)


def indexnow() -> dict:
    payload = json.dumps({"host": HOST, "key": KEY,
                          "keyLocation": f"https://{HOST}/{KEY}.txt",
                          "urlList": URLS}).encode("utf-8")
    out = {}
    for ep in ENDPOINTS:
        try:
            req = urllib.request.Request(ep, data=payload,
                                         headers={"Content-Type": "application/json; charset=utf-8"}, method="POST")
            with urllib.request.urlopen(req, timeout=25) as r:
                out[ep.split("/")[2]] = r.status
        except urllib.error.HTTPError as e:
            out[ep.split("/")[2]] = e.code
        except Exception as e:
            out[ep.split("/")[2]] = str(e)[:30]
    return out


def run_cli(args: list[str], timeout: int = 1200) -> int:
    try:
        p = subprocess.run([sys.executable, "-m", "alsada.cli", *args],
                           cwd=str(ROOT), capture_output=True, text=True, timeout=timeout)
        tail = ((p.stdout or "").strip().splitlines()[-1:] or [""])[0]
        log(f"cli {' '.join(args)} -> rc={p.returncode} | {tail[:90]}")
        return p.returncode
    except Exception as e:
        log(f"cli {' '.join(args)} FAILED: {e}")
        return 1


def main() -> int:
    client = load_client()
    log(f"=== GEO boost: {client.get('name')} (host={HOST}) ===")
    idx = indexnow()
    log(f"IndexNow ({len(URLS)} urls): {idx}")
    run_cli(["generate"])
    run_cli(["radar"])
    run_cli(["probe", "--engine", "gemini"])

    overall = sov = None
    run_id = None
    try:
        conn = db.connect()
        run_id = db.latest_run_id(conn)
        if run_id:
            agg = aggregate(db.read_probes(conn, run_id))
            overall, sov = agg.get("overall"), agg.get("sov")
        conn.close()
    except Exception as e:
        log(f"score read failed: {e}")

    entry = {"ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
             "entity": client.get("name"), "engine": "gemini", "run_id": run_id,
             "overall": overall, "sov": sov, "indexnow": idx}
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with HISTORY.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    log(f"overall={overall} sov={sov} -> history appended ({HISTORY})")
    log("=== done ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
