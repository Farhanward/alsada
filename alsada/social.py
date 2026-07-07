"""مركز النشر — Social Publishing Center.

Posts the brand's content to X (Twitter), Instagram, and TikTok via the OFFICIAL
APIs. You own it (runs on your server / locally), and it ties into «الناشر»:
الناشر يولّد المحتوى → يُدرَج في الطابور → هذا الموديول ينشره.

- Credentials are read from env (.env.local). NEVER hard-code tokens.
- Works in DRY-RUN with no credentials (prints what it WOULD post) — so the whole
  pipeline is testable before you obtain API access.
- Honest/legitimate posting only (official APIs), no scraping or bot automation.
"""
import json
import os
import time
import urllib.request

from alsada.config import PROJECT_ROOT

QUEUE_FILE = PROJECT_ROOT / "data" / "social_queue.jsonl"
POSTED_FILE = PROJECT_ROOT / "data" / "social_posted.jsonl"


def _http_post(url, payload, headers, timeout=60):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


class Post:
    """A single piece of content to publish."""
    def __init__(self, text, image_url=None, video_url=None, link=None, id=None):
        self.id = id or time.strftime("%Y%m%dT%H%M%S")
        self.text = text
        self.image_url = image_url   # must be a PUBLIC url for IG
        self.video_url = video_url   # public url for TikTok
        self.link = link

    def to_dict(self):
        return {"id": self.id, "text": self.text, "image_url": self.image_url,
                "video_url": self.video_url, "link": self.link}

    @staticmethod
    def from_dict(d):
        return Post(d.get("text", ""), d.get("image_url"), d.get("video_url"),
                    d.get("link"), d.get("id"))


# --- platform adapters -------------------------------------------------------

class XAdapter:
    """X (Twitter) API v2 — POST /2/tweets with a user OAuth2 access token."""
    name = "x"
    def __init__(self):
        self.token = os.environ.get("X_ACCESS_TOKEN")
    def ready(self):
        return bool(self.token)
    def post(self, p, dry=False):
        body = {"text": (p.text + (("\n" + p.link) if p.link else ""))[:280]}
        if dry or not self.ready():
            return {"platform": self.name, "dry": True, "would_post": body}
        out = _http_post("https://api.twitter.com/2/tweets", body,
                         {"Content-Type": "application/json",
                          "Authorization": "Bearer " + self.token})
        return {"platform": self.name, "ok": True, "id": out.get("data", {}).get("id")}


class InstagramAdapter:
    """Instagram Graph API — needs an IG Business account + Page token.
    Flow: create media container (image_url + caption) -> publish."""
    name = "instagram"
    def __init__(self):
        self.token = os.environ.get("IG_ACCESS_TOKEN")
        self.user_id = os.environ.get("IG_USER_ID")
    def ready(self):
        return bool(self.token and self.user_id)
    def post(self, p, dry=False):
        caption = p.text + (("\n" + p.link) if p.link else "")
        if dry or not self.ready():
            return {"platform": self.name, "dry": True,
                    "would_post": {"caption": caption, "image_url": p.image_url}}
        if not p.image_url:
            return {"platform": self.name, "ok": False, "err": "Instagram requires image_url"}
        base = "https://graph.facebook.com/v21.0/" + self.user_id
        c = _http_post(base + "/media",
                       {"image_url": p.image_url, "caption": caption, "access_token": self.token},
                       {"Content-Type": "application/json"})
        cid = c.get("id")
        pub = _http_post(base + "/media_publish",
                         {"creation_id": cid, "access_token": self.token},
                         {"Content-Type": "application/json"})
        return {"platform": self.name, "ok": True, "id": pub.get("id")}


class TikTokAdapter:
    """TikTok Content Posting API — needs an approved TikTok dev app + user token.
    Video publishing (PULL_FROM_URL)."""
    name = "tiktok"
    def __init__(self):
        self.token = os.environ.get("TIKTOK_ACCESS_TOKEN")
    def ready(self):
        return bool(self.token)
    def post(self, p, dry=False):
        if dry or not self.ready():
            return {"platform": self.name, "dry": True,
                    "would_post": {"caption": p.text, "video_url": p.video_url}}
        if not p.video_url:
            return {"platform": self.name, "ok": False, "err": "TikTok requires video_url"}
        out = _http_post(
            "https://open.tiktokapis.com/v2/post/publish/video/init/",
            {"post_info": {"title": p.text[:150], "privacy_level": "PUBLIC_TO_EVERYONE"},
             "source_info": {"source": "PULL_FROM_URL", "video_url": p.video_url}},
            {"Content-Type": "application/json", "Authorization": "Bearer " + self.token})
        return {"platform": self.name, "ok": True, "publish_id": out.get("data", {}).get("publish_id")}


_ADAPTERS = {"x": XAdapter, "instagram": InstagramAdapter, "tiktok": TikTokAdapter}


def get_adapter(name):
    return _ADAPTERS[name]()


# --- queue + publish ---------------------------------------------------------

def enqueue(post):
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(QUEUE_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(post.to_dict(), ensure_ascii=False) + "\n")
    return post.id


def _read_queue():
    if not QUEUE_FILE.exists():
        return []
    out = []
    for line in QUEUE_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(Post.from_dict(json.loads(line)))
    return out


def publish(post, platforms=None, dry=True):
    """Publish one post to the given platforms (default: all). dry=True by default
    so nothing goes live unless explicitly dry=False."""
    platforms = platforms or list(_ADAPTERS.keys())
    results = []
    for name in platforms:
        ad = get_adapter(name)
        try:
            results.append(ad.post(post, dry=dry))
        except Exception as exc:
            results.append({"platform": name, "ok": False, "err": str(exc)[:200]})
    return results


def publish_queue(platforms=None, dry=True):
    posts = _read_queue()
    summary = []
    for p in posts:
        summary.append({"id": p.id, "results": publish(p, platforms, dry)})
    return summary


def _load_env_local():
    f = PROJECT_ROOT / ".env.local"
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def main(argv=None):
    import argparse
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    _load_env_local()
    ap = argparse.ArgumentParser(prog="alsada.social", description="Social publishing center")
    sub = ap.add_subparsers(dest="cmd", required=True)
    pp = sub.add_parser("post")
    pp.add_argument("--text", required=True)
    pp.add_argument("--link", default="https://www.carbonflows.store")
    pp.add_argument("--image", default=None)
    pp.add_argument("--video", default=None)
    pp.add_argument("--platforms", default="x,instagram,tiktok")
    pp.add_argument("--live", action="store_true", help="actually publish (default: dry-run)")
    pp.add_argument("--queue", action="store_true", help="add to queue instead of posting")
    qp = sub.add_parser("publish-queue")
    qp.add_argument("--platforms", default="x,instagram,tiktok")
    qp.add_argument("--live", action="store_true")
    sp = sub.add_parser("status")
    args = ap.parse_args(argv)

    if args.cmd == "status":
        for name in _ADAPTERS:
            ad = get_adapter(name)
            print("  %-10s : %s" % (name, "READY (creds set)" if ad.ready() else "dry-run (no creds)"))
        return 0
    if args.cmd == "post":
        p = Post(args.text, image_url=args.image, video_url=args.video, link=args.link)
        if args.queue:
            print("queued:", enqueue(p))
            return 0
        results = publish(p, args.platforms.split(","), dry=not args.live)
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "publish-queue":
        out = publish_queue(args.platforms.split(","), dry=not args.live)
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
