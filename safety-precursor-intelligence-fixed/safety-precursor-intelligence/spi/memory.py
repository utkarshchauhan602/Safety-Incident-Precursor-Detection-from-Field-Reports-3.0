"""Session-scoped conversational memory with explicit privacy boundaries."""
from __future__ import annotations
from .models import ConversationState
from .normalization import normalize_text

FOLLOW_UP_ALIASES = {
    "yes": "yes", "yeah": "yes", "yep": "yes", "no": "no", "nope": "no",
    "power is off": "isolated", "power off": "isolated", "switched off": "isolated",
    "still live": "not_isolated", "still on": "not_isolated", "not yet": "not_isolated",
    "he is fine": "worker_stable", "she is fine": "worker_stable", "fine now": "worker_stable",
    "on break": "scheduled_break", "during break": "scheduled_break",
    "operating machine": "safety_critical", "driving": "safety_critical",
}

def state_from_session(session: dict) -> ConversationState:
    """Hydrate a minimal state object from Streamlit's session dictionary."""
    state = session.get("spi_conversation_state")
    if isinstance(state, ConversationState):
        return state
    state = ConversationState()
    for item in session.get("hse_chat_history", [])[-40:]:
        role = item.get("role", "assistant")
        content = str(item.get("content", ""))
        state.add(role, content)
    session["spi_conversation_state"] = state
    return state

def detect_short_follow_up(text: str, state: ConversationState) -> str | None:
    value = normalize_text(text)
    if len(value.split()) > 10:
        return None
    for phrase, meaning in FOLLOW_UP_ALIASES.items():
        if phrase in value:
            return meaning
    if state.pending_intent == "electric_shock" and value in {"isolated", "safe", "away", "called"}:
        return value
    if state.pending_intent == "fatigue" and any(term in value for term in ("break", "machine", "driving", "night shift")):
        return "task_context"
    return None

def update_state(state: ConversationState, user_text: str, assistant_text: str, hazard_key: str | None = None, pending: str | None = None) -> None:
    state.add("user", user_text)
    state.add("assistant", assistant_text)
    if hazard_key:
        state.last_hazard = hazard_key
    state.pending_intent = pending or hazard_key
    state.last_question = assistant_text.split("?")[-2] + "?" if "?" in assistant_text else None
