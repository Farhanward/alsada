"""Engine adapters: mock (free/offline), ollama (local), openai (cloud).

Each provider exposes .ask(prompt_dict) -> answer string.
Uses only the standard library so the MVP runs with no install step.
"""
import json
import os
import urllib.request


class ProviderError(Exception):
    pass


def _http_post(url, payload, headers, timeout=90, retries=6):
    """POST JSON with retry on transient 429/5xx (Gemini/OpenRouter capacity spikes).

    Free-tier Gemini enforces a per-minute quota; on 429 we honour the server's
    ``Retry-After`` header when present and otherwise back off exponentially, so a
    full probe run rides through rate limits instead of collecting false zeros.
    """
    import time as _time
    import urllib.error as _err
    data = json.dumps(payload).encode("utf-8")
    last = None
    for attempt in range(retries):
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except _err.HTTPError as e:
            last = e
            if e.code in (429, 500, 502, 503, 504) and attempt < retries - 1:
                wait = None
                try:
                    ra = e.headers.get("Retry-After") if e.headers else None
                    if ra:
                        wait = float(ra)
                except Exception:
                    wait = None
                if wait is None:
                    wait = min(60, 5 * (2 ** attempt))  # 5,10,20,40,60s
                _time.sleep(wait)
                continue
            raise
        except Exception as e:  # transient network
            last = e
            if attempt < retries - 1:
                _time.sleep(min(60, 5 * (2 ** attempt)))
                continue
            raise
    if last:
        raise last


class MockProvider:
    """Deterministic answers from each prompt's `mock_answer` field. For dev/testing."""
    name = "mock"

    def __init__(self, model="mock", prompts=None):
        self.model = "mock"
        self._answers = {p["id"]: p.get("mock_answer", "") for p in (prompts or [])}

    def ask(self, prompt):
        return self._answers.get(prompt["id"], "No information available.")


class OllamaProvider:
    """Local/self-hosted model via Ollama (free, real). Set ALSADA_OLLAMA_URL."""
    name = "ollama"

    def __init__(self, model="qwen2.5:3b", prompts=None):
        self.model = model
        self.url = os.environ.get("ALSADA_OLLAMA_URL", "http://localhost:11434").rstrip("/")

    def ask(self, prompt):
        out = _http_post(
            self.url + "/api/generate",
            {"model": self.model, "prompt": prompt["text"], "stream": False},
            {"Content-Type": "application/json"},
        )
        return out.get("response", "")


class OpenAIProvider:
    """OpenAI-compatible chat completions (cloud, paid). Set OPENAI_API_KEY."""
    name = "openai"

    def __init__(self, model="gpt-4o-mini", prompts=None):
        self.model = model
        self.key = os.environ.get("OPENAI_API_KEY")
        if not self.key:
            raise ProviderError("OPENAI_API_KEY is not set")
        base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.url = base + "/chat/completions"

    def ask(self, prompt):
        headers = {"Content-Type": "application/json", "Authorization": "Bearer " + self.key}
        ref = os.environ.get("OPENAI_HTTP_REFERER")
        title = os.environ.get("OPENAI_X_TITLE")
        if ref:
            headers["HTTP-Referer"] = ref
        if title:
            headers["X-Title"] = title
        out = _http_post(
            self.url,
            {"model": self.model, "messages": [{"role": "user", "content": prompt["text"]}]},
            headers,
        )
        choice0 = (out.get("choices") or [{}])[0]
        message = choice0.get("message", {}) if isinstance(choice0, dict) else {}
        msg = message.get("content", "") or ""
        # web-search engines (Perplexity/OpenRouter) return cited URLs separately,
        # via top-level `citations`/`search_results` or message `annotations` (url_citation).
        urls = []
        for c in (out.get("citations") or out.get("search_results") or []):
            u = c if isinstance(c, str) else (c.get("url") or c.get("link") or "")
            if u:
                urls.append(u)
        for a in (message.get("annotations") or []):
            if isinstance(a, dict):
                uc = a.get("url_citation") or {}
                u = uc.get("url") or a.get("url") or ""
                if u:
                    urls.append(u)
        if urls:
            seen = []
            for u in urls:
                if u not in seen:
                    seen.append(u)
            msg = msg + "\nSources: " + " ".join(seen)
        return msg


class FileProvider:
    """Replays real answers pre-fetched into a JSONL file (one {"id","answer"} per line).

    Set ALSADA_ANSWERS_FILE to the path and ALSADA_ANSWERS_MODEL to the real model name.
    Lets us run the full pipeline on real engine output captured where the engine is reachable
    (e.g. on the server itself), without exposing the engine to this host.
    """
    name = "file"

    def __init__(self, model=None, prompts=None):
        self.model = os.environ.get("ALSADA_ANSWERS_MODEL", "file")
        path = os.environ.get("ALSADA_ANSWERS_FILE")
        if not path:
            raise ProviderError("ALSADA_ANSWERS_FILE is not set")
        self._answers = {}
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                self._answers[obj["id"]] = obj.get("answer", "")

    def ask(self, prompt):
        return self._answers.get(prompt["id"], "")


class PerplexityProvider(OpenAIProvider):
    """Perplexity — OpenAI-compatible, but performs real web search (most representative
    of how AI search actually answers about a brand). Set PERPLEXITY_API_KEY."""
    name = "perplexity"

    def __init__(self, model="sonar", prompts=None):
        self.model = model or "sonar"
        self.key = os.environ.get("PERPLEXITY_API_KEY")
        if not self.key:
            raise ProviderError("PERPLEXITY_API_KEY is not set")
        base = os.environ.get("PERPLEXITY_BASE_URL", "https://api.perplexity.ai").rstrip("/")
        self.url = base + "/chat/completions"


