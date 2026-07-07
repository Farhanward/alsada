"""Command-line interface: probe / report / run."""
import argparse
import os
import sys
import time

from alsada import db
from alsada.analyze import analyze
from alsada.compare import compare as compare_runs, render as render_compare
from alsada.config import load_client, load_prompts, REPORTS_DIR
from alsada.generate import generate_all
from alsada.providers import get_provider, ProviderError
from alsada.radar import render as render_radar, competitor_standings, cited_sources, opportunities
from alsada.publish import build as build_publish, PUB_DIR
from alsada.report import render, save
from alsada.score import probe_score, label


def _utf8_stdout():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def cmd_probe(engine, model):
    client = load_client()
    prompts = load_prompts()
    provider = get_provider(engine, model, prompts)
    run_id = time.strftime("%Y%m%dT%H%M%S")
    ts = time.time()
    conn = db.connect()
    # Pace requests to stay under free-tier per-minute quotas (0 disables). The delay
    # is skipped for offline engines where it only slows local runs down.
    try:
        delay = float(os.environ.get("ALSADA_PROBE_DELAY", "5"))
    except ValueError:
        delay = 5.0
    if engine in ("mock", "file", "ollama"):
        delay = 0.0
    print("== probe: engine=%s model=%s prompts=%d ==" % (engine, provider.model, len(prompts)))
    for i, p in enumerate(prompts):
        if i and delay:
            time.sleep(delay)
        try:
            answer = provider.ask(p)
        except Exception as exc:  # network/provider failures shouldn't crash the run
            answer = ""
            print("  ! %s failed: %s" % (p["id"], exc))
        an = analyze(answer, client)
        db.insert_probe(conn, run_id, ts, engine, provider.model, p, answer, an)
        sc = probe_score(an)
        comp = (" | vs " + ", ".join(an["competitors"])) if an["competitors"] else ""
        print("  %s  score=%3d  %-12s  cited=%s%s"
              % (p["id"], sc, label(sc), "yes" if an["client_cited"] else "no", comp))
    db.insert_run(conn, run_id, ts, engine, provider.model, len(prompts))
    conn.close()
    return run_id


def cmd_report(run_id=None):
    client = load_client()
    conn = db.connect()
    rid = run_id or db.latest_run_id(conn)
    if not rid:
        print("no runs found. run a probe first.")
        return None
    probes = db.read_probes(conn, rid)
    row = conn.execute("SELECT * FROM runs WHERE run_id=?", (rid,)).fetchone()
    conn.close()
    meta = {"engine": row["engine"], "model": row["model"], "ts": row["ts"]}
    markdown, agg = render(client, probes, meta)
    path = save(markdown, client, rid)
    print("\n=== SUMMARY (%s) ===" % rid)
    print("AI Visibility Score : %.1f / 100 (%s)" % (agg["overall"], label(agg["overall"])))
    print("Share of Voice      : %.1f%%" % agg["sov"])
    print("Invisible in        : %d / %d prompts" % (len(agg["invisible"]), agg["n"]))
    print("Misinformation flags: %d" % len(agg["flagged"]))
    print("Report saved        : %s" % path)
    return path


def cmd_generate(run_id=None):
    client = load_client()
    conn = db.connect()
    rid = run_id or db.latest_run_id(conn)
    if not rid:
        print("no runs found. run a probe first.")
        return None
    probes = db.read_probes(conn, rid)
    conn.close()
    topics = []
    for p in probes:
        if not p.get("mentioned") and p.get("topic") and p["topic"] not in topics:
            topics.append(p["topic"])
    manifest = generate_all(client, topics)
    print("== generate: assets for %d invisible topics ==" % len(topics))
    print("  topics : %s" % ", ".join(topics))
    print("  llms.txt: %s" % manifest["llms_txt"])
    print("  schema  : %s" % manifest["schema"])
    for pg in manifest["pages"]:
        print("  page    : %s" % pg)
    return manifest


