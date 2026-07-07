# -*- coding: utf-8 -*-
"""Generate a 30-article professional blog package for carbonflows.store.

Real, GEO-optimized articles across 4 tracks (CarbonFlow news, Automation,
Programming, AI). Each article: unique angle + Article JSON-LD schema + a
CarbonFlow CTA, staggered publish dates (3/week). Output is STAGED locally in
C:\\Projects\\alsada\\blog\\staged\\ and manifested in blog\\schedule.json —
ready to publish the moment safe deploy access to the live site exists.
"""
from __future__ import annotations

import datetime
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "blog" / "staged"
MANIFEST = ROOT / "blog" / "schedule.json"
SITE = "https://www.carbonflows.store"
EMAIL = "far7an.o88@gmail.com"
PHONE = "+966504211844"

# Canonical CarbonFlow entity — sameAs to the official social profiles disambiguates
# this CarbonFlow (Saudi/Gulf AI automation) from the climate-tech companies of the
# same name that AI engines otherwise confuse it with.
ORG = {
    "@type": "Organization",
    "@id": SITE + "/#organization",
    "name": "CarbonFlow",
    "alternateName": ["CarbonFlow Store", "كاربون فلو"],
    "url": SITE,
    "description": ("Self-hosted AI automation, SaaS development, n8n workflow automation, "
                    "Cloudflare Workers deployment and custom dashboards for businesses in "
                    "Saudi Arabia and the Gulf."),
    "areaServed": ["SA", "AE", "KW", "BH", "QA", "OM"],
    "sameAs": [
        "https://mastodon.social/@carbonflows",
        "https://bsky.app/profile/carbonflows.bsky.social",
        "https://www.linkedin.com/in/carbonflows",
    ],
}

