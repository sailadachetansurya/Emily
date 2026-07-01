from dataclasses import dataclass
from pathlib import Path
import json
from re import IGNORECASE, sub

from pipeline.contracts.interfaces import LLMClient
from pipeline.contracts.models import GenerationResult, PromptBundle, PrunedResponse, ResponsePolicy, SafeResponse


@dataclass(frozen=True)
class SpeechActResult:
    speech_act: str
    confidence: float


class OutputPruner:
    """Project raw model output into a constrained fit space using Python rules."""

    def __init__(self, config_path: str = "configs/safety_config.json") -> None:
        self.config_path = Path(config_path)
        self.config = self._load_config()

    def prune(self, generation: GenerationResult, policy: ResponsePolicy) -> PrunedResponse:
        text = self.apply_pattern_filters(generation.raw_text)
        notes: list[str] = []
        classification = self.classify_speech_act(text)
        speech_act = classification.speech_act
        confidence = classification.confidence

        if speech_act not in policy.allowed_speech_acts:
            text = self.project_to_allowed_space(text, policy)
            reclassified = self.classify_speech_act(text)
            speech_act = reclassified.speech_act
            confidence = reclassified.confidence
            if speech_act not in policy.allowed_speech_acts:
                notes.append(f"Speech act '{speech_act}' not allowed for mode '{policy.mode}'")

        text = self.normalize_style(text)
        return PrunedResponse(
            text=text,
            speech_act=speech_act,
            was_regenerated=False,
            pruning_notes=notes,
        )

    def classify_speech_act(self, text: str) -> SpeechActResult:
        lowered = text.lower().strip()
        if not lowered:
            return SpeechActResult("statement", 0.5)

        hits = 0
        total_markers = 0

        if lowered.endswith("?") or "?" in lowered:
            return SpeechActResult("question", 0.9)

        reflect_markers = ["i hear", "that sounds", "it makes sense", "i can see", "it sounds like", "i understand"]
        reflect_hits = sum(1 for m in reflect_markers if m in lowered)
        total_markers += len(reflect_markers)
        hits += reflect_hits

        advice_markers = ["try", "consider", "suggest", "maybe you should"]
        advice_hits = sum(1 for m in advice_markers if m in lowered)
        total_markers += len(advice_markers)
        hits += advice_hits

        presence_markers = ["here with you", "i am with you", "stay with you", "with you in this"]
        presence_hits = sum(1 for m in presence_markers if m in lowered)
        total_markers += len(presence_markers)
        hits += presence_hits

        if reflect_hits > 0:
            conf = min(0.6 + reflect_hits * 0.15, 0.95)
            return SpeechActResult("reflect", conf)
        if advice_hits > 0:
            conf = min(0.6 + advice_hits * 0.15, 0.95)
            return SpeechActResult("advice", conf)
        if presence_hits > 0:
            conf = min(0.6 + presence_hits * 0.15, 0.95)
            return SpeechActResult("presence", conf)

        return SpeechActResult("statement", 0.5)

    def apply_pattern_filters(self, text: str) -> str:
        forbidden = self.config.get("forbidden_phrases", ["you should", "you need to", "always", "never"])
        replacements = {phrase: "" for phrase in forbidden}
        replacements.update({"diagnosis": "", "diagnose": "", "only I": "", "only me": ""})
        filtered = text
        for phrase, replacement in replacements.items():
            filtered = sub(phrase, replacement, filtered, flags=IGNORECASE, count=0)
        return " ".join(filtered.split())

    def project_to_allowed_space(self, text: str, policy: ResponsePolicy) -> str:
        if "reflect" in policy.allowed_speech_acts:
            return self.force_reflection(text)
        if "question" in policy.allowed_speech_acts:
            return self.force_soft_question(text)
        return self.force_presence(text)

    def force_reflection(self, text: str) -> str:
        core = self.strip_questions(text)
        if not core:
            return "I hear you. That sounds difficult."
        return core

    def force_soft_question(self, text: str) -> str:
        core = self.strip_questions(text).strip().rstrip(".")
        if not core:
            return "What feels most present for you right now?"
        if core.endswith("?"):
            return core
        return f"Would it help to talk more about {core.lower()}?"

    def force_presence(self, text: str) -> str:
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


