"""What the page may change: the model and the system prompt.

Model settings live in `haggle_settings.json` (git-ignored: it may hold the API key, which is write-only: the
page never gets it back). The system prompt is a plain file, `prompts/system.md` by default, tracked in git so
prompt versions are shared and reviewable; without the file the built-in prompt is used. Every run records
which prompt (file and hash) it used, and the raw request shows the full text."""

import hashlib
import json
import os
from pathlib import Path

from .agent import SYSTEM
from .llm import LLM

FIELDS = ("provider", "model", "base_url", "endpoint", "timeout", "prompt_file")
ENV = {
    "provider": "LLM_PROVIDER",
    "model": "LLM_MODEL",
    "base_url": "LLM_BASE_URL",
    "endpoint": "LLM_ENDPOINT",
    "timeout": "LLM_TIMEOUT",
}
DEFAULT_PROMPT_FILE = "prompts/system.md"


class Settings:
    def __init__(self, path=None):
        self.path = Path(path or os.environ.get("ARENA_SETTINGS", "haggle_settings.json"))

    def stored(self):
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def update(self, patch):
        """Merge the given fields; an empty api_key keeps the stored one, `clear_api_key` removes it."""
        data = self.stored()
        for key in FIELDS:
            if key in patch:
                value = str(patch[key]).strip()
                data[key] = value or None
        if patch.get("api_key"):
            data["api_key"] = str(patch["api_key"]).strip()
        if patch.get("clear_api_key"):
            data.pop("api_key", None)
        self.path.write_text(json.dumps(data, indent=1), encoding="utf-8")

    def env(self):
        env, data = dict(os.environ), self.stored()
        for key, name in ENV.items():
            if data.get(key):
                env[name] = str(data[key])
        if data.get("api_key"):
            env["ANTHROPIC_API_KEY" if env.get("LLM_PROVIDER") == "anthropic" else "LLM_API_KEY"] = data["api_key"]
        return env

    def llm(self):
        return LLM(self.env())

    def view(self):
        """Effective values for the page, never the key."""
        env, data = self.env(), self.stored()
        llm = LLM(env)
        return {
            "provider": llm.provider,
            "model": llm.model,
            "base_url": env.get("LLM_BASE_URL", "https://api.openai.com/v1"),
            "endpoint": env.get("LLM_ENDPOINT", "/chat/completions"),
            "timeout": llm.timeout,
            "prompt_file": data.get("prompt_file") or DEFAULT_PROMPT_FILE,
            "has_key": bool(llm.key),
            "configured": llm.configured,
        }

    # -- the system prompt ---------------------------------------------------------------------
    def prompt_path(self):
        return Path(self.stored().get("prompt_file") or DEFAULT_PROMPT_FILE)

    def prompt(self):
        """(text, source): the prompt file if it exists and is not empty, else the built-in prompt."""
        try:
            text = self.prompt_path().read_text(encoding="utf-8").strip()
        except OSError:
            text = ""
        return (text, str(self.prompt_path())) if text else (SYSTEM, "built-in")

    def save_prompt(self, text):
        path = self.prompt_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text.strip() + "\n", encoding="utf-8")

    def reset_prompt(self):
        self.prompt_path().unlink(missing_ok=True)


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()[:10]