# (category, slug, title, dek, [section (heading, body) ...], takeaway)
TOPICS = [
    ("news", "carbonflow-22-enterprise-platforms",
     "CarbonFlow Ships 22 On-Prem AI Platforms for Saudi & Gulf Businesses",
     "We turned 22 local AI tools into production-grade platforms with unified APIs, observability, and 419 automated tests — all running on your own infrastructure.",
     [("What changed", "Every tool became a real service: key-based auth, request guards, structured JSON logging, and p50/p95/p99 latency metrics. Nothing leaves your infrastructure."),
      ("Why on-prem matters in the Gulf", "For regulated SMEs in Saudi Arabia, Qatar, Kuwait and the wider GCC, data residency is not optional. Self-hosted AI keeps client data private by design."),
      ("What is inside", "An AI output judge, a data-sanitization gateway, an agent immune system against prompt injection, serverless licensing, and a compliance auditor — among others.")],
     "If you want AI without leaking your data, on-prem is the sober choice. Talk to us about adopting any of these platforms."),
    ("ai", "prompt-injection-owasp-number-one",
     "Prompt Injection Is OWASP's #1 LLM Risk — and Most Agents Have No Defense",
     "AI agents that call tools are exposed to prompt injection. Here is how a runtime immune system stops it before execution.",
     [("The attack", "Malicious text in a document, email, or web page can hijack an agent into leaking secrets or running destructive commands. It is the #1 risk in OWASP's LLM Top 10."),
      ("A defense that actually works", "Inspect the full agent loop — inputs, memory, tool calls, and outputs — and return ALLOW / REVIEW / QUARANTINE / BLOCK with a sanitized quarantine. Benchmarked at ~98% F1 on 15,919 real attacks."),
      ("For teams deploying agents", "If you run AI agents in production, add this layer before the model ever touches a tool.")],
     "Deploying AI agents in KSA or the Gulf? You need an immune layer, not just a prompt."),
    ("automation", "n8n-self-hosted-vs-zapier-gulf",
     "Self-Hosted n8n vs Zapier & Make: What Gulf SMEs Should Actually Pick",
     "Per-seat SaaS automation gets expensive and locks your data outside your borders. Here is the honest trade-off with self-hosted n8n.",
     [("The cost curve", "Zapier and Make price per task/seat. At scale, a self-hosted n8n instance you own is far cheaper and has no per-run ceiling."),
      ("Data sovereignty", "Self-hosting keeps every workflow and payload inside your infrastructure — critical for Saudi and GCC compliance."),
      ("When SaaS still wins", "For a tiny team with a handful of zaps, managed SaaS is fine. Past that, ownership pays off fast.")],
     "We deploy and manage self-hosted n8n for businesses across the Gulf."),
    ("programming", "cloudflare-workers-edge-deployment",
     "Why We Deploy on Cloudflare Workers (Edge) for Middle East Companies",
     "Edge runtimes cut latency for regional users and remove server maintenance. Here is how we ship production apps on Workers.",
     [("Latency where your users are", "Workers run at Cloudflare's edge, close to users in Riyadh, Jeddah, Doha and beyond — no cold origin round-trips."),
      ("No servers to babysit", "No VMs, no patching. You get atomic, versioned deploys with instant rollback."),
      ("Real apps, not toys", "TypeScript, D1, R2 and KV support full SaaS — marketing sites, dashboards, and marketplaces.")],
     "Need an app deployed on Cloudflare Workers? We build and ship it end-to-end."),
    ("ai", "data-sanitization-gateway-before-ai",
     "Your Team Is Pasting Company Data Into ChatGPT. A DLP Gateway Fixes That.",
     "A sanitization gateway sits between your staff and any AI tool, masking secrets before anything leaves.",
     [("The silent leak", "Employees paste customer data, API keys, and payment secrets into public AI tools every day."),
      ("How the gateway works", "It detects emails, phone numbers, API keys and payment keys (Stripe/Moyasar), replaces them with safe tokens, and returns ALLOW / REVIEW / QUARANTINE / BLOCK. Zero leaks across 47,757 stress checks."),
      ("Enable AI, safely", "Your team keeps its productivity; your data never leaves in the clear.")],
     "Let your team use AI without the leak risk. We deploy the gateway on-prem."),
    ("news", "geo-generative-engine-optimization-carbonflow",
     "GEO: How to Get ChatGPT and Gemini to Recommend Your Business",
     "Search is shifting from links to AI answers. Generative Engine Optimization (GEO) is how brands stay visible.",
     [("What GEO is", "Measuring and improving how ChatGPT, Gemini and Perplexity describe your brand — then producing the assets that make them cite you."),
      ("Why it matters now", "A growing share of buyers start with an AI assistant, not a search box. If the AI does not mention you, you are invisible."),
      ("The honest timeline", "GEO reputation is earned over weeks through indexed, authoritative content — not overnight.")],
     "We run GEO programs that measure and lift your visibility in AI engines."),
    ("automation", "workflow-automation-roi-smes",
     "The Real ROI of Workflow Automation for a 10-Person Team",
     "Automation is not about replacing people — it is about deleting the repetitive work that drains them.",
     [("Start with the boring 20%", "Invoicing, data entry, lead routing, report generation. Automate those first for the fastest payback."),
      ("Measure hours, not hype", "Track the hours reclaimed per week. A single automated workflow often pays for itself in a month."),
      ("Keep humans in the loop", "The best automations escalate edge cases to a person instead of failing silently.")],
     "We map your busywork and automate the highest-ROI workflows first."),
    ("programming", "custom-saas-vs-off-the-shelf",
     "Custom SaaS vs Off-the-Shelf: When Building Your Own Pays Off",
     "Off-the-shelf tools are fast to start but slow to fit. Here is when a custom build is the right call.",
     [("The fit problem", "Generic SaaS forces your process into someone else's model. Custom software fits your actual workflow."),
      ("Own your data and roadmap", "A custom build means no per-seat lock-in and no vendor deciding your feature priorities."),
      ("Ship in weeks, not years", "With modern edge stacks, a focused MVP ships in 6–12 weeks.")],
     "We build custom SaaS for Saudi and Gulf businesses, end-to-end."),
    ("ai", "self-hosted-ai-data-sovereignty",
     "Self-Hosted AI and Data Sovereignty: A Gulf Compliance Primer",
     "AI regulation is coming. Keeping models and data on your own infrastructure is the safest posture.",
     [("Where your data lives", "Cloud AI sends your prompts abroad. Self-hosted AI keeps them inside your borders and your control."),
      ("A sovereign router", "Route each request to local or cloud based on sensitivity — and hard-block sending sensitive data to the cloud."),
      ("Auditable by design", "Signed, tamper-evident logs make compliance reviews straightforward.")],
     "We deploy self-hosted AI with a sovereign router for regulated teams."),
    ("news", "ai-output-judge-hallucination-secrets",
     "Would You Let AI Reply to Customers Without a Safety Check?",
     "An AI output judge inspects every model answer before you use it — evidence, secrets, and injection.",
     [("Three checks before you ship", "Is it backed by evidence or hallucinated? Does it leak secrets? Does it contain unsafe instructions?"),
      ("A clear verdict", "PASS / REVIEW / BLOCK, with a tamper-proof signed audit log — fully on-prem."),
      ("For support and content teams", "Any team embedding AI into customer-facing text needs this guardrail.")],
     "Add a judge before your AI ships to customers. We deploy it on-prem."),
    ("automation", "rpa-vs-api-automation",
     "RPA vs API-First Automation: Stop Clicking, Start Integrating",
     "Screen-scraping bots break constantly. API-first automation is more reliable and cheaper to maintain.",
     [("Why RPA is fragile", "UI bots break every time a screen changes. Maintenance eats the savings."),
      ("API-first wins", "Connecting systems by their APIs is stable, testable, and observable."),
      ("A pragmatic mix", "Use APIs where they exist; reserve UI automation for legacy systems with no other door.")],
     "We build API-first automation that does not break every week."),
    ("programming", "typescript-edge-stack-2026",
     "The TypeScript Edge Stack We Use to Ship in 2026",
     "A modern, boring, reliable stack: TypeScript, React, edge runtimes, and typed data.",
     [("Boring is good", "We favor proven tools over hype. Fewer surprises in production."),
      ("Typed end-to-end", "Types from the database to the UI catch whole classes of bugs before deploy."),
      ("Edge by default", "Deploying to the edge means low latency for regional users and simple ops.")],
     "Building a product? We ship on a modern, typed, edge-first stack."),
    ("ai", "rag-that-works-in-production",
     "RAG That Actually Works in Production (Not a Demo)",
     "Retrieval-augmented generation is easy to demo and hard to ship. Here is what separates the two.",
     [("Retrieval quality first", "Most RAG failures are retrieval failures. Invest in chunking, indexing, and evals."),
      ("Ground every claim", "Answers must cite their sources so users — and auditors — can verify them."),
      ("Measure, do not guess", "Track recall and answer quality with a real evaluation set.")],
     "We build production RAG with real evals — not a wrapper around a prompt."),
    ("news", "serverless-licensing-ed25519",
     "Serverless Software Licensing With Ed25519 — No License Server Needed",
     "Issue and verify licenses locally, bound to a device fingerprint, with no phone-home server.",
     [("How it works", "Signed license codes verify offline against a device fingerprint. No server, no downtime."),
      ("Proven at scale", "12,000 licenses verified, 705 tampering attempts caught, sub-millisecond p99."),
      ("For software vendors", "Ship licensed desktop and business apps without running licensing infrastructure.")],
     "Selling software? We add serverless licensing that just works."),
    ("automation", "whatsapp-telegram-customer-agent",
     "A Local Customer-Messaging Agent for WhatsApp and Telegram",
     "Automate first-response on your channels while keeping customer data on your own server.",
     [("Triage, do not spam", "Classify intent, extract order numbers, and decide REPLY / ESCALATE / CREATE ORDER."),
      ("Privacy by design", "Emails and phone numbers are sanitized before any processing or logging."),
      ("Human handoff", "Complex cases escalate to a person with a safe summary.")],
     "We deploy a local messaging agent for your storefront or clinic."),
    ("programming", "custom-dashboards-that-drive-decisions",
     "Custom Dashboards That Drive Decisions, Not Vanity Metrics",
     "A good dashboard answers a decision. Here is how we design ones people actually use.",
     [("Start from the decision", "Define what the viewer must decide, then show only the data that supports it."),
      ("Dense but readable", "Pack signal without clutter. Add alerts and export paths."),
      ("Trusted data only", "Connect vetted sources so the numbers are believable.")],
     "We build custom business dashboards for Saudi and Gulf teams."),
    ("ai", "on-device-arabic-ai-assistants",
     "On-Device Arabic AI Assistants: Private, Fast, and Sovereign",
     "Local document assistants that speak Arabic and keep every file on the user's machine.",
     [("Arabic-first", "Full Arabic support, not an afterthought translation."),
      ("Local and private", "Documents never leave the device; no cloud upload."),
      ("Practical use cases", "Contracts, reports, and knowledge bases the assistant can answer over.")],
     "We build Arabic-first, on-device AI assistants for your documents."),
    ("automation", "indexnow-faster-ai-search-visibility",
     "IndexNow: The Fastest Way to Get New Pages Into AI Search",
     "Bing powers ChatGPT search. IndexNow tells it to crawl your new pages immediately.",
     [("Why it matters for GEO", "Faster indexing means AI engines find your content sooner."),
      ("How to wire it", "Host a key file, then POST your URLs to the IndexNow endpoint on every publish."),
      ("Automate it", "Ping IndexNow automatically whenever you ship new content.")],
     "We wire IndexNow and GEO automation so your content gets found faster."),
    ("news", "compliance-auditor-ai-platforms",
     "A Compliance Auditor for On-Prem AI Platforms",
     "Check AI platforms against data-class, region, and audit-log requirements before they go live.",
     [("What it checks", "Data classification, cloud allowance, region, PII handling, and tool allowlists."),
      ("A clear verdict", "PASS / REVIEW / BLOCK, with Arabic findings and remediation steps."),
      ("For regulated buyers", "Prove your AI stack meets policy before deployment.")],
     "We audit AI platforms for compliance on your own infrastructure."),
    ("programming", "edge-databases-d1-r2-kv",
     "Edge Data: When to Use D1, R2, and KV on Cloudflare",
     "Three storage primitives, three jobs. Picking the right one keeps your app fast and cheap.",
     [("D1 for relational", "SQLite at the edge for structured data and queries."),
      ("R2 for objects", "S3-compatible storage with no egress fees — great for files and media."),
      ("KV for hot config", "Low-latency key-value for flags and small hot data.")],
     "We architect edge data stacks that stay fast and affordable."),
    ("ai", "ai-agents-that-do-not-go-rogue",
     "How to Ship AI Agents That Do Not Go Rogue",
     "Autonomy without guardrails is a liability. Here is the control layer serious teams add.",
     [("Gate every action", "Pass each tool intent through an allow/deny policy before it runs."),
      ("Signed audit trail", "Log every decision in a tamper-evident ledger."),
      ("Fail safe", "Block destructive commands by default; escalate the ambiguous ones.")],
     "We add an action-gating control layer to your AI agents."),
    ("automation", "marketing-ops-automation-gulf",
     "Marketing-Ops Automation for Gulf SMEs: SEO, Content, and Radar",
     "Automate the repetitive parts of marketing so your team focuses on strategy.",
     [("Opportunity radar", "Find the content and SEO gaps where competitors beat you."),
      ("Safe publishing", "A no-spam publishing plan that earns citations honestly."),
      ("Measure movement", "Prove before/after lift with real numbers.")],
     "We automate marketing-ops with an honest, no-spam playbook."),
    ("programming", "shipping-mvp-in-eight-weeks",
     "How We Ship a Real MVP in 8 Weeks",
     "Discovery, design, and build — with weekly demos and no surprises.",
     [("Two weeks of discovery", "Pressure-test the idea, map the user, scope the MVP."),
      ("Design you can test", "High-fidelity prototypes in front of users before code."),
      ("Build in the open", "Weekly demos and a shared board — no black boxes.")],
     "Have an idea? We ship a defensible MVP in weeks."),
    ("ai", "evaluating-llms-for-your-use-case",
     "Evaluating LLMs for Your Use Case (Beyond the Leaderboard)",
     "Benchmarks do not predict your results. Build a small eval set that reflects your real task.",
     [("Your data, your eval", "Score models on your actual prompts and outputs."),
      ("Cost and latency count", "The best model is the one that fits your budget and speed."),
      ("Re-evaluate over time", "Models change; keep measuring.")],
     "We help you pick and evaluate the right model for your task."),
    ("news", "carbonflow-services-overview-2026",
     "CarbonFlow Services in 2026: From Protection to Growth",
     "A single studio for self-hosted AI, automation, SaaS, and GEO — built for the Gulf.",
     [("Protection", "Output judge, DLP gateway, agent immune system, compliance auditor."),
      ("Build", "Custom SaaS, dashboards, n8n automation, Cloudflare Workers deployment."),
      ("Growth", "GEO visibility and marketing-ops automation.")],
     "One studio, end-to-end. Tell us your goal and we will scope it."),
    ("automation", "no-code-vs-pro-code-automation",
     "No-Code vs Pro-Code Automation: A Practical Boundary",
     "No-code is great until it is not. Here is where to draw the line.",
     [("No-code for speed", "Simple, stable workflows ship fastest with no-code tools."),
      ("Pro-code for control", "Complex logic, performance, and testing need real code."),
      ("Hybrid is normal", "Use no-code for the edges and code for the core.")],
     "We blend no-code and pro-code so you get speed and control."),
    ("programming", "observability-for-small-teams",
     "Observability for Small Teams: Logs, Metrics, and Alerts That Matter",
     "You cannot fix what you cannot see. Here is a lean observability setup.",
     [("Structured logs", "JSON logs you can actually query."),
      ("The three latencies", "Track p50/p95/p99 to catch tail problems."),
      ("Alert on symptoms", "Page on user-facing symptoms, not noisy internals.")],
     "We add lean observability so you catch issues before customers do."),
    ("ai", "geo-vs-seo-what-changes",
     "GEO vs SEO: What Changes When AI Answers the Question",
     "SEO ranks links; GEO shapes AI answers. The overlap is real, and so are the differences.",
     [("Same foundation", "Crawlable, authoritative, well-structured content still wins."),
      ("New signals", "AI engines value clear, citable answers and structured data."),
      ("Measure differently", "Track mentions and share-of-voice in AI answers, not just rankings.")],
     "We run both SEO and GEO so you win links and AI answers."),
    ("news", "why-on-prem-beats-per-seat-saas",
     "Why On-Prem Beats Per-Seat SaaS for Growing Gulf Businesses",
     "Per-seat pricing punishes growth. Owning your stack rewards it.",
     [("The seat tax", "Every new hire raises your SaaS bill. On-prem does not."),
      ("Data stays home", "Your data lives on your infrastructure, under your policy."),
      ("Predictable cost", "Own the stack; pay for infrastructure, not seats.")],
     "Outgrowing per-seat SaaS? We move you to owned, on-prem software."),
    ("automation", "e-commerce-automation-saudi-stores",
     "E-Commerce Automation for Saudi Online Stores: Orders, Support, Stock",
     "From order handling to support triage to stock alerts — automate the operations that scale a store.",
     [("Order-to-fulfilment", "Automate order confirmation, routing, and status updates so nothing slips."),
      ("Support that scales", "Triage customer messages, answer FAQs, and escalate refunds to a human."),
      ("Stock and reorder alerts", "Get notified before you run out, and automate reorder drafts.")],
     "Running a Saudi online store? We automate its operations end-to-end."),
]

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&'
         'family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">')

