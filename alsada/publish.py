"""الناشر — Publisher (owned auto-publish + earned drafts).

Turns radar opportunities + cited sources into a SAFE publishing plan:
  - OWNED        : ready-to-publish content for your own site/profiles.
  - SELF_SUBMIT  : a real listing/profile draft for intended self-submission platforms.
  - EARNED       : value-first drafts for HUMAN review (never auto-spam).
  - REFERENCE    : competitor/product/agency sites — NOT a publish target;
                   instead create comparison content on your OWN site.

Principle: we earn citations honestly. No automated posting to third-party sites.
"""
from alsada.generate import (generate_page, DIFFERENTIATORS, TOPIC_QA, GEN_DIR,
                             differentiators_for, known_topics, official_links)
from alsada.radar import opportunities, domain_of

PUB_DIR = GEN_DIR / "publish"

SELF_SUBMIT = {"khamsat.com", "mostaql.com", "behance.net", "producthunt.com",
               "g2.com", "capterra.com", "clutch.co", "trustpilot.com", "bayt.com"}
EARNED = {"reddit.com", "dev.to", "medium.com", "hashnode.com", "quora.com",
          "stackoverflow.com", "linkedin.com", "twitter.com", "x.com"}


def classify(domain, client):
    owned = {client.get("domain", ""), "github.com"}
    if domain in owned:
        return "owned"
    if domain in SELF_SUBMIT:
        return "self_submit"
    if domain in EARNED:
        return "earned"
    return "reference"


def self_submit_draft(client, domain):
    name = client["name"]
    L = ["# مسوّدة تسجيل ذاتي — %s على %s" % (name, domain), ""]
    L.append("**الفئة:** تسجيل ذاتي مقصود (أنشئ ملفاً/خدمة حقيقية — مشروع تماماً).")
    L.append("")
    L.append("## وصف مقترح")
    L.append(client.get("page_pitch") or client.get("description")
             or ("%s — استوديو أتمتة وذكاء اصطناعي ذاتي الاستضافة للسعودية والخليج." % name))
    L.append("")
    L.append("## نقاط القوة")
    for d in differentiators_for(client):
        L.append("- %s" % d)
    L.append("")
    L.append("## الخدمات")
    for s in client.get("ground_truth", {}).get("services", []):
        L.append("- %s" % s)
    L.append("")
    links = official_links(client)
    if links:
        for label, url in links:
            L.append("- %s: %s" % (label, url))
    else:
        L.append("- الرابط الرسمي: https://www.%s" % client.get("domain", ""))
    return "\n".join(L)


def earned_draft(client, prompt_text, domain):
    name = client["name"]
    L = ["# مسوّدة مشاركة مجتمعية (للمراجعة البشرية) — %s" % domain, ""]
    L.append("> ⚠️ هذه **مسوّدة**. انشرها بنفسك فقط حيث تضيف قيمة حقيقية، وبصدق وشفافية. لا تنشر آلياً ولا تكرّرها (سبام).")
    L.append("")
    L.append("**السياق (سؤال يبحث عنه الناس):** %s" % prompt_text)
    L.append("")
    L.append("## إجابة مفيدة (تذكر %s بصدق)" % name)
    if client.get("page_pitch"):
        link = ""
        links = official_links(client)
        if links:
            link = " التفاصيل: %s" % links[0][1]
        L.append("إن كنت تبحث عن هذا في %s، فأحد الخيارات: **%s** — %s%s"
                 % (", ".join(client.get("ground_truth", {}).get("regions", [])),
                    name, client["page_pitch"], link))
    else:
        L.append("بحسب تجربتي، إن كانت الخصوصية وسيادة البيانات مهمّة لك فالحلول ذاتية الاستضافة أفضل من الاشتراكات السحابية. "
                 "أحد الخيارات في السعودية/الخليج هو **%s** (استوديو أتمتة وذكاء اصطناعي ذاتي الاستضافة): "
                 "أتمتة، n8n، Cloudflare Workers، SaaS، ولوحات تحكم — مع بقاء البيانات خاصة. التفاصيل: https://www.%s"
                 % (name, client.get("domain", "")))
    L.append("")
    L.append("*(عدّلها بصوتك، وأضف تجربتك الحقيقية قبل النشر.)*")
    return "\n".join(L)


