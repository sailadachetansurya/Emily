from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

from pipeline.contracts.models import EmotionState
from pipeline.stages.emotion_engine.nlp_emotion_model import NlpEmotionArchitecture, WhitespaceTokenizer


@dataclass(frozen=True)
class EmotionTrainingExample:
    text: str
    valence: float
    activation: str
    social_orientation: str
    stability: str


@dataclass
class LabelModel:
    labels: list[str] = field(default_factory=list)
    label_counts: dict[str, int] = field(default_factory=dict)
    token_counts: dict[str, dict[str, int]] = field(default_factory=dict)
    token_totals: dict[str, int] = field(default_factory=dict)
    vocabulary: list[str] = field(default_factory=list)


@dataclass
class EmotionTrainingArtifact:
    architecture: dict[str, Any]
    tokenizer: str
    categorical_models: dict[str, LabelModel]
    valence_token_scores: dict[str, float]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        return {
            "architecture": self.architecture,
            "tokenizer": self.tokenizer,
            "categorical_models": {field_name: asdict(model) for field_name, model in self.categorical_models.items()},
            "valence_token_scores": self.valence_token_scores,
            "metadata": self.metadata,
        }

    @classmethod
    def from_json(cls, payload: dict[str, Any]) -> "EmotionTrainingArtifact":
        categorical_models = {
            field_name: LabelModel(**model_payload)
            for field_name, model_payload in payload.get("categorical_models", {}).items()
        }
        return cls(
            architecture=dict(payload.get("architecture", {})),
            tokenizer=str(payload.get("tokenizer", "whitespace")),
            categorical_models=categorical_models,
            valence_token_scores={str(key): float(value) for key, value in payload.get("valence_token_scores", {}).items()},
            metadata=dict(payload.get("metadata", {})),
        )


class TrainingDataError(Exception):
    pass


class EmotionModelTrainer:
    def __init__(self) -> None:
        self.tokenizer = WhitespaceTokenizer()
        self.valid_activation_labels = ["low", "medium", "high"]
        self.valid_social_labels = ["withdrawn", "neutral", "reaching"]
        self.valid_stability_labels = ["stable", "fragile", "volatile"]

    def load_jsonl(self, data_path: str | Path) -> list[EmotionTrainingExample]:
        path = Path(data_path)
        if not path.exists():
            raise TrainingDataError(f"Training data file not found: {path}")

        examples: list[EmotionTrainingExample] = []
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise TrainingDataError(f"Invalid JSON on line {line_number}: {exc}") from exc
            examples.append(self.parse_example(payload, line_number=line_number))

        if not examples:
            raise TrainingDataError(f"No training examples found in {path}")
        return examples

    def parse_example(self, payload: dict[str, Any], line_number: int) -> EmotionTrainingExample:
        required = ["text", "valence", "activation", "social_orientation", "stability"]
        missing = [field for field in required if field not in payload]
        if missing:
            raise TrainingDataError(f"Line {line_number}: missing fields: {', '.join(missing)}")

        text = str(payload["text"]).strip()
        if not text:
            raise TrainingDataError(f"Line {line_number}: text cannot be empty")

        valence = float(payload["valence"])
        if valence < -1.0 or valence > 1.0:
            raise TrainingDataError(f"Line {line_number}: valence must be between -1.0 and 1.0")

        activation = str(payload["activation"]).strip()
        social_orientation = str(payload["social_orientation"]).strip()
        stability = str(payload["stability"]).strip()
        if activation not in self.valid_activation_labels:
            raise TrainingDataError(f"Line {line_number}: invalid activation label '{activation}'")
        if social_orientation not in self.valid_social_labels:
            raise TrainingDataError(f"Line {line_number}: invalid social_orientation label '{social_orientation}'")
        if stability not in self.valid_stability_labels:
            raise TrainingDataError(f"Line {line_number}: invalid stability label '{stability}'")

        return EmotionTrainingExample(
            text=text,
            valence=valence,
            activation=activation,
            social_orientation=social_orientation,
            stability=stability,
        )

    def train(self, examples: Iterable[EmotionTrainingExample]) -> EmotionTrainingArtifact:
        examples = list(examples)
        if not examples:
            raise TrainingDataError("At least one training example is required")

        activation_model = self.train_label_model(examples, field_name="activation")
        social_model = self.train_label_model(examples, field_name="social_orientation")
        stability_model = self.train_label_model(examples, field_name="stability")
        valence_token_scores = self.train_valence_scores(examples)

        return EmotionTrainingArtifact(
            architecture=asdict(NlpEmotionArchitecture()),
            tokenizer="whitespace_lexical_tokenizer",
            categorical_models={
                "activation": activation_model,
                "social_orientation": social_model,
                "stability": stability_model,
            },
            valence_token_scores=valence_token_scores,
            metadata={
                "example_count": len(examples),
                "label_fields": ["activation", "social_orientation", "stability"],
            },
        )

    def train_label_model(self, examples: Iterable[EmotionTrainingExample], field_name: str) -> LabelModel:
        label_counts: Counter[str] = Counter()
        token_counts: dict[str, Counter[str]] = defaultdict(Counter)
        token_totals: Counter[str] = Counter()
        vocabulary: set[str] = set()

        for example in examples:
            label = getattr(example, field_name)
            label_counts[label] += 1
            tokens = self.tokenizer.tokenize(example.text)
            vocabulary.update(tokens)
            token_totals[label] += len(tokens)
            token_counts[label].update(tokens)

        return LabelModel(
            labels=sorted(label_counts.keys()),
            label_counts=dict(label_counts),
            token_counts={label: dict(counts) for label, counts in token_counts.items()},
            token_totals=dict(token_totals),
            vocabulary=sorted(vocabulary),
        )

    def train_valence_scores(self, examples: Iterable[EmotionTrainingExample]) -> dict[str, float]:
        token_sum: defaultdict[str, float] = defaultdict(float)
        token_count: defaultdict[str, int] = defaultdict(int)
        for example in examples:
            tokens = set(self.tokenizer.tokenize(example.text))
            for token in tokens:
                token_sum[token] += example.valence
                token_count[token] += 1

        scores: dict[str, float] = {}
        for token, total in token_sum.items():
            scores[token] = round(total / max(token_count[token], 1), 6)
        return scores

    def save(self, artifact: EmotionTrainingArtifact, output_path: str | Path) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(artifact.to_json(), indent=2, ensure_ascii=False), encoding="utf-8")
        return path


