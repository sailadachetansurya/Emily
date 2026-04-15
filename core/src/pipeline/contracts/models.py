from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class RequestEnvelope:
    request_id: str
    user_id: str
    user_input: str
    trace_id: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EmotionState:
    emotional_valence: float = 0.0
    activation_level: Literal["low", "medium", "high"] = "medium"
    social_orientation: Literal["withdrawn", "neutral", "reaching"] = "neutral"
    stability: Literal["stable", "fragile", "volatile"] = "stable"
    signals: dict[str, float] = field(default_factory=dict)

    def valence_is_negative(self) -> bool:
        return self.emotional_valence < 0.0


@dataclass
class MemoryContext:
    factual_facts: dict[str, str] = field(default_factory=dict)
    emotional_summary: str = ""
    emotional_records: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class FactualMemoryRecord:
    key: str
    value: str
    confidence: float = 1.0
    updated_at: str = ""


@dataclass
class EmotionalMemoryRecord:
    record_id: str
    summary: str
    embedding: list[float] = field(default_factory=list)
    themes: list[str] = field(default_factory=list)
    triggers: list[str] = field(default_factory=list)
    recency_weight: float = 1.0
    updated_at: str = ""


@dataclass
class ResponsePolicy:
    mode: Literal["reflection", "validation", "soft_question", "brief_presence", "gentle_redirection"]
    max_tokens: int
    temperature: float
    allowed_speech_acts: list[str]
    disallowed_speech_acts: list[str]
    explanation: str = ""
    confidence: float = 1.0


@dataclass
class PromptBundle:
    system_prompt: str
    user_prompt: str
    context_blocks: list[str]
    generation_params: dict[str, Any]
    do_not_constraints: list[str] = field(default_factory=list)


@dataclass
class GenerationResult:
    raw_text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PrunedResponse:
    text: str
    speech_act: str
    was_regenerated: bool = False
    pruning_notes: list[str] = field(default_factory=list)


@dataclass
class SafeResponse:
    text: str
    was_regenerated: bool = False
    safety_notes: list[str] = field(default_factory=list)


@dataclass
class StageTrace:
    stage_name: str
    status: str
    message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineResult:
    request_id: str
    response: SafeResponse
    traces: list[StageTrace] = field(default_factory=list)
