"""Hybrid conversational orchestration for Safety Precursor Intelligence."""
from __future__ import annotations
from .knowledge import get_playbook
from .memory import detect_short_follow_up
from .models import AssistantResult, ConversationState
from .normalization import normalize_text
from .provider import generate_chat, provider_configured
from .triage import classify_intent, detect_hazard, is_safety_domain
from .humanised_chat import get_humanised_example

EMERGENCY_OPENERS = {
    "electric_shock": "I'm sorry this happened. Please treat an electric shock as an emergency, even if the worker seems okay.",
    "unconsciousness": "This may be a life-threatening emergency. Please activate emergency medical response now.",
    "fire": "Please raise the site alarm and follow the emergency evacuation procedure now.",
    "gas_release": "Please move away from the suspected release and follow the site's gas emergency procedure now.",
    "chemical_spill": "Please keep clear of the unknown substance and notify trained spill responders.",
}

def _numbered(items: tuple[str, ...]) -> str:
    return "\n".join(f"{index}. {item}" for index, item in enumerate(items, 1))

def _follow_up(state: ConversationState, text: str) -> AssistantResult | None:
    follow = detect_short_follow_up(text, state)
    if not follow or not state.pending_intent:
        return None
    if state.pending_intent == "electric_shock":
        if follow in {"not_isolated", "no"}:
            response = ("Keep everyone away. Do not touch the worker or equipment while the source may be live. "
                        "Raise the emergency alarm and have authorized responders isolate the supply. "
                        "Has emergency medical help been contacted?")
        elif follow in {"isolated", "yes", "worker_stable"}:
            response = ("Thank you for clarifying. Keep the area controlled and prevent re-energization. "
                        "The worker still needs prompt medical assessment, even if they feel normal. "
                        "Has the emergency medical or first-aid team reached them?")
        else:
            response = "I want to make sure the scene is safe. Has an authorized responder confirmed the electrical source is isolated?"
        return AssistantResult(response, intent="emergency_follow_up", requires_attention=True, follow_up="Has emergency medical help been contacted?", source="local_rules")
    if state.pending_intent == "fatigue":
        if follow == "scheduled_break":
            response = ("Thanks, that distinction matters. If the worker was on an authorized break in a designated rest area, "
                        "that is different from falling asleep while assigned to a task. Check the site's break and fatigue policy. "
                        "Was the worker actually assigned to duty at that time?")
        elif follow == "safety_critical":
            response = ("That raises the concern. Arrange a safe handover and keep the worker away from driving, machinery or other "
                        "safety-critical duties until the supervisor follows the site's fitness-for-work process. "
                        "Has this happened repeatedly across shifts?")
        else:
            response = "Understood. Was the worker on a scheduled break, or were they expected to be actively working?"
        return AssistantResult(response, intent="fatigue_follow_up", requires_attention=True, follow_up="Was the worker on duty or on a scheduled break?", source="local_rules")
    return None

def _local_hazard_response(match, text: str) -> AssistantResult:
    playbook = get_playbook(match.key)
    if not playbook:
        return AssistantResult("I can see a possible safety concern. Please follow your site procedure and tell me what happened and where.", source="local_rules")
    humanised = get_humanised_example(match.key, text) or {}
    acknowledgement = humanised.get("humanised_acknowledgement")
    emergency_opener = EMERGENCY_OPENERS.get(match.key)
    if emergency_opener:
        opener = f"{acknowledgement} {emergency_opener}" if acknowledgement else emergency_opener
    else:
        opener = acknowledgement or f"Thanks for reporting this. I recognize a {playbook.title.lower()} concern."
    urgency = " **Activate emergency response first; do not wait for this chat.**" if playbook.emergency else ""
    response = (f"{opener}{urgency}\n\n**What to do now**\n{_numbered(playbook.immediate_steps)}"
                f"\n\n**Why it matters**\n{playbook.why}"
                f"\n\n**One question so I can guide the next step:** {playbook.follow_up[0]}"
                "\n\nI can help document the facts once people are safe. This is a screening assistant, not a substitute for your site emergency plan or qualified HSE staff.")
    return AssistantResult(response, intent="hazard_report", hazard=match, requires_attention=match.emergency,
                           follow_up=playbook.follow_up[0], source="local_rules", confidence=match.confidence)

def _general_response(text: str) -> AssistantResult:
    intent = classify_intent(text)
    if intent == "greeting":
        return AssistantResult("Hi! I'm here to help with workplace safety. Tell me what you noticed, describe an incident, or ask me to review safety trends. What's happening at your site?", intent="greeting")
    if any(term in normalize_text(text) for term in ("what is a near miss", "meaning of near miss", "define near miss")):
        return AssistantResult("A **near miss** is an unplanned event that did not cause injury or damage this time but could have. It is worth reporting because it can reveal a hazard before someone is hurt. What happened, and where?", intent="safety_explanation")
    if any(term in normalize_text(text) for term in ("lockout tagout", "lock out tag out", "loto")):
        return AssistantResult("**Lockout/Tagout (LOTO)** is the site's controlled process for isolating hazardous energy so equipment cannot start unexpectedly during work. Only trained and authorized people should follow your approved procedure, verify isolation and release equipment. Are you asking about a specific machine or task?", intent="safety_explanation")
    if "unsafe act" in normalize_text(text):
        return AssistantResult("An **unsafe act** is an action or omission that could expose someone to harm, such as bypassing a guard. Record what was observed factually, without blame, and follow the site's reporting process. Would you like help classifying an example?", intent="safety_explanation")
    if "unsafe condition" in normalize_text(text):
        return AssistantResult("An **unsafe condition** is a hazardous workplace state, such as exposed wiring, a leaking line or an unprotected opening. Record the location, time and controls already taken. Do you have a specific condition to report?", intent="safety_explanation")
    if not is_safety_domain(text):
        return AssistantResult("I'm your workplace safety assistant, so I focus on hazards, incidents, near misses, safe work practices and HSE reports. Tell me what is happening at the site and I'll help you work through it.", intent="out_of_scope")
    return AssistantResult("I can help with that. To avoid guessing, could you tell me **what happened**, **where it happened**, and **whether anyone was injured or exposed**? If there is immediate danger, activate your site's emergency response first.", intent=intent, follow_up="What happened and is anyone in immediate danger?")

def respond(text: str, state: ConversationState | None = None, use_generation: bool = True) -> AssistantResult:
    """Produce a safe answer using local triage and optional natural-language generation."""
    raw = str(text or "").strip()
    if not raw:
        return AssistantResult("I'm listening. Tell me what happened at the workplace.", intent="clarification")
    state = state or ConversationState()
    follow_up = _follow_up(state, raw)
    if follow_up:
        result = follow_up
    else:
        match = detect_hazard(raw)
        if match:
            result = _local_hazard_response(match, raw)
        else:
            result = _general_response(raw)
    # Optional model rewrites the locally grounded answer, never the triage decision.
    # Critical emergency steps are retained in the prompt and fallback remains local.
    if use_generation and provider_configured() and result.source == "local_rules":
        messages = state.recent(limit=10)
        if not messages or messages[-1].get("content") != raw:
            messages.append({"role": "user", "content": raw})
        messages.extend([
            {"role": "assistant", "content": result.text},
            {"role": "user", "content": "Rewrite the assistant response to sound empathetic and conversational. Preserve every safety instruction, urgency statement, uncertainty and follow-up question. Do not add new procedures or remove emergency actions."},
        ])
        generated = generate_chat(messages)
        if generated:
            result.text = generated
            result.source = "hybrid_local_plus_llm"
    return result
