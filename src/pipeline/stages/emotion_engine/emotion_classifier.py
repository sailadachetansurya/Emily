from dataclasses import dataclass
from typing import Protocol

from pipeline.contracts.models import EmotionState, RequestEnvelope


class EmotionClassifierPlugin(Protocol):
    def classify(self, text: str) -> EmotionState:
        ...


@dataclass(frozen=True)
class EmotionRule:
    keywords: tuple[str, ...]
    valence: float
    activation: str
    social_orientation: str
    stability: str
    signal_key: str


class HeuristicEmotionEngine:
    """Deterministic emotion perception with a plugin escape hatch."""

    def __init__(self, plugin: EmotionClassifierPlugin | None = None) -> None:
        self.plugin = plugin
        self.rules = [
            EmotionRule(("anxious", "worried", "scared", "panic"), -0.45, "high", "reaching", "fragile", "anxiety"),
            EmotionRule(("sad", "lonely", "empty", "down"), -0.55, "low", "withdrawn", "fragile", "sadness"),
            EmotionRule(("angry", "frustrated", "irritated"), -0.25, "high", "reaching", "volatile", "anger"),
            EmotionRule(("happy", "good", "excited", "glad"), 0.55, "medium", "reaching", "stable", "positive"),
        ]

    def infer(self, request: RequestEnvelope) -> EmotionState:
        if self.plugin is not None:
            return self.plugin.classify(request.user_input)

        text = request.user_input.lower()
        exclamation_boost = min(text.count("!") * 0.05, 0.2)
        question_boost = min(text.count("?") * 0.03, 0.1)
        base = EmotionState()
        base.signals = {"exclamation_boost": exclamation_boost, "question_boost": question_boost}

        matched = self.match_rule(text)
        if matched is None:
            if any(token in text for token in ["maybe", "not sure", "uncertain", "kind of"]):
                base.emotional_valence = -0.05
                base.activation_level = "medium"
                base.social_orientation = "neutral"
                base.stability = "stable"
            return base

        base.emotional_valence = max(-1.0, min(1.0, matched.valence + exclamation_boost - question_boost))
        base.activation_level = matched.activation
        base.social_orientation = matched.social_orientation
        base.stability = matched.stability
        base.signals[matched.signal_key] = 1.0
        return base

    def match_rule(self, text: str) -> EmotionRule | None:
        for rule in self.rules:
            if any(keyword in text for keyword in rule.keywords):
                return rule
        return None


class HeuristicEmotionClassifier(HeuristicEmotionEngine):
    """Backward-compatible alias."""
