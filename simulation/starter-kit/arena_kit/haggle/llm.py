"""One chat call to the configured model, with the exact request and response kept for inspection.
LLM_PROVIDER=openai (any OpenAI-compatible endpoint) or anthropic. Keys never enter a record."""

import os
import time

import httpx


class LLMError(Exception):
    pass


class LLM:
    def __init__(self, env=os.environ):
        self.provider = env.get("LLM_PROVIDER", "openai")
        self.model = env.get("LLM_MODEL", "")
        self.key = env.get("ANTHROPIC_API_KEY" if self.provider == "anthropic" else "LLM_API_KEY", "")
        base = env.get("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.url = f"{base}/{env.get('LLM_ENDPOINT', '/chat/completions').strip().lstrip('/')}"
        self.timeout = float(env.get("LLM_TIMEOUT", "45"))
        self.local = base.startswith(("http://localhost", "http://127.0.0.1"))

    @property
    def configured(self):
        return bool(self.model and (self.key or self.local))

    def chat(self, system, messages, timeout=None, record=lambda r: None):
        """The model's text. `record` gets {request, response, ms, error} for every call, failed or not."""
        if self.provider == "anthropic":
            url = "https://api.anthropic.com/v1/messages"
            headers = {"x-api-key": self.key, "anthropic-version": "2023-06-01"}
            body = {"model": self.model, "max_tokens": 4096, "system": system, "messages": messages}
        else:
            url, headers = self.url, {"Authorization": f"Bearer {self.key}"}
            body = {"model": self.model, "messages": [{"role": "system", "content": system}, *messages]}
        t0, rec = time.monotonic(), {"url": url, "request": body, "response": None, "error": None}
        try:
            r = httpx.post(url, json=body, headers=headers, timeout=timeout or self.timeout)
            try:
                rec["response"] = r.json()
            except ValueError:
                rec["response"] = r.text[:4000]
            r.raise_for_status()
            data = rec["response"]
            if self.provider == "anthropic":
                return "".join(b.get("text", "") for b in data["content"] if b.get("type") == "text")
            return data["choices"][0]["message"]["content"]
        except (httpx.HTTPError, KeyError, IndexError, TypeError) as exc:
            rec["error"] = f"{type(exc).__name__}: {exc}"[:500]
            raise LLMError(rec["error"]) from None
        finally:
            rec["ms"] = round((time.monotonic() - t0) * 1000)
            record(rec)
