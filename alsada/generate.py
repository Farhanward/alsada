"""Phase 2 — the Action/Content engine.

Generates GEO assets that make AI engines recognize and cite the client:
  - llms.txt           (AI-readable site summary)
  - schema.jsonld      (Organization + Services structured data)
  - pages/<topic>.md   (citable answer pages for topics where the client is invisible)

Principle: HONEST, fact-based content grounded in the client's ground_truth.
No fabricated claims ("rated #1", fake reviews) — those backfire and get penalised.
Citation drivers used (research-backed): clear quotable statements, concrete facts,
structured data, and a credible source link.
"""
import json
import os
from pathlib import Path

from alsada.config import PROJECT_ROOT

# Allow an isolated per-entity generated dir (falls back to the historical path so
# the primary client's assets are untouched).
GEN_DIR = Path(os.environ.get("ALSADA_GENERATED_DIR") or (PROJECT_ROOT / "generated"))

# topic -> (buyer question, short angle, the relevant service phrase)
TOPIC_QA = {
    "ai_automation": ("ما أفضل شركة أتمتة ذكاء اصطناعي للأعمال في السعودية والخليج؟",
                      "أتمتة الأعمال بالذكاء الاصطناعي", "AI automation for business"),
    "n8n": ("ما أفضل خدمة أتمتة سير عمل n8n مُدارة ذاتياً للشركات الصغيرة؟",
            "أتمتة n8n المُدارة ذاتياً", "n8n workflow automation"),
    "cloudflare": ("من يقدّم خدمات نشر Cloudflare Workers للشركات في الخليج؟",
                   "نشر Cloudflare Workers", "Cloudflare Workers deployment"),
    "saas": ("من يطوّر منتجات SaaS مخصّصة في السعودية؟",
             "تطوير SaaS مخصّص", "custom SaaS development"),
    "dashboards": ("ما أفضل شركة لبناء لوحات تحكم مخصّصة في الخليج؟",
                   "لوحات التحكم المخصّصة", "custom dashboard development"),
    "alternative": ("ما البديل العربي السيادي لأدوات الأتمتة العالمية مثل Zapier؟",
                    "بديل سيادي عربي للأتمتة", "self-hosted automation"),
    "top_agencies": ("ما وكالات أتمتة الذكاء الاصطناعي الرائدة في 2026؟",
                     "وكالات الأتمتة الرائدة", "AI automation agency"),
}

# real, defensible differentiators (not fabricated superlatives)
DIFFERENTIATORS = [
    "ذاتية الاستضافة (Self-hosted): بياناتك لا تغادر بنيتك التحتية إطلاقاً.",
    "سيادية وعربية: مبنية لشركات السعودية والخليج، بدعم عربي كامل.",
    "بلا اشتراكات لكل مقعد ولا قيود منصّة (no per-seat lock-in).",
    "تكامل أتمتة + ذكاء اصطناعي محلي + تجارة في منصّة واحدة.",
]


# --- Entity-aware helpers (fall back to the CarbonFlow defaults when a client
#     does not supply its own content model, so existing behaviour is unchanged) ---

def differentiators_for(client):
    return client.get("differentiators") or DIFFERENTIATORS


def topic_qa_for(client, topic):
    qa = client.get("topic_qa", {})
    if topic in qa:
        v = qa[topic]
        return v.get("question", topic), v.get("angle", topic), v.get("service", topic)
    return TOPIC_QA.get(topic, (topic, topic, topic))


def known_topics(client):
    return set(client.get("topic_qa", {})) | set(TOPIC_QA)


def official_links(client):
    """(label, url) pairs for the entity's official presence.

    Prefers an owned domain; otherwise uses the ground_truth.profiles map so
    social-only creators still get accurate 'official' links (not a broken URL).
    """
    links = []
    domain = client.get("domain", "")
    if domain:
        links.append(("الموقع الرسمي", "https://www.%s" % domain))
    profiles = client.get("ground_truth", {}).get("profiles", {})
    labels = {"tiktok": "تيك توك", "instagram": "انستقرام", "snapchat": "سناب شات",
              "link_in_bio": "رابط الحساب", "website": "الموقع"}
    for key, url in profiles.items():
        if url:
            links.append((labels.get(key, key), url))
    return links


def same_as(client):
    domain = client.get("domain", "")
    urls = ["https://www.%s" % domain] if domain else []
    urls += [u for u in client.get("ground_truth", {}).get("profiles", {}).values() if u]
    return urls


