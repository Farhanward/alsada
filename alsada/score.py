"""Scoring: per-probe visibility score and aggregate metrics."""


def probe_score(an):
    """0-100 visibility score for a single answer."""
    if not an.get("mentioned"):
        return 0
    s = 50
    s += round(20 * an.get("prominence", 0.0))
    if an.get("sentiment") == "positive":
        s += 20
    elif an.get("sentiment") == "negative":
        s -= 25
    if an.get("client_cited"):
        s += 10
    s = max(0, min(100, s))
    # A named mention that is the wrong entity, or that the engine admits it knows
    # nothing about, is not real visibility — cap it so the score stays honest.
    flags = an.get("flags", [])
    if any(f.startswith("identity_mismatch") for f in flags):
        s = min(s, 20)
    elif any(f.startswith("insufficient_info") for f in flags):
        s = min(s, 30)
    return s


def label(score):
    if score >= 70:
        return "ظاهر بقوة"
    if score >= 40:
        return "ظاهر جزئياً"
    if score > 0:
        return "ظهور ضعيف"
    return "غير مرئيّ"


def aggregate(probes):
    """probes: list of dicts with analysis fields + 'engine'."""
    n = len(probes)
    scores = [probe_score(p) for p in probes]
    overall = round(sum(scores) / n, 1) if n else 0.0

    client_mentions = sum(1 for p in probes if p.get("mentioned"))
    comp_mentions = sum(len(p.get("competitors", [])) for p in probes)
    denom = client_mentions + comp_mentions
    sov = round(100 * client_mentions / denom, 1) if denom else 0.0

    by_engine = {}
    for p in probes:
        by_engine.setdefault(p.get("engine", "?"), []).append(probe_score(p))
    per_engine = {e: round(sum(v) / len(v), 1) for e, v in by_engine.items()}

    return {
        "n": n,
        "overall": overall,
        "sov": sov,
        "per_engine": per_engine,
        "client_mentions": client_mentions,
        "comp_mentions": comp_mentions,
        "invisible": [p for p in probes if not p.get("mentioned")],
        "negative": [p for p in probes if p.get("sentiment") == "negative"],
        "flagged": [p for p in probes if p.get("flags")],
    }
