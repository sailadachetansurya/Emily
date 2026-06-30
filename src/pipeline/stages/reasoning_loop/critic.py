from __future__ import annotations

import json
from dataclasses import dataclass

from pipeline.contracts.models import GenerationResult, PromptBundle, ResponsePolicy
from pipeline.stages.llm_client import LocalLLMClient

from .models import CritiqueResult, ReasoningTrace
from .prompts import build_critique_prompt


class PolicyCritiqueEvaluator:
    def __init__(self, llm_client: LocalLLMClient, max_tokens: int = 100, temperature: float = 0.2) -> None:
        self.llm_client = llm_client
        self.max_tokens = max_tokens
        self.temperature = temperature

    def evaluate(
        self,
        generation: GenerationResult,
        policy: ResponsePolicy,
        reasoning_trace: ReasoningTrace,
    ) -> CritiqueResult:
        prompt_text = build_critique_prompt(
            policy_mode=policy.mode,
            allowed_acts=policy.allowed_speech_acts,
            disallowed_acts=policy.disallowed_speech_acts,
            response_text=generation.raw_text,
            reasoning_rationale=reasoning_trace.rationale,
        )
        bundle = PromptBundle(
            system_prompt=prompt_text,
            user_prompt="",
            context_blocks=[],
            generation_params={
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
            },
        )
        result = self.llm_client.generate(bundle)
        return self._parse_critique(result.raw_text)

    def _parse_critique(self, raw_text: str) -> CritiqueResult:
        try:
            cleaned = raw_text.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                lines = [line for line in lines if not line.strip().startswith("```")]
                cleaned = "\n".join(lines)
            payload = json.loads(cleaned)
            return CritiqueResult(
                compliant=bool(payload.get("compliant", True)),
                violations=list(payload.get("violations", [])),
                suggested_fix=str(payload.get("suggested_fix", "")),
                score=float(payload.get("score", 1.0)),
            )
        except (json.JSONDecodeError, ValueError, TypeError):
            return CritiqueResult(compliant=True)
