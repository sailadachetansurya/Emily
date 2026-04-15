from dataclasses import dataclass
from pathlib import Path
import json
from re import IGNORECASE, sub

from pipeline.contracts.models import GenerationResult, PrunedResponse, ResponsePolicy, SafeResponse


@dataclass(frozen=True)
class SpeechActResult:
    speech_act: str
    confidence: float


class OutputPruner:
    """Project raw model output into a constrained fit space."""

    def __init__(self, config_path: str = "configs/safety_config.json") -> None:
        self.config_path = Path(config_path)
        self.config = self._load_config()

    def prune(self, generation: GenerationResult, policy: ResponsePolicy) -> PrunedResponse:
        text = self.apply_pattern_filters(generation.raw_text)
        notes: list[str] = []
        speech_act = self.classify_speech_act(text)
        if speech_act not in policy.allowed_speech_acts:
            text = self.project_to_allowed_space(text, policy)
            speech_act = self.classify_speech_act(text)
            if speech_act not in policy.allowed_speech_acts:
                notes.append(f"Speech act '{speech_act}' not allowed for mode '{policy.mode}'")
        text = self.normalize_style(text)
        return PrunedResponse(text=text, speech_act=speech_act, was_regenerated=False, pruning_notes=notes)

    def apply_pattern_filters(self, text: str) -> str:
        forbidden = self.config.get("forbidden_phrases", ["you should", "you need to", "always", "never"])
        replacements = {phrase: "" for phrase in forbidden}
        replacements.update({"diagnosis": "", "diagnose": "", "only I": "", "only me": ""})
        filtered = text
        for phrase, replacement in replacements.items():
            filtered = sub(phrase, replacement, filtered, flags=IGNORECASE, count=0)
        return " ".join(filtered.split())

    def classify_speech_act(self, text: str) -> str:
        lowered = text.lower()
        if lowered.endswith("?") or lowered.count("?") > 0:
            return "question"
        if any(marker in lowered for marker in ["i hear", "that sounds", "it makes sense", "i can see", "it sounds like"]):
            return "reflect"
        if any(marker in lowered for marker in ["try", "consider", "suggest", "maybe"]):
            return "advice"
        if any(marker in lowered for marker in ["here with you", "i am with you", "stay with you"]):
            return "presence"
        return "statement"

    def project_to_allowed_space(self, text: str, policy: ResponsePolicy) -> str:
        if "reflect" in policy.allowed_speech_acts:
            return self.force_reflection(text)
        if "question" in policy.allowed_speech_acts:
            return self.force_soft_question(text)
        return self.force_presence(text)

    def force_reflection(self, text: str) -> str:
        core = self.strip_questions(text)
        if not core:
            return "It sounds like you are carrying a lot right now."
        if "sounds heavy" in core.lower():
            return "It sounds like this feels heavy right now."
        return f"It sounds like {core.lower()}"

    def force_soft_question(self, text: str) -> str:
        core = self.strip_questions(text).strip().rstrip(".")
        if core.endswith("?"):
            return core
        return f"Would it help to explore what feels most present in {core.lower()}?"

    def force_presence(self, text: str) -> str:
        _ = text
        return "I am here with you in this moment."

    def normalize_style(self, text: str) -> str:
        sentences = [sentence.strip() for sentence in text.replace("\n", " ").split(".") if sentence.strip()]
        max_sentences = int(self.config.get("max_sentences", 4))
        if len(sentences) > max_sentences:
            sentences = sentences[:max_sentences]
        normalized = ". ".join(sentences)
        if normalized and not normalized.endswith((".", "?", "!")):
            normalized += "."
        return normalized

    def strip_questions(self, text: str) -> str:
        cleaned = text.replace("?", ".")
        parts = [part.strip() for part in cleaned.split(".") if part.strip()]
        if not parts:
            return ""
        return parts[0]

    def _load_config(self) -> dict[str, object]:
        if not self.config_path.exists():
            return {}
        return json.loads(self.config_path.read_text(encoding="utf-8"))


class ProjectionSafetyProcessor(OutputPruner):
    def validate(self, generation: GenerationResult, policy: ResponsePolicy) -> SafeResponse:
        pruned = self.prune(generation, policy)
        return SafeResponse(text=pruned.text, was_regenerated=pruned.was_regenerated, safety_notes=pruned.pruning_notes)


class DefaultSafetyProcessor(ProjectionSafetyProcessor):
    """Backward-compatible alias."""
