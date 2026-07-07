"""Render a Markdown visibility report from aggregated probes."""
import time
from collections import Counter

from alsada.config import REPORTS_DIR
from alsada.score import aggregate, probe_score, label


def _competitor_counts(probes):
    c = Counter()
    for p in probes:
        for comp in p.get("competitors", []):
            c[comp] += 1
    return c.most_common()


def render(client, probes, run_meta):
    agg = aggregate(probes)
    name = client.get("name", "?")
    lines = []
    lines.append("# تقرير الظهور في الذكاء الاصطناعي — %s" % name)
    lines.append("")
    lines.append("- المحرّك: **%s** (%s) · البرومبتات: **%d** · التاريخ: %s"
                 % (run_meta.get("engine"), run_meta.get("model"), agg["n"],
                    time.strftime("%Y-%m-%d %H:%M", time.localtime(run_meta.get("ts", time.time())))))
    lines.append("")
    lines.append("## الملخّص التنفيذي")
    lines.append("- **درجة الظهور الكلية: %.1f / 100** (%s)" % (agg["overall"], label(agg["overall"])))
    lines.append("- **حصّة الصوت مقابل المنافسين: %.1f%%** (ذُكرتَ في %d من %d، والمنافسون %d مرّة)"
                 % (agg["sov"], agg["client_mentions"], agg["n"], agg["comp_mentions"]))
    if agg["per_engine"]:
        lines.append("- حسب المحرّك: " + " · ".join("%s=%.1f" % (e, v) for e, v in agg["per_engine"].items()))
    lines.append("")

    # share of voice
    lines.append("## حصّة الصوت — من يهزمك")
    comps = _competitor_counts(probes)
    lines.append("| الطرف | مرّات الذكر |")
    lines.append("|---|---|")
    lines.append("| **%s (أنت)** | %d |" % (name, agg["client_mentions"]))
    for comp, cnt in comps:
        lines.append("| %s | %d |" % (comp, cnt))
    lines.append("")

    # invisibility
    lines.append("## أين أنت غير مرئيّ (%d برومبت)" % len(agg["invisible"]))
    if agg["invisible"]:
        for p in agg["invisible"]:
            comp = ("؛ يذكر بدلاً منك: " + "، ".join(p["competitors"])) if p["competitors"] else ""
            lines.append("- [%s] %s%s" % (p["prompt_id"], p["prompt_text"], comp))
    else:
        lines.append("- (ظاهر في كل البرومبتات ✔)")
    lines.append("")

    # misinformation / risk flags
    lines.append("## تنبيهات ومعلومات قد تكون خاطئة (%d)" % len(agg["flagged"]))
    if agg["flagged"]:
        for p in agg["flagged"]:
            lines.append("- [%s] %s" % (p["prompt_id"], p["prompt_text"]))
            for f in p["flags"]:
                lines.append("    - ⚠️ %s" % f)
            snippet = (p["answer"] or "")[:220].replace("\n", " ")
            lines.append("    - مقتطف: \"%s…\"" % snippet)
    else:
        lines.append("- (لا تنبيهات)")
    lines.append("")

    # negative sentiment
    if agg["negative"]:
        lines.append("## نبرة سلبية (%d)" % len(agg["negative"]))
        for p in agg["negative"]:
            lines.append("- [%s] %s" % (p["prompt_id"], p["prompt_text"]))
        lines.append("")

    # per-prompt detail
    lines.append("## تفصيل البرومبتات")
    lines.append("| # | البرومبت | الدرجة | الحالة | استشهاد بك | المنافسون |")
    lines.append("|---|---|---|---|---|---|")
    for p in probes:
        s = probe_score(p)
        lines.append("| %s | %s | %d | %s | %s | %s |" % (
            p["prompt_id"], (p["prompt_text"][:48]), s, label(s),
            "نعم" if p["client_cited"] else "—",
            "، ".join(p["competitors"]) if p["competitors"] else "—"))
    lines.append("")

    # recommendations
    lines.append("## توصيات فورية (للمرحلة 2 — إغلاق الحلقة)")
    if agg["invisible"]:
        lines.append("- أنشئ محتوى موثّقاً غنيّاً بالإحصاءات والاقتباسات للمواضيع التي تغيب عنها (اقتباس +41% · إحصائية +32%).")
    if agg["flagged"]:
        lines.append("- صحّح المعلومات الخاطئة: انشر بيانات مهيكلة (schema/llms.txt) وصفحات حقائق رسمية تردّ على ما تخطئه النماذج.")
    if agg["sov"] < 50:
        lines.append("- حصّة صوتك أقل من المنافسين — استهدف المصادر التي تستشهد بها النماذج (listicles/مراجعات/أدلّة) لرفع الذكر.")
    lines.append("")
    return "\n".join(lines), agg


def save(markdown, client, run_id):
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    safe = (client.get("name", "client")).replace(" ", "_")
    path = REPORTS_DIR / ("alsada_%s_%s.md" % (safe, run_id))
    path.write_text(markdown, encoding="utf-8")
    return path
