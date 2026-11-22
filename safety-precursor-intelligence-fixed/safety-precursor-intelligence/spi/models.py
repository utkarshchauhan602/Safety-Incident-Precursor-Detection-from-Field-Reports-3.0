"""Typed data structures shared by the safety assistant modules."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Optional
import uuid

@dataclass(frozen=True)
class HazardMatch:
    key: str
    title: str
    category: str
    severity: str
    confidence: float
    matched_terms: tuple[str, ...] = ()
    emergency: bool = False

@dataclass
class ConversationTurn:
    role: str
    content: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class ConversationState:
    conversation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    turns: list[ConversationTurn] = field(default_factory=list)
    pending_intent: Optional[str] = None
    pending_slots: dict[str, Any] = field(default_factory=dict)
    last_hazard: Optional[str] = None
    last_question: Optional[str] = None
    language: str = "en"

    def add(self, role: str, content: str, **metadata: Any) -> None:
        self.turns.append(ConversationTurn(role=role, content=content, metadata=metadata))
        self.turns = self.turns[-40:]

    def recent(self, limit: int = 12) -> list[dict[str, str]]:
        return [{"role": turn.role, "content": turn.content} for turn in self.turns[-limit:]]

@dataclass
class AssistantResult:
    text: str
    intent: str = "general_safety"
    hazard: Optional[HazardMatch] = None
    requires_attention: bool = False
    follow_up: Optional[str] = None
    source: str = "local_rules"
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
