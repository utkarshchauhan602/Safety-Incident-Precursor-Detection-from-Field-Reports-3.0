"""Adapter between Streamlit state, legacy report queries and hybrid assistant."""
from __future__ import annotations
from .conversation import respond
from .memory import state_from_session, update_state
from .triage import classify_intent

def answer_in_session(user_text: str, session: dict, use_generation: bool = True):
    state = state_from_session(session)
    result = respond(user_text, state=state, use_generation=use_generation)
    hazard_key = result.hazard.key if result.hazard else state.last_hazard
    pending = result.hazard.key if result.hazard else state.pending_intent
    update_state(state, user_text, result.text, hazard_key=hazard_key, pending=pending)
    session["spi_conversation_state"] = state
    return result

def assistant_mode_label() -> str:
    from .provider import provider_configured
    return "Hybrid AI enabled" if provider_configured() else "Local AI mode (API not configured)"
