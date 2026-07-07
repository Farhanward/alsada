# -*- coding: utf-8 -*-
"""Build the standalone carbonflow-blog Cloudflare Worker (index + 30 articles).

SAFE: separate worker routed ONLY to /blog + 30 new slugs; never touches the live
tanstack-start-app. Date-gated (404 before publishAt) → scheduled drip publishing.
The index page is styled to match the CarbonFlow brand (dark, Plus Jakarta Sans,
JetBrains Mono, cyan accent). Article HTML comes pre-styled from blog_generate.py.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STAGED = ROOT / "blog" / "staged"
MANIFEST = ROOT / "blog" / "schedule.json"
OUT_DIR = ROOT / "blog-worker"
ZONE = "carbonflows.store"

manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
posts = {}
for m in manifest:
    html = (STAGED / f"{m['slug']}.html").read_text(encoding="utf-8")
    posts[m["slug"]] = {"publishAt": m["publishAt"], "title": m["title"],
                        "category": m["category"], "dek": m.get("dek", ""), "html": html}

DATA = json.dumps(posts, ensure_ascii=False)

# Brand-matched index CSS (dark theme, matches the article template).
INDEX_CSS = (
    ":root{--bg:oklch(0.075 0.01 250);--fg:oklch(0.94 0.006 248);--card:oklch(0.125 0.012 250);"
    "--muted:oklch(0.72 0.014 247);--accent:oklch(0.74 0.13 205);--accent-fg:oklch(0.075 0.012 250);"
    "--border:oklch(1 0 0 / 0.10);--radius:0.85rem}"
    "*{box-sizing:border-box}"
    "body{margin:0;background:var(--bg);color:var(--fg);font-family:'Plus Jakarta Sans',ui-sans-serif,system-ui,sans-serif;line-height:1.7;-webkit-font-smoothing:antialiased}"
    "a{color:inherit;text-decoration:none}.wrap{max-width:1080px;margin:0 auto;padding:0 24px}"
    "header.site{position:sticky;top:0;z-index:20;backdrop-filter:blur(14px);background:oklch(0.075 0.01 250 / 0.82);border-bottom:1px solid var(--border)}"
    ".nav{display:flex;align-items:center;justify-content:space-between;height:66px}"
    ".brand{display:flex;align-items:center;gap:11px;font-weight:800;font-size:1.15rem;letter-spacing:-.02em}"
    ".brand .logo{width:30px;height:30px;border-radius:9px;background:linear-gradient(135deg,var(--accent),oklch(0.55 0.15 255));display:grid;place-items:center;color:var(--accent-fg);font-weight:900}"
    ".nav a.link{color:var(--muted);font-size:.92rem;font-weight:600;margin-left:24px;transition:color .15s}.nav a.link:hover{color:var(--fg)}"
    ".nav .cta{background:var(--accent);color:var(--accent-fg);padding:9px 18px;border-radius:999px;font-weight:700;margin-left:24px}"
    ".eyebrow{font-family:'JetBrains Mono',monospace;font-size:.8rem;letter-spacing:.14em;text-transform:uppercase;color:var(--accent)}"
    ".hero{padding:80px 0 34px}.hero h1{font-size:clamp(2.4rem,5.5vw,3.6rem);line-height:1.04;letter-spacing:-.035em;margin:16px 0 14px;font-weight:800}"
    ".hero p.lead{color:var(--muted);font-size:1.2rem;max-width:640px}"
    ".chips{display:flex;gap:10px;flex-wrap:wrap;margin:30px 0 4px}"
    ".chip{font:inherit;font-size:.86rem;font-weight:600;color:var(--muted);border:1px solid var(--border);padding:8px 16px;border-radius:999px;cursor:pointer;transition:.15s;background:transparent}"
    ".chip.active,.chip:hover{color:var(--accent-fg);background:var(--accent);border-color:var(--accent)}"
    ".grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:22px;padding:34px 0 72px}"
    ".card{display:flex;flex-direction:column;background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:24px;transition:.18s;height:100%}"
    ".card:hover{transform:translateY(-4px);border-color:var(--accent);box-shadow:0 16px 44px oklch(0 0 0 / 0.45)}"
    ".badge{align-self:flex-start;font-family:'JetBrains Mono',monospace;font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;color:var(--accent);border:1px solid var(--accent);border-radius:6px;padding:4px 9px}"
    ".card .date{font-family:'JetBrains Mono',monospace;font-size:.8rem;color:var(--muted);margin-top:16px}"
    ".card h3{font-size:1.22rem;line-height:1.3;margin:9px 0 10px;letter-spacing:-.01em;font-weight:700}"
    ".card p{color:var(--muted);font-size:.96rem;margin:0 0 18px;flex:1}"
    ".card .more{color:var(--accent);font-weight:700;font-size:.92rem;margin-top:auto}"
    ".empty{padding:80px 0;color:var(--muted);text-align:center}"
    "footer.site{border-top:1px solid var(--border);padding:48px 0;color:var(--muted);font-size:.92rem;margin-top:20px}footer.site a{color:var(--accent)}"
    "@media(max-width:640px){.nav a.link:not(.cta){display:none}}"
)

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&'
         'family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">')

HEADER = ('<header class="site"><div class="wrap nav">'
          '<a href="/" class="brand"><span class="logo">C</span>CarbonFlow</a>'
          '<nav><a class="link" href="/services">Services</a>'
          '<a class="link" href="/blog">Blog</a>'
          '<a class="link" href="/ai-automation-for-business">AI Automation</a>'
          '<a class="link cta" href="/contact">Contact</a></nav></div></header>')

FOOTER = ('<footer class="site"><div class="wrap">'
          '<strong>CarbonFlow</strong> — self-hosted AI automation &amp; software studio for Saudi Arabia and the Gulf.<br>'
          '<a href="mailto:far7an.o88@gmail.com">far7an.o88@gmail.com</a> · +966504211844 · '
          '<a href="https://www.carbonflows.store">carbonflows.store</a>'
          '<div style="margin-top:16px;opacity:.55">© 2026 CarbonFlow. All rights reserved.</div></div></footer>')

# Canonical CarbonFlow entity for the blog index — sameAs disambiguates it from the
# climate-tech companies of the same name that AI engines otherwise confuse it with.
ORG_LD = json.dumps({
    "@context": "https://schema.org",
    "@type": "Organization",
    "@id": "https://www.carbonflows.store/#organization",
    "name": "CarbonFlow",
    "alternateName": ["CarbonFlow Store", "كاربون فلو"],
    "url": "https://www.carbonflows.store",
    "description": ("Self-hosted AI automation, SaaS development, n8n workflow automation, "
                    "Cloudflare Workers deployment and custom dashboards for businesses in "
                    "Saudi Arabia and the Gulf."),
    "areaServed": ["SA", "AE", "KW", "BH", "QA", "OM"],
    "sameAs": [
        "https://mastodon.social/@carbonflows",
        "https://bsky.app/profile/carbonflows.bsky.social",
        "https://www.linkedin.com/in/carbonflows",
    ],
}, ensure_ascii=False)

WORKER = r'''// carbonflow-blog — standalone, additive blog worker (generated by tools/build_blog_worker.py).
// Serves 30 scheduled articles at /blog/<slug>; date-gated (404 before publishAt).
const POSTS = __DATA__;
const CSS = `__CSS__`;
const HEADER = `__HEADER__`;
const FOOTER = `__FOOTER__`;
const FONTS = `__FONTS__`;
const ORG_LD = `__ORG_LD__`;
const SITE = "https://www.carbonflows.store";
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));

function todayISO() { return new Date().toISOString().slice(0, 10); }

function indexPage() {
  const t = todayISO();
  const live = Object.entries(POSTS)
    .filter(([, p]) => p.publishAt <= t)
    .sort((a, b) => (a[1].publishAt < b[1].publishAt ? 1 : -1));
  const cards = live.map(([slug, p]) =>
    `<a class="card" data-cat="${esc(p.category)}" href="/blog/${slug}">` +
    `<span class="badge">${esc(p.category)}</span>` +
    `<span class="date">${esc(p.publishAt)}</span>` +
    `<h3>${esc(p.title)}</h3><p>${esc(p.dek)}</p>` +
    `<span class="more">Read article &rarr;</span></a>`).join("");
  const cats = [...new Set(live.map(([, p]) => p.category))];
  const chips = `<button class="chip active" data-f="all">All</button>` +
    cats.map((c) => `<button class="chip" data-f="${esc(c)}">${esc(c)}</button>`).join("");
  const grid = live.length ? `<div class="grid" id="grid">${cards}</div>`
    : `<div class="empty">New articles are on the way — check back soon.</div>`;
  return `<!doctype html><html lang="en"><head><meta charset="utf-8">` +
    `<meta name="viewport" content="width=device-width, initial-scale=1">` +
    `<title>Blog | CarbonFlow</title><meta name="theme-color" content="#0a0d12">` +
    `<meta name="description" content="CarbonFlow blog — automation, programming, and AI for businesses in Saudi Arabia and the Gulf.">` +
    `<link rel="canonical" href="${SITE}/blog"><script type="application/ld+json">${ORG_LD}</script>${FONTS}<style>${CSS}</style></head><body>${HEADER}` +
    `<main class="wrap"><section class="hero"><p class="eyebrow">CarbonFlow Blog</p>` +
    `<h1>Automation, code &amp; AI — done right.</h1>` +
    `<p class="lead">Practical guides and product news on self-hosted AI, workflow automation, and software engineering for Saudi Arabia and the Gulf.</p>` +
    `<div class="chips">${chips}</div></section>${grid}</main>${FOOTER}` +
    `<script>const chips=document.querySelectorAll('.chip');chips.forEach(ch=>ch.addEventListener('click',()=>{` +
    `chips.forEach(x=>x.classList.remove('active'));ch.classList.add('active');const f=ch.dataset.f;` +
    `document.querySelectorAll('.card').forEach(c=>{c.style.display=(f==='all'||c.dataset.cat===f)?'':'none'})}));</script>` +
    `</body></html>`;
}

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const path = url.pathname.replace(/\/$/, "");
    if (path === "/blog" || path === "") {
      return new Response(indexPage(), { headers: { "content-type": "text/html; charset=utf-8", "cache-control": "public, max-age=1800" } });
    }
    const m = path.match(/^\/blog\/([a-z0-9-]+)$/);
    if (m) {
      const post = POSTS[m[1]];
      if (post && post.publishAt <= todayISO()) {
        return new Response(post.html, { headers: { "content-type": "text/html; charset=utf-8", "cache-control": "public, max-age=3600" } });
      }
    }
    return new Response("Not found", { status: 404, headers: { "content-type": "text/plain" } });
  },
};
'''

WORKER = (WORKER
          .replace("__DATA__", DATA)
          .replace("__CSS__", INDEX_CSS)
          .replace("__HEADER__", HEADER)
          .replace("__FOOTER__", FOOTER)
          .replace("__FONTS__", FONTS)
          .replace("__ORG_LD__", ORG_LD))

OUT_DIR.mkdir(parents=True, exist_ok=True)
(OUT_DIR / "worker.js").write_text(WORKER, encoding="utf-8")

routes = [{"pattern": f"www.{ZONE}/blog", "zone_name": ZONE}]
for slug in posts:
    routes.append({"pattern": f"www.{ZONE}/blog/{slug}", "zone_name": ZONE})
wrangler = {"name": "carbonflow-blog", "main": "worker.js",
            "compatibility_date": "2025-09-24", "workers_dev": False, "routes": routes}
(OUT_DIR / "wrangler.jsonc").write_text(json.dumps(wrangler, indent=2), encoding="utf-8")

size = len((OUT_DIR / "worker.js").read_text(encoding="utf-8").encode("utf-8"))
import datetime
today = datetime.date.today().isoformat()
print(f"built worker.js ({size} bytes, {len(posts)} posts) + {len(routes)} routes")
print("live today:", sorted(s for s, p in posts.items() if p["publishAt"] <= today))