class AnthropicProvider:
    """Anthropic Claude (messages API). Set ANTHROPIC_API_KEY."""
    name = "anthropic"

    def __init__(self, model="claude-haiku-4-5-20251001", prompts=None):
        self.model = model or "claude-haiku-4-5-20251001"
        self.key = os.environ.get("ANTHROPIC_API_KEY")
        if not self.key:
            raise ProviderError("ANTHROPIC_API_KEY is not set")
        base = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com").rstrip("/")
        self.url = base + "/v1/messages"
        self.version = os.environ.get("ANTHROPIC_VERSION", "2023-06-01")
        self.max_tokens = int(os.environ.get("ALSADA_MAX_TOKENS", "1024"))

    def _build(self, prompt):
        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": prompt["text"]}],
        }
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.key,
            "anthropic-version": self.version,
        }
        return self.url, payload, headers

    def ask(self, prompt):
        url, payload, headers = self._build(prompt)
        out = _http_post(url, payload, headers)
        parts = out.get("content", []) or []
        return "".join(p.get("text", "") for p in parts if p.get("type") == "text")


class OpenRouterProvider(OpenAIProvider):
    """OpenRouter — one key for ALL cloud models (OpenAI, Claude, Gemini, Perplexity...).
    Use web search by default with perplexity/sonar, or append ':online' to any model.
    Set OPENROUTER_API_KEY."""
    name = "openrouter"

    def __init__(self, model="perplexity/sonar", prompts=None):
        self.model = model or "perplexity/sonar"
        self.key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY")
        if not self.key:
            raise ProviderError("OPENROUTER_API_KEY is not set")
        base = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
        self.url = base + "/chat/completions"


class GeminiProvider:
    """Google Gemini via the native Generative Language API (free tier available at
    https://aistudio.google.com/apikey). Set GEMINI_API_KEY (or GOOGLE_API_KEY)."""
    name = "gemini_native"

    def __init__(self, model="gemini-2.5-flash", prompts=None):
        self.model = model or "gemini-2.5-flash"
        self.key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not self.key:
            raise ProviderError("GEMINI_API_KEY is not set")
        base = os.environ.get("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com").rstrip("/")
        self.url = "%s/v1beta/models/%s:generateContent" % (base, self.model)

    def ask(self, prompt):
        headers = {"Content-Type": "application/json", "x-goog-api-key": self.key}
        body = {"contents": [{"parts": [{"text": prompt["text"]}]}]}
        if os.environ.get("ALSADA_WEB_SEARCH", "").strip().lower() in ("1", "true", "yes", "on"):
            body["tools"] = [{"google_search": {}}]  # live web grounding
        out = _http_post(self.url, body, headers)
        cands = out.get("candidates") or []
        if not cands:
            return ""
        parts = (cands[0].get("content") or {}).get("parts") or []
        text = "".join(p.get("text", "") for p in parts if isinstance(p, dict) and "text" in p)
        gm = cands[0].get("groundingMetadata") or {}
        srcs = []
        for c in (gm.get("groundingChunks") or []):
            w = c.get("web") or {}
            for v in (w.get("uri"), w.get("title")):
                if v and v not in srcs:
                    srcs.append(v)
        if srcs:
            text = text + "\nSources: " + " ".join(srcs)
        return text


def _online(model):
    """Append OpenRouter's ':online' web-search suffix when ALSADA_WEB_SEARCH is enabled,
    so answers reflect what the engine actually says after searching the live web."""
    on = os.environ.get("ALSADA_WEB_SEARCH", "").strip().lower() in ("1", "true", "yes", "on")
    return model + ":online" if on and ":online" not in model else model


def make_chatgpt(model=None, prompts=None):
    """`chatgpt` engine — native OpenAI when OPENAI_BASE_URL is OpenAI, else via OpenRouter (openai/gpt-4o)."""
    base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    via_router = "openrouter" in base
    default = _online("openai/gpt-4o") if via_router else (os.environ.get("ALSADA_CHATGPT_MODEL") or "gpt-4o")
    return OpenAIProvider(model=model or default, prompts=prompts)


def make_gemini(model=None, prompts=None):
    """`gemini` engine — native Google when GEMINI_API_KEY is set, else via OpenRouter (google/gemini-2.5-flash)."""
    if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
        return GeminiProvider(model=model or (os.environ.get("ALSADA_GEMINI_MODEL") or "gemini-2.5-flash"), prompts=prompts)
    return OpenRouterProvider(model=model or _online("google/gemini-2.5-flash"), prompts=prompts)


_REGISTRY = {
    "mock": MockProvider,
    "ollama": OllamaProvider,
    "openai": OpenAIProvider,
    "openrouter": OpenRouterProvider,
    "perplexity": PerplexityProvider,
    "anthropic": AnthropicProvider,
    "file": FileProvider,
    "gemini_native": GeminiProvider,
    "chatgpt": make_chatgpt,
    "gemini": make_gemini,
}


def get_provider(name, model=None, prompts=None):
    name = (name or "mock").lower()
    if name not in _REGISTRY:
        raise ProviderError("unknown engine '%s' (available: %s)" % (name, ", ".join(_REGISTRY)))
    cls = _REGISTRY[name]
    return cls(model=model, prompts=prompts) if model else cls(prompts=prompts)
