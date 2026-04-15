from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from pipeline.contracts.models import EmotionState


@dataclass(frozen=True)
class NlpEmotionArchitecture:
    """Sample NLP architecture for emotion detection.

    Tokenizer -> lexical feature encoder -> emotion projection head -> structured emotion state.
    This is intentionally lightweight and inspectable so it can be swapped with a real model later.
    """

    tokenizer_name: str = "whitespace_lexical_tokenizer"
    encoder_name: str = "lexical_feature_encoder"
    head_name: str = "emotion_projection_head"


class NLPEmotionModel(Protocol):
    def classify(self, text: str) -> EmotionState:
        ...


@dataclass(frozen=True)
class TokenFeatures:
    token_count: int
    question_count: int
    exclamation_count: int
    lexicon_hits: dict[str, int]
    uncertainty_count: int
    intensity_count: int


class WhitespaceTokenizer:
    def tokenize(self, text: str) -> list[str]:
        return [token.strip(".,!?;:\"'()[]{}").lower() for token in text.split() if token.strip()]


class LexicalFeatureEncoder:
    def __init__(self) -> None:
        self.lexicon = {
            "anxiety": {"anxious", "worried", "panic", "scared"},
            "sadness": {"sad", "lonely", "empty", "down"},
            "anger": {"angry", "frustrated", "irritated"},
            "positive": {"happy", "good", "excited", "glad"},
            "uncertainty": {"maybe", "not sure", "uncertain", "kind of"},
            "intensity": {"very", "really", "so", "extremely"},
        }

    def encode(self, raw_text: str, tokens: list[str]) -> TokenFeatures:
        joined = " ".join(tokens)
        lexicon_hits = {name: self._count_hits(joined, terms) for name, terms in self.lexicon.items()}
        return TokenFeatures(
            token_count=len(tokens),
            question_count=raw_text.count("?"),
            exclamation_count=raw_text.count("!"),
            lexicon_hits=lexicon_hits,
            uncertainty_count=lexicon_hits["uncertainty"],
            intensity_count=lexicon_hits["intensity"],
        )

    def _count_hits(self, text: str, terms: set[str]) -> int:
        count = 0
        for term in terms:
            if term in text:
                count += 1
        return count


class EmotionProjectionHead:
    def project(self, features: TokenFeatures) -> EmotionState:
        valence = 0.0
        valence += features.lexicon_hits.get("positive", 0) * 0.25
        valence -= features.lexicon_hits.get("anxiety", 0) * 0.3
        valence -= features.lexicon_hits.get("sadness", 0) * 0.35
        valence -= features.lexicon_hits.get("anger", 0) * 0.25
        valence += features.intensity_count * 0.03
        valence -= features.question_count * 0.02
        valence = max(-1.0, min(1.0, valence))

        activation = "medium"
        if features.exclamation_count > 1 or features.intensity_count > 1:
            activation = "high"
        elif features.token_count <= 4:
            activation = "low"

        social_orientation = "neutral"
        if features.lexicon_hits.get("sadness", 0) or features.lexicon_hits.get("anxiety", 0):
            social_orientation = "withdrawn"
        if features.question_count > 0 or features.uncertainty_count > 0:
            social_orientation = "reaching"

        stability = "stable"
        if features.lexicon_hits.get("anxiety", 0) or features.lexicon_hits.get("sadness", 0):
            stability = "fragile"
        if features.lexicon_hits.get("anger", 0) and features.exclamation_count > 0:
            stability = "volatile"

        signals = {
            "token_count": float(features.token_count),
            "question_count": float(features.question_count),
            "exclamation_count": float(features.exclamation_count),
            "uncertainty_count": float(features.uncertainty_count),
            "intensity_count": float(features.intensity_count),
        }
        for name, count in features.lexicon_hits.items():
            signals[name] = float(count)

        return EmotionState(
            emotional_valence=valence,
            activation_level=activation,
            social_orientation=social_orientation,
            stability=stability,
            signals=signals,
        )


class SampleNLPEmotionModel:
    """Sample architecture that uses a tokenizer, feature encoder, and projection head."""

    def __init__(self) -> None:
        self.architecture = NlpEmotionArchitecture()
        self.tokenizer = WhitespaceTokenizer()
        self.encoder = LexicalFeatureEncoder()
        self.head = EmotionProjectionHead()

    def classify(self, text: str) -> EmotionState:
        tokens = self.tokenizer.tokenize(text)
        features = self.encoder.encode(text, tokens)
        return self.head.project(features)

    def infer(self, request_or_text: str | object) -> EmotionState:
        if isinstance(request_or_text, str):
            return self.classify(request_or_text)
        user_input = getattr(request_or_text, "user_input", "")
        return self.classify(str(user_input))
