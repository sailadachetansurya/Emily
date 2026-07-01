from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

from pipeline.contracts.interfaces import LLMClient
from pipeline.contracts.models import GenerationResult, PromptBundle, ResponsePolicy

from .critic import PolicyCritiqueEvaluator
from .models import CritiqueResult, IterationRecord, ReasoningTrace
from .prompts import (
    build_enhanced_system_prompt,
    build_reasoning_prompt,
    build_tightened_prompt,
)


@dataclass
class ReasoningLoopConfig:
    enabled: bool = False
    max_iterations: int = 2
    activation_threshold: float = 0.5
    reasoning_max_tokens: int = 150
    critic_max_tokens: int = 100
    reasoning_temperature: float = 0.3


class ReasoningLoopOrchestrator:
    def __init__(self, llm_client: LLMClient, config: ReasoningLoopConfig) -> None:
        self.llm_client = llm_client
        self.config = config
        self.critic = PolicyCritiqueEvaluator(
            llm_client,
            max_tokens=config.critic_max_tokens,
        )

    def should_activate(self, score_breakdown: dict[str, float]) -> bool:
        if not self.config.enabled:
            return False
        emotional_risk = score_breakdown.get("emotional_risk", 0.0)
        return emotional_risk >= self.config.activation_threshold

    def process(
        self,
        prompt: PromptBundle,
        policy: ResponsePolicy,
        score_breakdown: dict[str, float],
    ) -> GenerationResult:
        reasoning_trace = self._generate_reasoning(prompt, policy)
        enhanced_prompt = self._build_enhanced_prompt(prompt, reasoning_trace)
        generation = self.llm_client.generate(enhanced_prompt)

        records: list[IterationRecord] = [
            IterationRecord(
                iteration=0,
                reasoning_trace=reasoning_trace,
                generation_text=generation.raw_text,
                critique=None,
                prompt_variant="enhanced",
            )
        ]

        if self.config.max_iterations <= 1:
            return self._attach_records(generation, records)

        current_prompt = enhanced_prompt
        current_generation = generation
        for iteration in range(1, self.config.max_iterations):
            critique = self.critic.evaluate(current_generation, policy, reasoning_trace)
            if critique.compliant:
                records[-1].critique = critique
                break
            current_prompt = build_tightened_prompt(current_prompt, critique, reasoning_trace)
            current_generation = self.llm_client.generate(current_prompt)
            records.append(
                IterationRecord(
                    iteration=iteration,
                    reasoning_trace=reasoning_trace,
                    generation_text=current_generation.raw_text,
                    critique=critique,
                    prompt_variant="tightened",
                )
            )

        return self._attach_records(current_generation, records)

    def _attach_records(self, generation: GenerationResult, records: list[IterationRecord]) -> GenerationResult:
        loop_metadata = {
            "activated": True,
            "iterations": len(records),
            "final_variant": records[-1].prompt_variant if records else "none",
            "iteration_details": [asdict(record) for record in records],
        }
        return GenerationResult(
            raw_text=generation.raw_text,
            metadata={**generation.metadata, "reasoning_loop": loop_metadata},
        )

    def _generate_reasoning(self, prompt: PromptBundle, policy: ResponsePolicy) -> ReasoningTrace:
        emotion_summary = "; ".join(prompt.context_blocks[:1]) if prompt.context_blocks else "unknown"
        memory_summary = "; ".join(prompt.context_blocks[1:3]) if len(prompt.context_blocks) > 1 else "none"
        reasoning_text = build_reasoning_prompt(
            policy_mode=policy.mode,
            allowed_acts=policy.allowed_speech_acts,
            disallowed_acts=policy.disallowed_speech_acts,
            emotion_summary=emotion_summary,
            memory_summary=memory_summary,
            user_input=prompt.user_prompt,
        )
        bundle = PromptBundle(
            system_prompt=reasoning_text,
            user_prompt="",
            context_blocks=[],
            generation_params={
                "max_tokens": self.config.reasoning_max_tokens,
                "temperature": self.config.reasoning_temperature,
            },
        )
        result = self.llm_client.generate(bundle)
        return self._parse_reasoning(result.raw_text)

    def _build_enhanced_prompt(self, prompt: PromptBundle, trace: ReasoningTrace) -> PromptBundle:
        enhanced_system = build_enhanced_system_prompt(prompt.system_prompt, trace)
        return PromptBundle(
            system_prompt=enhanced_system,
            user_prompt=prompt.user_prompt,
            context_blocks=list(prompt.context_blocks),
            generation_params=dict(prompt.generation_params),
            do_not_constraints=list(prompt.do_not_constraints),
        )

    def _parse_reasoning(self, raw_text: str) -> ReasoningTrace:
        default = ReasoningTrace(
            reasoning_text=raw_text,
            chosen_approach="reflect",
            rationale="Defaulting to reflective approach due to parse failure.",
            risk_assessment="Unknown risk.",
        )
        try:
            cleaned = raw_text.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                lines = [line for line in lines if not line.strip().startswith("```")]
                cleaned = "\n".join(lines)
            payload = json.loads(cleaned)
            return ReasoningTrace(
                reasoning_text=raw_text,
                chosen_approach=str(payload.get("chosen_approach", "reflect")),
                rationale=str(payload.get("rationale", "")),
                risk_assessment=str(payload.get("risk_assessment", "")),
            )
        except (json.JSONDecodeError, ValueError, TypeError):
            return default
