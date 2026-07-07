"""Phase 2 — re-measurement: compare two runs to PROVE movement (before -> after).

Shows: change in visibility score and share-of-voice, prompts that went
invisible -> mentioned (and vice-versa), score improvements, and
misinformation flags that were resolved or newly appeared.
"""
from alsada.score import aggregate, probe_score, label


def _by_id(probes):
    return {p["prompt_id"]: p for p in probes}


def compare(base_probes, head_probes):
    ab, ah = aggregate(base_probes), aggregate(head_probes)
    b, h = _by_id(base_probes), _by_id(head_probes)

    gained, lost, improved, declined = [], [], [], []
    for pid, hp in h.items():
        bp = b.get(pid)
        if not bp:
            continue
        was, now = bp.get("mentioned"), hp.get("mentioned")
        if not was and now:
            gained.append(hp)
        elif was and not now:
            lost.append(hp)
        else:
            ds = probe_score(hp) - probe_score(bp)
            if ds > 0:
                improved.append((hp, ds))
            elif ds < 0:
                declined.append((hp, ds))

    resolved_flags = [h[pid] for pid in h
                      if b.get(pid) and b[pid].get("flags") and not h[pid].get("flags")]
    new_flags = [h[pid] for pid in h
                 if h[pid].get("flags") and b.get(pid) and not b[pid].get("flags")]

    return {
        "base": ab, "head": ah,
        "d_overall": round(ah["overall"] - ab["overall"], 1),
        "d_sov": round(ah["sov"] - ab["sov"], 1),
        "gained": gained, "lost": lost,
        "improved": improved, "declined": declined,
        "resolved_flags": resolved_flags, "new_flags": new_flags,
    }


def _arrow(d):
    return "▲" if d > 0 else ("▼" if d < 0 else "—")


def render(client, base_meta, head_meta, cmp):
    name = client.get("name", "?")
    L = []
    L.append("# تقرير الحركة (قبل ← بعد) — %s" % name)
    L.append("")
    L.append("- **قبل:** %s (%s) — درجة %.1f" % (base_meta.get("engine"), base_meta.get("run_id"), cmp["base"]["overall"]))
    L.append("- **بعد:** %s (%s) — درجة %.1f" % (head_meta.get("engine"), head_meta.get("run_id"), cmp["head"]["overall"]))
    L.append("")
    L.append("## المحصّلة")
    L.append("- درجة الظهور: %.1f ← %.1f  (%s %+.1f)" % (
        cmp["base"]["overall"], cmp["head"]["overall"], _arrow(cmp["d_overall"]), cmp["d_overall"]))
    L.append("- حصّة الصوت: %.1f%% ← %.1f%%  (%s %+.1f)" % (
        cmp["base"]["sov"], cmp["head"]["sov"], _arrow(cmp["d_sov"]), cmp["d_sov"]))
    L.append("")
    L.append("## ✅ ظهرتَ حيث كنت غائباً (%d)" % len(cmp["gained"]))
    for p in cmp["gained"]:
        L.append("- [%s] %s" % (p["prompt_id"], p["prompt_text"]))
    if not cmp["gained"]:
        L.append("- (لا جديد بعد — امنح النماذج وقتاً لإعادة الزحف)")
    L.append("")
    if cmp["lost"]:
        L.append("## ⚠️ تراجعتَ (اختفيت) (%d)" % len(cmp["lost"]))
        for p in cmp["lost"]:
            L.append("- [%s] %s" % (p["prompt_id"], p["prompt_text"]))
        L.append("")
    if cmp["improved"]:
        L.append("## ↑ تحسّنت درجتك (%d)" % len(cmp["improved"]))
        for p, ds in cmp["improved"]:
            L.append("- [%s] %s (%+d)" % (p["prompt_id"], p["prompt_text"], ds))
        L.append("")
    if cmp["resolved_flags"]:
        L.append("## 🛠️ معلومات خاطئة صُحّحت (%d)" % len(cmp["resolved_flags"]))
        for p in cmp["resolved_flags"]:
            L.append("- [%s] %s" % (p["prompt_id"], p["prompt_text"]))
        L.append("")
    if cmp["new_flags"]:
        L.append("## ⚠️ معلومات خاطئة جديدة (%d)" % len(cmp["new_flags"]))
        for p in cmp["new_flags"]:
            L.append("- [%s] %s" % (p["prompt_id"], p["prompt_text"]))
        L.append("")
    return "\n".join(L)