class TrainedEmotionModel:
    def __init__(self, artifact: EmotionTrainingArtifact) -> None:
        self.artifact = artifact
        self.tokenizer = WhitespaceTokenizer()

    @classmethod
    def load(cls, artifact_path: str | Path) -> "TrainedEmotionModel":
        payload = json.loads(Path(artifact_path).read_text(encoding="utf-8"))
        return cls(EmotionTrainingArtifact.from_json(payload))

    def classify(self, text: str) -> EmotionState:
        tokens = self.tokenizer.tokenize(text)
        activation = self.predict_label("activation", tokens)
        social_orientation = self.predict_label("social_orientation", tokens)
        stability = self.predict_label("stability", tokens)
        valence = self.predict_valence(tokens)
        return EmotionState(
            emotional_valence=valence,
            activation_level=activation,
            social_orientation=social_orientation,
            stability=stability,
            signals={"token_count": float(len(tokens))},
        )

    def infer(self, request_or_text: str | object) -> EmotionState:
        if isinstance(request_or_text, str):
            return self.classify(request_or_text)
        return self.classify(str(getattr(request_or_text, "user_input", "")))

    def predict_label(self, field_name: str, tokens: list[str]) -> str:
        model = self.artifact.categorical_models[field_name]
        vocab_size = max(len(model.vocabulary), 1)
        best_label = model.labels[0]
        best_score = float("-inf")
        total_examples = sum(model.label_counts.values())

        for label in model.labels:
            label_count = model.label_counts.get(label, 0)
            prior = math.log((label_count + 1) / (total_examples + len(model.labels)))
            token_total = model.token_totals.get(label, 0)
            score = prior
            label_token_counts = model.token_counts.get(label, {})
            for token in tokens:
                token_count = label_token_counts.get(token, 0)
                score += math.log((token_count + 1) / (token_total + vocab_size))
            if score > best_score:
                best_score = score
                best_label = label
        return best_label

    def predict_valence(self, tokens: list[str]) -> float:
        scores: list[float] = []
        for token in tokens:
            if token in self.artifact.valence_token_scores:
                scores.append(self.artifact.valence_token_scores[token])
        if not scores:
            return 0.0
        average = sum(scores) / len(scores)
        return max(-1.0, min(1.0, round(average, 4)))


def train_from_jsonl(data_path: str | Path, output_path: str | Path) -> Path:
    trainer = EmotionModelTrainer()
    examples = trainer.load_jsonl(data_path)
    artifact = trainer.train(examples)
    return trainer.save(artifact, output_path)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train the sample NLP emotion model from a JSONL dataset.")
    parser.add_argument("--data", required=True, help="Path to the labeled JSONL dataset.")
    parser.add_argument("--output", required=True, help="Path to write the trained model artifact JSON.")
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    output_path = train_from_jsonl(args.data, args.output)
    print(f"Saved trained emotion model to {output_path}")


if __name__ == "__main__":
    main()