class LLMOutputPruner:
    """Use the LLM itself to rewrite output to comply with policy rules."""

    def __init__(self, llm_client: LLMClient, config_path: str = "configs/safety_config.json") -> None:
        self.llm_client = llm_client
        self.config_path = Path(config_path)
        self.config = self._load_config()

    def prune(self, generation: GenerationResult, policy: ResponsePolicy) -> PrunedResponse:
        prompt_text = self._build_pruning_prompt(generation.raw_text, policy)
        bundle = PromptBundle(
            system_prompt=prompt_text,
            user_prompt="",
            context_blocks=[],
            generation_params={
                "max_tokens": 150,
                "temperature": 0.3,
            },
        )
        result = self.llm_client.generate(bundle)
        pruned_text = result.raw_text.strip() if result.raw_text.strip() else generation.raw_text

        classification = self._classify(pruned_text)
        notes = []
        if classification not in policy.allowed_speech_acts:
            notes.append(f"LLM pruned output still has speech act '{classification}'")

        return PrunedResponse(
            text=pruned_text,
            speech_act=classification,
            was_regenerated=(pruned_text != generation.raw_text),
            pruning_notes=notes,
        )

    def _build_pruning_prompt(self, text: str, policy: ResponsePolicy) -> str:
        allowed = ", ".join(policy.allowed_speech_acts) or "any"
        return (
            "You are a response editor. Rewrite the following response to comply with these rules:\n"
            f"- Allowed speech acts: {allowed}\n"
            f"- Policy mode: {policy.mode}\n"
            "- Keep the meaning and emotional tone intact\n"
            "- Do not add diagnostic or advisory language\n"
            "- Keep it concise (1-3 sentences)\n"
            "- Output ONLY the rewritten response, nothing else\n\n"
            f"Original response: {text}"
        )

    def _classify(self, text: str) -> str:
        lowered = text.lower().strip()
        if "?" in lowered:
            return "question"
        if any(m in lowered for m in ["i hear", "that sounds", "it makes sense", "i can see", "it sounds like", "i understand"]):
            return "reflect"
        if any(m in lowered for m in ["try", "consider", "suggest"]):
            return "advice"
        if any(m in lowered for m in ["here with you", "i am with you", "with you in this"]):
            return "presence"
        return "statement"

    def _load_config(self) -> dict[str, object]:
        if not self.config_path.exists():
            return {}
        return json.loads(self.config_path.read_text(encoding="utf-8"))


class AdaptiveSafetyProcessor:
    """Choose between Python and LLM pruning based on confidence threshold."""

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        config_path: str = "configs/safety_config.json",
        pruning_mode: str = "python",
        confidence_threshold: float = 0.9,
    ) -> None:
        self.python_pruner = OutputPruner(config_path)
        self.llm_pruner = LLMOutputPruner(llm_client, config_path) if llm_client else None
        self.pruning_mode = pruning_mode
        self.confidence_threshold = confidence_threshold

    def validate(self, generation: GenerationResult, policy: ResponsePolicy) -> SafeResponse:
        raw_text = generation.raw_text

        if self.pruning_mode == "off":
            classification = self.python_pruner.classify_speech_act(raw_text)
            return SafeResponse(
                text=raw_text,
                was_regenerated=False,
                safety_notes=[],
                raw_text=raw_text,
                pruning_method="none",
            )

        python_result = self.python_pruner.prune(generation, policy)
        classification = self.python_pruner.classify_speech_act(raw_text)

        if self.pruning_mode == "python" or self.llm_pruner is None:
            return SafeResponse(
                text=python_result.text,
                was_regenerated=python_result.was_regenerated,
                safety_notes=python_result.pruning_notes,
                raw_text=raw_text,
                pruning_method="python",
            )

        if classification.confidence >= self.confidence_threshold and classification.speech_act not in policy.allowed_speech_acts:
            llm_result = self.llm_pruner.prune(generation, policy)
            return SafeResponse(
                text=llm_result.text,
                was_regenerated=llm_result.was_regenerated,
                safety_notes=llm_result.pruning_notes,
                raw_text=raw_text,
                pruning_method="llm",
            )

        return SafeResponse(
            text=python_result.text,
            was_regenerated=python_result.was_regenerated,
            safety_notes=python_result.pruning_notes,
            raw_text=raw_text,
            pruning_method="python",
        )


class ProjectionSafetyProcessor(AdaptiveSafetyProcessor):
    """Backward-compatible name for the pipeline."""

    def __init__(self, llm_client: LLMClient | None = None, **kwargs) -> None:
        super().__init__(llm_client=llm_client, **kwargs)


class DefaultSafetyProcessor(ProjectionSafetyProcessor):
    """Backward-compatible alias."""
