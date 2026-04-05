from dataclasses import dataclass, field
from typing import Any


@dataclass
class RequestEnvelope:
    request_id: str
    user_id: str
    user_input: str
    trace_id: str


@dataclass
class EmotionState:
    emotional_valence: float = 0.0
    activation_level: str = "medium"
    social_orientation: str = "neutral"
    stability: str = "stable"


@dataclass
class MemoryContext:
    factual_facts: list[str] = field(default_factory=list)
    emotional_summary: str = ""


@dataclass
class ResponsePolicy:
    mode: str
    max_tokens: int
    temperature: float
    allowed_speech_acts: list[str]
    disallowed_speech_acts: list[str]


@dataclass
class PromptBundle:
    system_prompt: str
    user_prompt: str
    context_blocks: list[str]
    generation_params: dict[str, Any]


@dataclass
class GenerationResult:
    raw_text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SafeResponse:
    text: str
    was_regenerated: bool = False
    safety_notes: list[str] = field(default_factory=list)