CSS = """
:root{--bg:oklch(0.075 0.01 250);--fg:oklch(0.94 0.006 248);--card:oklch(0.125 0.012 250);
--muted:oklch(0.72 0.014 247);--accent:oklch(0.74 0.13 205);--accent-fg:oklch(0.075 0.012 250);
--border:oklch(1 0 0 / 0.10);--radius:0.85rem}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font-family:"Plus Jakarta Sans",ui-sans-serif,system-ui,sans-serif;line-height:1.7;-webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration:none}
.wrap{max-width:1080px;margin:0 auto;padding:0 24px}
header.site{position:sticky;top:0;z-index:20;backdrop-filter:blur(14px);background:oklch(0.075 0.01 250 / 0.82);border-bottom:1px solid var(--border)}
.nav{display:flex;align-items:center;justify-content:space-between;height:66px}
.brand{display:flex;align-items:center;gap:11px;font-weight:800;font-size:1.15rem;letter-spacing:-.02em}
.brand .logo{width:30px;height:30px;border-radius:9px;background:linear-gradient(135deg,var(--accent),oklch(0.55 0.15 255));display:grid;place-items:center;color:var(--accent-fg);font-weight:900;font-size:1rem}
.nav a.link{color:var(--muted);font-size:.92rem;font-weight:600;margin-left:24px;transition:color .15s}
.nav a.link:hover{color:var(--fg)}
.nav .cta{background:var(--accent);color:var(--accent-fg);padding:9px 18px;border-radius:999px;font-weight:700;margin-left:24px}
footer.site{border-top:1px solid var(--border);padding:48px 0;color:var(--muted);font-size:.92rem;margin-top:40px}
footer.site a{color:var(--accent)}
.eyebrow{font-family:"JetBrains Mono",monospace;font-size:.78rem;letter-spacing:.14em;text-transform:uppercase;color:var(--accent)}
article{padding:56px 0 20px}
article .meta{display:flex;gap:14px;align-items:center;flex-wrap:wrap}
.badge{font-family:"JetBrains Mono",monospace;font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;color:var(--accent);border:1px solid var(--accent);border-radius:6px;padding:4px 9px}
.date{font-family:"JetBrains Mono",monospace;font-size:.8rem;color:var(--muted)}
article h1{font-size:clamp(2.1rem,4.6vw,3.1rem);line-height:1.08;letter-spacing:-.03em;margin:20px 0 14px;font-weight:800;max-width:820px}
article .dek{color:var(--muted);font-size:1.22rem;max-width:720px;margin-bottom:10px}
.prose{max-width:720px}
.prose h2{font-size:1.55rem;margin:2.6rem 0 .6rem;letter-spacing:-.01em;font-weight:700}
.prose p{font-size:1.08rem;color:oklch(0.88 0.006 248)}
.prose a{color:var(--accent);text-decoration:underline;text-underline-offset:3px}
.cta{margin:52px 0 8px;padding:30px;border:1px solid var(--accent);border-radius:var(--radius);background:oklch(0.74 0.13 205 / 0.07)}
.cta strong{font-size:1.18rem;display:block;margin-bottom:8px}
.cta .c{color:var(--muted)}.cta .c a{color:var(--accent)}
.back{display:inline-block;margin:8px 0 0;color:var(--muted);font-weight:600}
.back:hover{color:var(--accent)}
@media(max-width:640px){.nav a.link:not(.cta){display:none}}
"""

