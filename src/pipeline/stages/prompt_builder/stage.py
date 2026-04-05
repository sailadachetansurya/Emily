from pipeline.contracts.models import EmotionState, MemoryContext, PromptBundle, RequestEnvelope, ResponsePolicy


class DefaultPromptBuilder:
    def build(self, request: RequestEnvelope, emotion: EmotionState, memory: MemoryContext, policy: ResponsePolicy) -> PromptBundle:
        system_prompt = (
            "You are a warm, emotionally attuned assistant. "
            "Keep responses concise. "
            f"Allowed speech acts: {', '.join(policy.allowed_speech_acts)}. "
            f"Disallowed speech acts: {', '.join(policy.disallowed_speech_acts)}."
        )
        context_blocks = [
            f"Emotion: valence={emotion.emotional_valence}, activation={emotion.activation_level}, orientation={emotion.social_orientation}, stability={emotion.stability}",
            f"Factual memory: {'; '.join(memory.factual_facts)}",
            f"Emotional continuity: {memory.emotional_summary}",
        ]
        user_prompt = request.user_input
        generation_params = {
            "max_tokens": policy.max_tokens,
            "temperature": policy.temperature,
            "mode": policy.mode,
        }
        return PromptBundle(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            context_blocks=context_blocks,
            generation_params=generation_params,
        )
