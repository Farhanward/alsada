"""Deterministic tests for the analyze + score pipeline."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alsada.analyze import analyze
from alsada.score import probe_score, aggregate

CLIENT = {
    "name": "CarbonFlow",
    "domain": "carbonflows.store",
    "aliases": ["CarbonFlow", "carbonflows"],
    "competitors": ["Zapier", "Make", "n8n"],
}


def test_visible_positive_cited():
    ans = ("CarbonFlow (https://www.carbonflows.store) is a recommended, reliable provider "
           "of Cloudflare Workers deployment.")
    an = analyze(ans, CLIENT)
    assert an["mentioned"] is True
    assert an["client_cited"] is True
    assert an["sentiment"] == "positive"
    assert probe_score(an) >= 70


def test_invisible_competitors_only():
    ans = "The best options are Zapier and Make for workflow automation."
    an = analyze(ans, CLIENT)
    assert an["mentioned"] is False
    assert set(an["competitors"]) == {"Zapier", "Make"}
    assert probe_score(an) == 0


def test_competitor_common_word_requires_brand_signal():
    ans = "CarbonFlow can make workflow automation easier than manual spreadsheets."
    an = analyze(ans, CLIENT)
    assert an["mentioned"] is True
    assert "Make" not in an["competitors"]


def test_client_citation_requires_real_domain():
    ans = "CarbonFlow is discussed at https://notcarbonflows.store.example/review"
    an = analyze(ans, CLIENT)
    assert an["mentioned"] is True
    assert an["client_cited"] is False


def test_misinformation_flag_and_negative():
    ans = "CarbonFlow appears to be discontinued and may no longer be operating."
    an = analyze(ans, CLIENT)
    assert an["mentioned"] is True
    assert an["sentiment"] == "negative"
    assert any("misinformation" in f for f in an["flags"])
    assert probe_score(an) < 50


def test_pricing_flag():
    ans = "CarbonFlow charges around $499 per month."
    an = analyze(ans, CLIENT)
    assert any("pricing" in f for f in an["flags"])


def test_aggregate():
    probes = [
        {"engine": "mock", "mentioned": True, "prominence": 0.9, "sentiment": "positive",
         "client_cited": True, "competitors": []},
        {"engine": "mock", "mentioned": False, "prominence": 0.0, "sentiment": "absent",
         "client_cited": False, "competitors": ["Zapier", "Make"]},
    ]
    agg = aggregate(probes)
    assert agg["n"] == 2
    assert agg["client_mentions"] == 1
    assert agg["comp_mentions"] == 2
    assert len(agg["invisible"]) == 1
    assert 0 <= agg["overall"] <= 100


def test_cloud_providers_construct():
    # validates request wiring for cloud engines WITHOUT any network call or cost
    os.environ["OPENAI_API_KEY"] = "dummy-openai"
    os.environ["ANTHROPIC_API_KEY"] = "dummy-anthropic"
    os.environ["PERPLEXITY_API_KEY"] = "dummy-pplx"
    from alsada.providers import get_provider
    op = get_provider("openai", "gpt-4o-mini")
    assert op.url.endswith("/chat/completions") and op.model == "gpt-4o-mini"
    px = get_provider("perplexity", "sonar")
    assert "perplexity.ai" in px.url and px.key == "dummy-pplx"
    an = get_provider("anthropic", "claude-haiku-4-5-20251001")
    url, payload, headers = an._build({"id": "x", "text": "hi"})
    assert url.endswith("/v1/messages")
    assert headers["x-api-key"] == "dummy-anthropic" and headers["anthropic-version"]
    assert payload["model"] == "claude-haiku-4-5-20251001" and payload["max_tokens"] >= 1
    os.environ["OPENROUTER_API_KEY"] = "dummy-or"
    orr = get_provider("openrouter", "perplexity/sonar")
    assert "openrouter.ai" in orr.url and orr.key == "dummy-or"


def test_compare_movement():
    from alsada.compare import compare
    base = [
        {"prompt_id": "p1", "prompt_text": "q1", "engine": "x", "mentioned": False,
         "prominence": 0.0, "sentiment": "absent", "client_cited": False,
         "competitors": ["Zapier"], "flags": []},
        {"prompt_id": "p2", "prompt_text": "q2", "engine": "x", "mentioned": True,
         "prominence": 0.5, "sentiment": "negative", "client_cited": False,
         "competitors": [], "flags": ["possible_misinformation: x"]},
    ]
    head = [
        {"prompt_id": "p1", "prompt_text": "q1", "engine": "x", "mentioned": True,
         "prominence": 0.9, "sentiment": "positive", "client_cited": True,
         "competitors": [], "flags": []},
        {"prompt_id": "p2", "prompt_text": "q2", "engine": "x", "mentioned": True,
         "prominence": 0.6, "sentiment": "neutral", "client_cited": False,
         "competitors": [], "flags": []},
    ]
    c = compare(base, head)
    assert len(c["gained"]) == 1 and c["gained"][0]["prompt_id"] == "p1"
    assert c["d_overall"] > 0
    assert len(c["resolved_flags"]) == 1


def test_radar():
    from alsada.radar import competitor_standings, cited_sources, opportunities, domain_of
    probes = [
        {"prompt_id": "p1", "prompt_text": "q1", "topic": "t1", "mentioned": False,
         "competitors": ["Zapier", "Make"],
         "citations": ["https://www.g2.com/x", "https://reddit.com/y"]},
        {"prompt_id": "p2", "prompt_text": "q2", "topic": "t2", "mentioned": True,
         "competitors": ["Zapier"], "citations": ["https://g2.com/z"]},
    ]
    standings, cm = competitor_standings(probes)
    assert cm == 1
    assert dict(standings)["Zapier"] == 2
    srcs = dict(cited_sources(probes))
    assert srcs.get("g2.com") == 2 and srcs.get("reddit.com") == 1
    assert domain_of("https://www.g2.com/x") == "g2.com"
    opps = opportunities(probes)
    assert len(opps) == 1 and opps[0]["prompt_id"] == "p1"


def test_publish_classify():
    from alsada.publish import classify
    cl = {"domain": "carbonflows.store"}
    assert classify("carbonflows.store", cl) == "owned"
    assert classify("github.com", cl) == "owned"
    assert classify("khamsat.com", cl) == "self_submit"
    assert classify("reddit.com", cl) == "earned"
    assert classify("n8n.io", cl) == "reference"


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print("PASS", fn.__name__)
    print("ALL %d TESTS PASSED" % len(fns))


if __name__ == "__main__":
    _run_all()
