"""Extract structured signals from an AI engine answer (deterministic, heuristic).

Returns: mentioned, mention_count, prominence, client_cited, sentiment,
competitors[], citations[], flags[] (risk/misinformation).
"""
import re
from urllib.parse import urlparse

URL_RE = re.compile(r'https?://[^\s)>\]"\',]+', re.I)

POS_WORDS = ["recommended", "leading", "best", "excellent", "trusted", "reliable",
             "great", "top choice", "قوية", "موثوق", "ممتاز", "يُنصح", "رائدة", "أفضل"]
NEG_WORDS = ["discontinued", "shut down", "no longer", "not operating", "avoid", "scam",
             "poor", "limited reviews", "limited", "outdated", "محدودة", "لا يُنصح",
             "متوقّفة", "مغلقة", "قديمة", "ضعيف"]
MISINFO_NEG = ["discontinued", "no longer operating", "shut down", "may no longer",
               "not operating", "may be discontinued", "متوقّفة", "مغلقة", "لم يعد"]
# Engine explicitly signals it has little/no public info — a named mention here is
# NOT a real endorsement and must not be scored as positive visibility.
NOINFO = ["insufficient information", "limited information", "little information",
          "no reviews", "limited public reviews", "not enough information",
          "couldn't find", "could not find", "no relevant results", "unable to find",
          "لا توجد معلومات", "لا تتوفّر معلومات", "لا تتوفر معلومات", "معلومات محدودة",
          "لم يسفر", "لا يمكن تأكيد", "لا توجد مراجعات", "لا توجد معلومات كافية",
          "معلومات كافية", "غير متوفرة"]
PRICE_RE = re.compile(r'(\$|usd|sar|ر\.?\s?س)\s?\d|\d+\s?(per month|/month|شهري)', re.I)
COMMON_WORD_BRANDS = {"make"}


def _norm(s):
    return (s or "").lower()


def _phrase_matches(text, phrase, *, ignore_case=True):
    flags = re.I if ignore_case else 0
    pattern = r"(?<![A-Za-z0-9_])" + re.escape(phrase) + r"(?![A-Za-z0-9_])"
    return list(re.finditer(pattern, text or "", flags))


def _host(url):
    parsed = urlparse(url)
    host = (parsed.netloc or "").lower().split("@")[-1].split(":")[0]
    if host.startswith("www."):
        host = host[4:]
    return host


def _domain_matches(url, domain):
    clean_domain = (domain or "").lower().strip()
    if clean_domain.startswith("www."):
        clean_domain = clean_domain[4:]
    host = _host(url)
    return bool(clean_domain) and (host == clean_domain or host.endswith("." + clean_domain))


def _competitor_mentioned(text, competitor):
    if not competitor:
        return False
    name = competitor.strip()
    if name.lower() in COMMON_WORD_BRANDS:
        if _phrase_matches(text, name, ignore_case=False):
            return True
        return _domain_matches("https://" + name.lower() + ".com", name.lower() + ".com") and (
            name.lower() + ".com" in _norm(text)
        )
    return bool(_phrase_matches(text, name, ignore_case=True))


def analyze(answer, client):
    a = answer or ""
    low = _norm(a)
    aliases = [x for x in client.get("aliases", []) if x]

    positions, count = [], 0
    for al in aliases:
        for m in _phrase_matches(a, al, ignore_case=True):
            count += 1
            positions.append(m.start())
    mentioned = count > 0

    prominence = 0.0
    if mentioned and len(a) > 0:
        prominence = round(1.0 - (min(positions) / len(a)), 3)  # earlier mention => higher

    citations = URL_RE.findall(a)
    domain = client.get("domain", "")
    client_cited = any(_domain_matches(u, domain) for u in citations)

    competitors = sorted({c for c in client.get("competitors", []) if _competitor_mentioned(a, c)},
                         key=str.lower)

    no_info = any((w in a) or (w.lower() in low) for w in NOINFO)

    if mentioned:
        pos = sum(1 for w in POS_WORDS if w.lower() in low)
        neg = sum(1 for w in NEG_WORDS if w.lower() in low)
        sentiment = "positive" if pos > neg else ("negative" if neg > pos else "neutral")
        # "we found no info about X" is not a positive endorsement, however phrased.
        if no_info and sentiment == "positive":
            sentiment = "neutral"
    else:
        sentiment = "absent"

    flags = []
    if mentioned:
        if any(w.lower() in low for w in MISINFO_NEG):
            flags.append("possible_misinformation: brand described as discontinued/inactive")
        if PRICE_RE.search(low):
            flags.append("unverified_claim: a pricing figure is stated about the brand")
        if no_info:
            flags.append("insufficient_info: engine reports little/no public info about the brand")
        # Identity/namesake confusion: the brand is named, but the answer never lands
        # in the brand's own context (opt-in via client 'context_anchors').
        anchors = [x for x in client.get("context_anchors", []) if x]
        if anchors and not any(_phrase_matches(a, x, ignore_case=True) for x in anchors):
            flags.append("identity_mismatch: brand named outside its known context (possible namesake confusion)")

    return {
        "mentioned": mentioned,
        "mention_count": count,
        "prominence": prominence,
        "client_cited": client_cited,
        "sentiment": sentiment,
        "competitors": competitors,
        "citations": citations,
        "flags": flags,
    }