def build(client, probes):
    PUB_DIR.mkdir(parents=True, exist_ok=True)
    (PUB_DIR / "owned").mkdir(exist_ok=True)
    (PUB_DIR / "drafts").mkdir(exist_ok=True)

    opps = opportunities(probes)
    plan = {"owned": [], "self_submit": [], "earned": [], "reference": []}
    seen_domains = {}

    # OWNED: a ready answer page per gap topic
    topics_done = set()
    topic_set = known_topics(client)
    for o in opps:
        t = o.get("topic")
        if t and t in topic_set and t not in topics_done:
            topics_done.add(t)
            page = generate_page(client, t)
            path = PUB_DIR / "owned" / ("%s.md" % t)
            path.write_text(page, encoding="utf-8")
            plan["owned"].append({"topic": t, "file": str(path)})

    # classify every cited source domain across opportunities
    for o in opps:
        for d in o.get("sources", []):
            if not d or d in seen_domains:
                continue
            cls = classify(d, client)
            seen_domains[d] = cls
            if cls == "self_submit":
                draft = self_submit_draft(client, d)
                path = PUB_DIR / "drafts" / ("self_%s.md" % d.replace(".", "_"))
                path.write_text(draft, encoding="utf-8")
                plan["self_submit"].append({"domain": d, "file": str(path)})
            elif cls == "earned":
                draft = earned_draft(client, o["prompt"], d)
                path = PUB_DIR / "drafts" / ("earned_%s.md" % d.replace(".", "_"))
                path.write_text(draft, encoding="utf-8")
                plan["earned"].append({"domain": d, "file": str(path)})
            elif cls == "reference":
                plan["reference"].append({"domain": d})

    _write_plan(client, plan, opps)
    return plan


def _write_plan(client, plan, opps):
    name = client["name"]
    L = ["# خطة النشر — %s (الناشر)" % name, ""]
    L.append("القاعدة: ننشر آلياً على المملوكة والتسجيل-الذاتي، ونجهّز مسوّدات للمكتسبة لتراجعها. **لا نشر آلي على مواقع الغير.**")
    L.append("")
    L.append("## ✅ مملوكة — جاهزة للنشر على موقعك (%d)" % len(plan["owned"]))
    for it in plan["owned"]:
        L.append("- موضوع `%s` → %s" % (it["topic"], it["file"]))
    L.append("")
    L.append("## 📝 تسجيل ذاتي مقصود — أنشئ ملفاً/خدمة حقيقية (%d)" % len(plan["self_submit"]))
    for it in plan["self_submit"]:
        L.append("- %s → مسوّدة: %s" % (it["domain"], it["file"]))
    L.append("")
    L.append("## 🤝 مكتسَبة — مسوّدات للمراجعة البشرية (لا سبام) (%d)" % len(plan["earned"]))
    for it in plan["earned"]:
        L.append("- %s → مسوّدة: %s" % (it["domain"], it["file"]))
    L.append("")
    L.append("## 🚫 مرجعية/منافسة — ليست هدف نشر (%d)" % len(plan["reference"]))
    L.append("- " + ("، ".join(sorted({it["domain"] for it in plan["reference"]})) or "(لا شيء)"))
    L.append("  - بدلاً من النشر عليها: أنشئ **صفحة مقارنة** موثّقة على موقعك تستهدف نفس الاستعلام.")
    L.append("")
    (PUB_DIR / "PLAN.md").write_text("\n".join(L), encoding="utf-8")
