# -*- coding: utf-8 -*-
"""Daily blog IndexNow pinger for the deployed carbonflow-blog worker.

The 30 articles are already deployed in the standalone `carbonflow-blog` worker
and are DATE-GATED (each returns 404 before its publishAt, real HTML on/after).
So publishing is automatic. This job's role: on each article's publish day, once
it is actually live (200), push it to IndexNow (Bing/Yandex) so AI search crawls
it immediately. It never pings a 404. Runs daily (task: "AlSada Blog Publisher").
"""
from __future__ import annotations

import datetime
import json
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "blog" / "schedule.json"
LOG = ROOT / "blog" / "publish.log"
INDEXNOW_KEY = "cf3ab927d4e11b2a9f7c85d6e40821fc"
HOST = "www.carbonflows.store"


def log(msg: str) -> None:
    line = f"[{datetime.datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"


def is_live(url: str) -> bool:
    try:
        req = urllib.request.Request(url, method="GET", headers={"User-Agent": _UA})
        with urllib.request.urlopen(req, timeout=12) as r:
            return r.status == 200
    except Exception:
        return False


def indexnow(urls: list[str]) -> dict:
    payload = json.dumps({"host": HOST, "key": INDEXNOW_KEY,
                          "keyLocation": f"https://{HOST}/{INDEXNOW_KEY}.txt",
                          "urlList": urls}).encode("utf-8")
    out = {}
    for ep in ("https://api.indexnow.org/indexnow", "https://www.bing.com/indexnow"):
        try:
            req = urllib.request.Request(ep, data=payload,
                                         headers={"Content-Type": "application/json; charset=utf-8"}, method="POST")
            with urllib.request.urlopen(req, timeout=25) as r:
                out[ep.split("/")[2]] = r.status
        except Exception as e:
            out[ep.split("/")[2]] = getattr(e, "code", str(e)[:30])
    return out


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    today = datetime.date.today().isoformat()
    due = [m for m in manifest
           if not m.get("pinged")
           and m["publishAt"] <= today
           and is_live(m["url"])]
    if not due:
        log("no newly-live articles to ping.")
        return 0
    urls = [m["url"] for m in due] + [f"https://{HOST}/blog"]
    res = indexnow(urls)
    for m in due:
        m["pinged"] = True
        m["pingedAt"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"IndexNow {res} for {len(due)} newly-live article(s): {', '.join(m['slug'] for m in due)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