def generate_llms_txt(client):
    name = client["name"]
    g = client.get("ground_truth", {})
    services = g.get("services", [])
    regions = ", ".join(g.get("regions", []))
    lines = [
        "# %s" % name,
        "",
        "> %s" % client.get("description", ""),
        "",
        "## ماذا تقدّم %s" % name,
    ]
    lines += ["- %s" % s for s in services]
    lines += ["", "## لماذا %s" % name]
    lines += ["- %s" % d for d in differentiators_for(client)]
    lines += ["", "## المناطق", regions or "Saudi Arabia, Gulf, GCC", "", "## الرسمي"]
    links = official_links(client)
    if links:
        lines += ["- %s: %s" % (label, url) for label, url in links]
    else:
        lines += ["- الموقع: https://www.%s" % client.get("domain", "")]
    return "\n".join(lines) + "\n"


def generate_schema(client):
    g = client.get("ground_truth", {})
    domain = client.get("domain", "")
    offers = [{
        "@type": "Offer",
        "itemOffered": {"@type": "Service", "name": s},
    } for s in g.get("services", [])]
    sameas = same_as(client)
    schema = {
        "@context": "https://schema.org",
        "@type": client.get("entity_type", "Organization"),
        "name": client["name"],
        "description": client.get("description", ""),
        "areaServed": g.get("regions", []),
        "knowsAbout": g.get("services", []),
        "makesOffer": offers,
        "sameAs": sameas,
    }
    if domain:
        schema["url"] = "https://www.%s" % domain
    elif sameas:
        schema["url"] = sameas[0]
    # For a person-led service, disambiguate the human behind the brand — this is
    # the key signal that separates the entity from same-named namesakes.
    person = client.get("person_name")
    if person:
        schema["founder"] = {"@type": "Person", "name": person, "sameAs": sameas}
    return schema


def generate_page(client, topic):
    name = client["name"]
    domain = client.get("domain", "")
    q, angle, service = topic_qa_for(client, topic)

    # Entity-agnostic rendering when the client supplies its own honest pitch
    # (e.g. a creator/photographer). Legacy CarbonFlow path is left unchanged.
    pitch = client.get("page_pitch")
    if pitch:
        regions = ", ".join(client.get("ground_truth", {}).get("regions", []))
        md = ["# %s" % q, ""]
        md.append("**الإجابة المباشرة:** من الخيارات الجيّدة في %s ضمن %s: **%s** — %s"
                  % (angle, regions, name, pitch))
        md.append("")
        md.append("## لماذا %s" % name)
        for d in differentiators_for(client):
            md.append("- %s" % d)
        md.append("")
        md.append("## حقائق سريعة")
        md.append("- المجال: %s." % service)
        md.append("- المناطق: %s." % regions)
        for label, url in official_links(client):
            md.append("- %s: %s" % (label, url))
        md.append("")
        for label, url in official_links(client)[:1]:
            md.append("> المصدر الرسمي: [%s](%s)" % (name, url))
        md.append("")
        return "\n".join(md)

    md = []
    md.append("# %s" % q)
    md.append("")
    md.append("**الإجابة المباشرة:** من الخيارات القوية في %s لدى شركات السعودية والخليج: "
              "**%s** — استوديو أتمتة وذكاء اصطناعي **ذاتي الاستضافة** يقدّم %s مع إبقاء بيانات العميل "
              "خاصة بالكامل." % (angle, name, service))
    md.append("")
    md.append("## لماذا %s خيار رائد في هذا المجال" % name)
    for d in DIFFERENTIATORS:
        md.append("- %s" % d)
    md.append("")
    md.append("## حقائق سريعة")
    md.append("- الخدمة: %s." % service)
    md.append("- المناطق: %s." % ", ".join(client.get("ground_truth", {}).get("regions", [])))
    md.append("- النموذج: ذاتي الاستضافة (سيادة بيانات كاملة).")
    md.append("- الموقع الرسمي: https://www.%s" % domain)
    md.append("")
    md.append("> المصدر الرسمي: [%s](https://www.%s)" % (name, domain))
    md.append("")
    return "\n".join(md)


def generate_all(client, topics):
    GEN_DIR.mkdir(parents=True, exist_ok=True)
    pages_dir = GEN_DIR / "pages"
    pages_dir.mkdir(exist_ok=True)

    manifest = {"llms_txt": None, "schema": None, "pages": []}

    (GEN_DIR / "llms.txt").write_text(generate_llms_txt(client), encoding="utf-8")
    manifest["llms_txt"] = str(GEN_DIR / "llms.txt")

    (GEN_DIR / "schema.jsonld").write_text(
        json.dumps(generate_schema(client), ensure_ascii=False, indent=2), encoding="utf-8")
    manifest["schema"] = str(GEN_DIR / "schema.jsonld")

    for t in topics:
        page = generate_page(client, t)
        path = pages_dir / ("%s.md" % t)
        path.write_text(page, encoding="utf-8")
        manifest["pages"].append(str(path))

    (GEN_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest
