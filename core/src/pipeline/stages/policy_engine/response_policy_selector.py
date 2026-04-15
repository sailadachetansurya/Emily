from dataclasses import dataclass
from math import fsum
from pathlib import Path
import json

from pipeline.contracts.models import EmotionState, MemoryContext, RequestEnvelope, ResponsePolicy


@dataclass(frozen=True)
class PolicyRule:
    mode: str
    max_tokens: int
    temperature: float
    allowed_speech_acts: list[str]
    disallowed_speech_acts: list[str]
    explanation: str


@dataclass(frozen=True)
class PolicyDecision:
    policy: ResponsePolicy
    score_breakdown: dict[str, float]
    explanation: str


class PolicyEngine:
    """Select a response policy from a compact, reusable rule set."""

    def __init__(self, config_path: str = "configs/policy_config.json") -> None:
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._fragile_rule = PolicyRule(
            mode="reflection",
            max_tokens=self._mode_value("reflection", "max_tokens", 80),
            temperature=self._mode_value("reflection", "temperature", 0.7),
            allowed_speech_acts=["reflect", "validate", "wonder"],
            disallowed_speech_acts=["advise", "diagnose", "optimize"],
            explanation="Use when emotional volatility or fragility is elevated.",
        )
        self._default_rule = PolicyRule(
            mode="soft-question",
            max_tokens=self._mode_value("soft_question", "max_tokens", 120),
            temperature=self._mode_value("soft_question", "temperature", 0.8),
            allowed_speech_acts=["reflect", "validate", "question"],
            disallowed_speech_acts=["diagnose"],
            explanation="Use for neutral or moderately engaged conversational turns.",
        )
        self._brief_rule = PolicyRule(
            mode="brief_presence",
            max_tokens=self._mode_value("brief_presence", "max_tokens", 70),
            temperature=self._mode_value("brief_presence", "temperature", 0.6),
            allowed_speech_acts=["reflect", "validate"],
            disallowed_speech_acts=["advise", "diagnose", "pressure"],
            explanation="Use when the user seems withdrawn or the context is low energy.",
        )
        self._gentle_rule = PolicyRule(
            mode="gentle_redirection",
            max_tokens=self._mode_value("gentle_redirection", "max_tokens", 90),
            temperature=self._mode_value("gentle_redirection", "temperature", 0.7),
            allowed_speech_acts=["reflect", "validate", "redirect"],
            disallowed_speech_acts=["diagnose", "command"],
            explanation="Use when the user is reaching but needs light guidance or pacing.",
        )

    def select(self, request: RequestEnvelope, emotion: EmotionState, memory: MemoryContext) -> ResponsePolicy:
        decision = self.decide(request, emotion, memory)
        return decision.policy

    def decide(self, request: RequestEnvelope, emotion: EmotionState, memory: MemoryContext) -> PolicyDecision:
        _ = request
        score_breakdown = self.score(emotion, memory)
        rule = self.choose_rule(score_breakdown)
        policy = ResponsePolicy(
            mode=rule.mode,
            max_tokens=rule.max_tokens,
            temperature=rule.temperature,
            allowed_speech_acts=list(rule.allowed_speech_acts),
            disallowed_speech_acts=list(rule.disallowed_speech_acts),
            explanation=rule.explanation,
            confidence=self.confidence(score_breakdown),
        )
        return PolicyDecision(policy=policy, score_breakdown=score_breakdown, explanation=rule.explanation)

    def score(self, emotion: EmotionState, memory: MemoryContext) -> dict[str, float]:
        emotional_risk = 0.0
        emotional_risk += 0.7 if emotion.stability == "fragile" else 0.0
        emotional_risk += 0.9 if emotion.stability == "volatile" else 0.0
        emotional_risk += 0.5 if emotion.activation_level == "high" else 0.0
        emotional_risk += 0.3 if emotion.social_orientation == "withdrawn" else 0.0
        emotional_risk += min(len(memory.emotional_records) * 0.05, 0.25)

        presence_need = 0.0
        presence_need += 0.5 if emotion.social_orientation == "withdrawn" else 0.0
        presence_need += 0.3 if emotion.activation_level == "low" else 0.0
        presence_need += 0.2 if emotion.valence_is_negative() else 0.0

        redirection_need = 0.0
        redirection_need += 0.4 if emotion.social_orientation == "reaching" else 0.0
        redirection_need += 0.3 if emotion.activation_level == "medium" else 0.0
        redirection_need += 0.2 if len(memory.factual_facts) > 4 else 0.0

        return {
            "emotional_risk": round(emotional_risk, 3),
            "presence_need": round(presence_need, 3),
            "redirection_need": round(redirection_need, 3),
        }

    def choose_rule(self, score_breakdown: dict[str, float]) -> PolicyRule:
        if score_breakdown["emotional_risk"] >= 1.0:
            return self._fragile_rule
        if score_breakdown["presence_need"] >= 0.6:
            return self._brief_rule
        if score_breakdown["redirection_need"] >= 0.6:
            return self._gentle_rule
        return self._default_rule

    def confidence(self, score_breakdown: dict[str, float]) -> float:
        raw = 1.0 - min(fsum(score_breakdown.values()) / 6.0, 0.45)
        return round(max(0.55, raw), 3)

    def _load_config(self) -> dict[str, object]:
        if not self.config_path.exists():
            return {}
        return json.loads(self.config_path.read_text(encoding="utf-8"))

    def _mode_value(self, mode_name: str, key: str, default: float | int) -> float | int:
        modes = self.config.get("modes", {}) if isinstance(self.config, dict) else {}
        mode = modes.get(mode_name, {}) if isinstance(modes, dict) else {}
        value = mode.get(key, default) if isinstance(mode, dict) else default
        return value


class RuleBasedPolicyEngine(PolicyEngine):
    """Backward-compatible alias for the baseline pipeline."""


class DeterministicPolicyEngine(PolicyEngine):
    """Preferred explicit name for standalone use."""

