"""Optional OpenAI-compatible chat provider; local safety controls always win."""
from __future__ import annotations
import json
import os
import urllib.request
import urllib.error
from typing import Sequence

DEFAULT_SYSTEM = (
    "You are a warm, calm workplace HSE assistant. Speak naturally and briefly. "
    "Never claim to be a doctor, emergency dispatcher, investigator, or legal authority. "
    "Do not diagnose injuries or give instructions that bypass site procedures. "
    "For imminent danger, tell the user to activate the site's emergency response first. "
    "Ask one useful follow-up question at a time. Distinguish observed facts from assumptions. "
    "Do not invent incident counts, site records, policies, or regulatory requirements. "
    "If local safety guidance is supplied, preserve it and do not contradict it."
)

def load_local_env() -> None:
    """Load simple KEY=VALUE entries from a project .env without dependencies."""
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    try:
        with open(env_path, "r", encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except OSError:
        return

def provider_configured() -> bool:
    load_local_env()
    return bool(os.getenv("OPENAI_API_KEY", "").strip())

def provider_model() -> str:
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"

def generate_chat(messages: Sequence[dict[str, str]], timeout: int = 18) -> str | None:
    """Call an OpenAI-compatible Chat Completions endpoint when configured.

    The standard library is used so the local application remains installable
    without an additional SDK. Errors fail closed to the deterministic assistant.
    """
    load_local_env()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    endpoint = base_url + "/chat/completions"
    payload = {"model": provider_model(), "temperature": 0.35,
               "messages": [{"role": "system", "content": DEFAULT_SYSTEM}, *messages[-12:]]}
    request = urllib.request.Request(endpoint, data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
        content = body["choices"][0]["message"]["content"]
        return str(content).strip() or None
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, KeyError, IndexError, ValueError, OSError):
        return None
