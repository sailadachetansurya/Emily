from pipeline.contracts.models import EmotionState, MemoryContext, PromptBundle, RequestEnvelope, ResponsePolicy


class PromptAssembler:
    """Compose the final model prompt from state, memory, and policy inputs."""

    def build(self, request: RequestEnvelope, emotion: EmotionState, memory: MemoryContext, policy: ResponsePolicy) -> PromptBundle:
        system_prompt = self.build_system_prompt(policy)
        context_blocks = self.build_context_blocks(emotion, memory)
        generation_params = self.build_generation_params(policy)
        do_not_constraints = self.build_do_not_constraints(policy)
        return PromptBundle(
            system_prompt=system_prompt,
            user_prompt=request.user_input,
            context_blocks=context_blocks,
            generation_params=generation_params,
            do_not_constraints=do_not_constraints,
        )

    def build_system_prompt(self, policy: ResponsePolicy) -> str:
        allowed = ", ".join(policy.allowed_speech_acts) or "none"
        disallowed = ", ".join(policy.disallowed_speech_acts) or "none"
        return (
            "You are Emily the emotive AI, a warm, emotionally attuned assistant. "
            "Keep responses concise and grounded. "
            f"Allowed speech acts: {allowed}. "
            f"Disallowed speech acts: {disallowed}."
        )

    def build_context_blocks(self, emotion: EmotionState, memory: MemoryContext) -> list[str]:
        factual = "; ".join(f"{key}={value}" for key, value in memory.factual_facts.items()) if memory.factual_facts else "none"
        emotional_records = " | ".join(record.get("summary", "") for record in memory.emotional_records) if memory.emotional_records else "none"
        return [
            self.format_emotion(emotion),
            f"Factual memory: {factual}",
            f"Emotional continuity: {memory.emotional_summary or 'none'}",
            f"Emotional matches: {emotional_records}",
        ]

    def build_generation_params(self, policy: ResponsePolicy) -> dict[str, object]:
        return {
            "max_tokens": policy.max_tokens,
            "temperature": policy.temperature,
            "mode": policy.mode,
            "top_p": 0.9,
            "presence_penalty": 0.1,
            "frequency_penalty": 0.1,
        }

    def build_do_not_constraints(self, policy: ResponsePolicy) -> list[str]:
        constraints = [
            "DO NOT use diagnostic language.",
            "DO NOT claim authority or exclusivity.",
            "DO NOT give unasked-for advice.",
        ]
        constraints.extend(f"DO NOT produce {speech_act} speech acts when not allowed." for speech_act in policy.disallowed_speech_acts)
        return constraints

    def format_emotion(self, emotion: EmotionState) -> str:
        return (
            "Emotion: "
            f"valence={emotion.emotional_valence}, "
            f"activation={emotion.activation_level}, "
            f"orientation={emotion.social_orientation}, "
            f"stability={emotion.stability}"
        )


class DefaultPromptBuilder(PromptAssembler):
    """Backward-compatible alias for the baseline pipeline."""