def cmd_compare(base=None, head=None):
    client = load_client()
    conn = db.connect()
    runs = conn.execute("SELECT run_id, ts, engine, model FROM runs ORDER BY ts DESC").fetchall()
    if len(runs) < 2:
        print("need at least 2 runs to compare (run a probe before and after publishing).")
        conn.close()
        return None
    head_id = head or runs[0]["run_id"]
    base_id = base or runs[1]["run_id"]
    meta = {r["run_id"]: {"run_id": r["run_id"], "engine": r["engine"], "model": r["model"]} for r in runs}
    bp = db.read_probes(conn, base_id)
    hp = db.read_probes(conn, head_id)
    conn.close()
    cmp = compare_runs(bp, hp)
    md = render_compare(client, meta[base_id], meta[head_id], cmp)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / ("alsada_movement_%s_vs_%s.md" % (base_id, head_id))
    path.write_text(md, encoding="utf-8")
    print("== compare: %s -> %s ==" % (base_id, head_id))
    print("  visibility    : %.1f -> %.1f (%+.1f)" % (cmp["base"]["overall"], cmp["head"]["overall"], cmp["d_overall"]))
    print("  share-of-voice: %.1f%% -> %.1f%% (%+.1f)" % (cmp["base"]["sov"], cmp["head"]["sov"], cmp["d_sov"]))
    print("  newly visible : %d  | lost: %d  | improved: %d" % (len(cmp["gained"]), len(cmp["lost"]), len(cmp["improved"])))
    print("  report        : %s" % path)
    return path


def cmd_radar(run_id=None):
    client = load_client()
    conn = db.connect()
    rid = run_id or db.latest_run_id(conn)
    if not rid:
        print("no runs found. run a probe first.")
        conn.close()
        return None
    probes = db.read_probes(conn, rid)
    row = conn.execute("SELECT * FROM runs WHERE run_id=?", (rid,)).fetchone()
    conn.close()
    meta = {"run_id": rid, "engine": row["engine"], "model": row["model"]}
    md = render_radar(client, probes, meta)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / ("alsada_radar_%s.md" % rid)
    path.write_text(md, encoding="utf-8")
    standings, cm = competitor_standings(probes)
    top = standings[0] if standings else ("-", 0)
    print("== radar: %s ==" % rid)
    print("  your mentions  : %d" % cm)
    print("  top competitor : %s (%d)" % (top[0], top[1]))
    print("  cited sources  : %d" % len(cited_sources(probes)))
    print("  opportunities  : %d" % len(opportunities(probes)))
    print("  report         : %s" % path)
    return path


def cmd_publish(run_id=None):
    client = load_client()
    conn = db.connect()
    rid = run_id or db.latest_run_id(conn)
    if not rid:
        print("no runs found. run a probe first.")
        conn.close()
        return None
    probes = db.read_probes(conn, rid)
    conn.close()
    plan = build_publish(client, probes)
    print("== publish: plan from run %s ==" % rid)
    print("  owned (auto-ready) : %d" % len(plan["owned"]))
    print("  self-submit drafts : %d" % len(plan["self_submit"]))
    print("  earned drafts      : %d" % len(plan["earned"]))
    print("  reference (skip)   : %d" % len(plan["reference"]))
    print("  plan               : %s" % (PUB_DIR / "PLAN.md"))
    return plan


def main(argv=None):
    _utf8_stdout()
    from alsada.config import load_env
    load_env()  # auto-load .env.local (API keys, engine settings)
    ap = argparse.ArgumentParser(prog="alsada", description="AL-SADA AI visibility monitor")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for c in ("probe", "run"):
        sp = sub.add_parser(c)
        sp.add_argument("--engine", default="mock")
        sp.add_argument("--model", default=None)
    rp = sub.add_parser("report")
    rp.add_argument("--run-id", default=None)
    gp = sub.add_parser("generate")
    gp.add_argument("--run-id", default=None)
    cp = sub.add_parser("compare")
    cp.add_argument("--base", default=None)
    cp.add_argument("--head", default=None)
    rdp = sub.add_parser("radar")
    rdp.add_argument("--run-id", default=None)
    pubp = sub.add_parser("publish")
    pubp.add_argument("--run-id", default=None)
    servep = sub.add_parser("serve")
    servep.add_argument("--host", default=None)
    servep.add_argument("--port", type=int, default=None)
    sub.add_parser("version")
    args = ap.parse_args(argv)

    if args.cmd == "serve":
        from alsada.service import run_server

        run_server(host=args.host, port=args.port)
        return 0
    if args.cmd == "version":
        from alsada.version import __version__

        print('{"service": "alsada", "version": "%s"}' % __version__)
        return 0

    try:
        if args.cmd == "probe":
            cmd_probe(args.engine, args.model)
        elif args.cmd == "report":
            cmd_report(args.run_id)
        elif args.cmd == "generate":
            cmd_generate(args.run_id)
        elif args.cmd == "compare":
            cmd_compare(args.base, args.head)
        elif args.cmd == "radar":
            cmd_radar(args.run_id)
        elif args.cmd == "publish":
            cmd_publish(args.run_id)
        elif args.cmd == "run":
            rid = cmd_probe(args.engine, args.model)
            cmd_report(rid)
    except ProviderError as exc:
        print("provider error: %s" % exc)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
