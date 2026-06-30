from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ReasoningTrace:
    reasoning_text: str
    chosen_approach: str
    rationale: str
    risk_assessment: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CritiqueResult:
    compliant: bool
    violations: list[str] = field(default_factory=list)
    suggested_fix: str = ""
    score: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class IterationRecord:
    iteration: int
    reasoning_trace: ReasoningTrace | None
    generation_text: str
    critique: CritiqueResult | None
    prompt_variant: str
