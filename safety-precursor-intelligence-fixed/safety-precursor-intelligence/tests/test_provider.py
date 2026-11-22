"""Tests for optional API configuration and safe local fallback."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from spi.provider import generate_chat

def test_provider_falls_back_when_no_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert generate_chat([{"role": "user", "content": "hello"}]) is None

def test_provider_model_has_default(monkeypatch):
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    from spi.provider import provider_model
    assert provider_model() == "gpt-4o-mini"
