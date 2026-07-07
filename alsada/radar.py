"""الرادار — GEO Competitive Intelligence.

Works in parallel with AL-SADA (no waiting for re-crawl). From a probe run it answers:
  - WHO wins in AI answers (competitor standings + share-of-voice)
  - WHICH sources the AI cites (the AI-trusted sources to target / get mentioned on)
  - WHERE the opportunities are (per query you're invisible in: who to beat + where)
"""
from collections import Counter
from urllib.parse import urlparse


def domain_of(url):
    try:
        net = urlparse(url).netloc.lower()
        return net[4:] if net.startswith("www.") else net
    except Exception:
        return ""


def competitor_standings(probes):
    comp = Counter()
    for p in probes:
        for c in p.get("competitors", []):
            comp[c] += 1
    client_mentions = sum(1 for p in probes if p.get("mentioned"))
    return comp.most_common(), client_mentions


def cited_sources(probes):
    dom = Counter()
    for p in probes:
        for u in p.get("citations", []):
            d = domain_of(u)
            if d:
                dom[d] += 1
    return dom.most_common()


def opportunities(probes):
    opps = []
    for p in probes:
        if p.get("mentioned"):
            continue
        opps.append({
            "prompt_id": p.get("prompt_id"),
            "prompt": p.get("prompt_text"),
            "topic": p.get("topic"),
            "competitors": list(p.get("competitors", [])),
            "sources": sorted({domain_of(u) for u in p.get("citations", []) if domain_of(u)}),
        })
    return opps


def _recommend(opp):
    if opp["sources"]:
        return "اسعَ لذكرٍ/استشهاد على: " + "، ".join(opp["sources"])
    if opp["competitors"]:
        return "أنشئ محتوى مقارنة موثّقاً يتفوّق على: " + "، ".join(opp["competitors"])
    return "أنشئ صفحة مرجعية موثّقة (إحصاءات + اقتباسات) لهذا الموضوع."


def render(client, probes, run_meta):
    name = client.get("name", "?")
    standings, client_mentions = competitor_standings(probes)
    sources = cited_sources(probes)
    opps = opportunities(probes)

    L = []
    L.append("# رادار المنافسين في الذكاء الاصطناعي — %s" % name)
    L.append("")
    L.append("- المحرّك: **%s** (%s) · البرومبتات: %d · التاريخ من التشغيل: %s"
             % (run_meta.get("engine"), run_meta.get("model"), len(probes), run_meta.get("run_id")))
    L.append("")

    L.append("## من يفوز (ترتيب الذكر)")
    L.append("| # | الطرف | مرّات الذكر |")
    L.append("|---|---|---|")
    rows = [(name + " (أنت)", client_mentions)] + [(c, n) for c, n in standings]
    rows.sort(key=lambda x: x[1], reverse=True)
    for i, (who, n) in enumerate(rows, 1):
        star = " ⭐" if who.endswith("(أنت)") else ""
        L.append("| %d | %s%s | %d |" % (i, who, star, n))
    L.append("")

    L.append("## المصادر التي يثق بها الذكاء (استهدفها)")
    if sources:
        L.append("| المصدر | مرّات الاستشهاد |")
        L.append("|---|---|")
        for d, n in sources:
            L.append("| %s | %d |" % (d, n))
    else:
        L.append("- (لم تُلتقط مصادر في هذا التشغيل — استخدم محرّك بحث ويب مع التقاط الاستشهادات)")
    L.append("")

    L.append("## الفرص (حيث أنت غائب: من تهزم وأين)")
    if opps:
        for o in opps:
            beat = ("؛ المنافسون: " + "، ".join(o["competitors"])) if o["competitors"] else ""
            L.append("- [%s] %s%s" % (o["prompt_id"], o["prompt"], beat))
            L.append("    - 🎯 %s" % _recommend(o))
    else:
        L.append("- (ظاهر في كل البرومبتات ✔)")
    L.append("")
    return L and "\n".join(L)
