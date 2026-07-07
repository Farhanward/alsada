# -*- coding: utf-8 -*-
"""AL-SADA daily reputation booster — runs twice daily (09:00 / 21:00).

Each run performs REAL, honest GEO reputation actions (no score faking):
  1. IndexNow  — push all GEO URLs to Bing/Yandex so engines re-crawl them fast.
  2. generate  — refresh on-site GEO assets (llms.txt, schema, answer pages).
  3. radar     — intel: which sources AI cites + visibility opportunities.
  4. probe     — measure real visibility on Gemini (native, free, live web).
  5. history   — append {ts, overall, sov} to reports/reputation_history.jsonl.

Reputation rises over days/weeks as engines index the pages and gain trust —
this loop keeps pushing indexing + fresh signals and tracks the real trajectory.
"""
from __future__ import annotations

import datetime
import json
import re
import subprocess
import sys
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORTS = ROOT / "reports"
HISTORY = REPORTS / "reputation_history.jsonl"
INDEXNOW_KEY = "cf3ab927d4e11b2a9f7c85d6e40821fc"
HOST = "www.carbonflows.store"

GEO_URLS = [
    f"https://{HOST}/",
    f"https://{HOST}/answers/ai-automation",
    f"https://{HOST}/answers/n8n-automation",
    f"https://{HOST}/answers/cloudflare-workers",
    f"https://{HOST}/answers/saas-development",
    f"https://{HOST}/answers/custom-dashboards",
    f"https://{HOST}/answers/zapier-alternative",
    f"https://{HOST}/answers/top-ai-automation-agencies",
    f"https://{HOST}/ai-automation-for-business",
    f"https://{HOST}/saas-development-saudi",
    f"https://{HOST}/workflow-automation-n8n",
    f"https://{HOST}/cloudflare-workers-deployment",
    f"https://{HOST}/custom-dashboard-development",
    f"https://{HOST}/services",
    f"https://{HOST}/ar/ai-automation-for-business",
    f"https://{HOST}/ar/saas-development-saudi",
    f"https://{HOST}/ar/workflow-automation-n8n",
    f"https://{HOST}/ar/cloudflare-workers-deployment",
    f"https://{HOST}/ar/custom-dashboard-development",
    f"https://{HOST}/blog/business-automation-saudi",
]

ENDPOINTS = [
    "https://api.indexnow.org/indexnow",
    "https://www.bing.com/indexnow",
    "https://yandex.com/indexnow",
]


def log(msg: str) -> None:
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def indexnow() -> dict:
    payload = json.dumps({
        "host": HOST, "key": INDEXNOW_KEY,
        "keyLocation": f"https://{HOST}/{INDEXNOW_KEY}.txt",
        "urlList": GEO_URLS,
    }).encode("utf-8")
    out = {}
    for ep in ENDPOINTS:
        try:
            req = urllib.request.Request(ep, data=payload,
                                         headers={"Content-Type": "application/json; charset=utf-8"},
                                         method="POST")
            with urllib.request.urlopen(req, timeout=25) as r:
                out[ep.split("/")[2]] = r.status
        except urllib.error.HTTPError as e:
            out[ep.split("/")[2]] = e.code
        except Exception as e:
            out[ep.split("/")[2]] = str(e)[:30]
    return out


def run_cli(args: list[str], timeout: int = 600) -> int:
    try:
        p = subprocess.run([sys.executable, "-m", "alsada.cli", *args],
                           cwd=str(ROOT), capture_output=True, text=True, timeout=timeout)
        tail = (p.stdout or "").strip().splitlines()[-1:] or [""]
        log(f"cli {' '.join(args)} -> rc={p.returncode} | {tail[0][:80]}")
        return p.returncode
    except Exception as e:
        log(f"cli {' '.join(args)} FAILED: {e}")
        return 1


def latest_score() -> tuple[float | None, float | None, str]:
    reps = sorted(REPORTS.glob("alsada_CarbonFlow_*.md"))
    if not reps:
        return None, None, ""
    txt = reps[-1].read_text(encoding="utf-8")
    m = re.search(r"الظهور الكلية:\s*([\d.]+)", txt)
    s = re.search(r"مقابل المنافسين:\s*([\d.]+)", txt)
    return (float(m.group(1)) if m else None,
            float(s.group(1)) if s else None,
            reps[-1].name)


def main() -> int:
    log("=== AL-SADA daily boost start ===")
    idx = indexnow()
    log(f"IndexNow: {idx}")
    run_cli(["generate"])                       # refresh on-site GEO assets
    run_cli(["radar"])                          # sources + opportunities intel
    run_cli(["probe", "--engine", "gemini"])    # measure (free, grounded)
    overall, sov, rep = latest_score()
    entry = {
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "engine": "gemini",
        "overall": overall,
        "sov": sov,
        "report": rep,
        "indexnow": idx,
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    with HISTORY.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    log(f"score overall={overall} sov={sov} -> history appended")
    log("=== done ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