HEADER = ('<header class="site"><div class="wrap nav">'
          '<a href="/" class="brand"><span class="logo">C</span>CarbonFlow</a>'
          '<nav><a class="link" href="/services">Services</a>'
          '<a class="link" href="/blog">Blog</a>'
          '<a class="link" href="/ai-automation-for-business">AI Automation</a>'
          '<a class="link cta" href="/contact">Contact</a></nav></div></header>')

FOOTER = ('<footer class="site"><div class="wrap">'
          '<strong>CarbonFlow</strong> — self-hosted AI automation &amp; software studio for Saudi Arabia and the Gulf.<br>'
          f'<a href="mailto:{EMAIL}">{EMAIL}</a> · {PHONE} · '
          '<a href="https://www.carbonflows.store">carbonflows.store</a>'
          '<div style="margin-top:16px;opacity:.55">© 2026 CarbonFlow. All rights reserved.</div>'
          '</div></footer>')


def render(topic, publish_date):
    cat, slug, title, dek, sections, takeaway = topic
    url = f"{SITE}/blog/{slug}"
    body = "\n".join(f"<h2>{html.escape(h)}</h2>\n<p>{html.escape(b)}</p>" for h, b in sections)
    schema = {
        "@context": "https://schema.org", "@type": "BlogPosting",
        "headline": title, "description": dek, "inLanguage": "en",
        "datePublished": publish_date, "dateModified": publish_date,
        "author": {"@type": "Organization", "name": "CarbonFlow", "url": SITE},
        "publisher": ORG,
        "mainEntityOfPage": url, "about": ["AI automation", "software", cat],
        "keywords": "CarbonFlow, AI automation, Saudi Arabia, Gulf, " + cat,
    }
    org_ld = json.dumps({"@context": "https://schema.org", **ORG}, ensure_ascii=False)
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} | CarbonFlow</title>
<meta name="description" content="{html.escape(dek)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article"><meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(dek)}"><meta property="og:url" content="{url}">
<meta name="theme-color" content="#0a0d12">
{FONTS}<style>{CSS}</style>
<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
<script type="application/ld+json">{org_ld}</script>
</head><body>
{HEADER}
<main class="wrap"><article>
<div class="meta"><span class="badge">{html.escape(cat)}</span><span class="date">{publish_date}</span></div>
<h1>{html.escape(title)}</h1>
<p class="dek">{html.escape(dek)}</p>
<div class="prose">
{body}
<div class="cta"><strong>{html.escape(takeaway)}</strong>
<span class="c">CarbonFlow — self-hosted AI automation &amp; software studio for Saudi Arabia and the Gulf.<br>
<a href="mailto:{EMAIL}">{EMAIL}</a> · {PHONE} · <a href="{SITE}">{SITE}</a></span></div>
</div>
<a class="back" href="/blog">← Back to all articles</a>
</article></main>
{FOOTER}
</body></html>"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    start = datetime.date(2026, 7, 6)
    steps = [0, 2, 4]  # Sun/Tue/Thu-ish → 3 per week
    manifest = []
    for i, topic in enumerate(TOPICS):
        week, day = divmod(i, 3)
        pub = start + datetime.timedelta(days=week * 7 + steps[day])
        pub_s = pub.isoformat()
        cat, slug, title, dek = topic[0], topic[1], topic[2], topic[3]
        (OUT / f"{slug}.html").write_text(render(topic, pub_s), encoding="utf-8")
        manifest.append({"n": i + 1, "category": cat, "slug": slug, "title": title, "dek": dek,
                         "publishAt": pub_s, "url": f"{SITE}/blog/{slug}", "published": False})
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    cats = {}
    for m in manifest:
        cats[m["category"]] = cats.get(m["category"], 0) + 1
    print(f"generated {len(manifest)} articles into {OUT}")
    print("by category:", cats)
    print("schedule:", manifest[0]["publishAt"], "->", manifest[-1]["publishAt"])


if __name__ == "__main__":
    main()
