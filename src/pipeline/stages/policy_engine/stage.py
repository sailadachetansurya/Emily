from pipeline.contracts.models import EmotionState, MemoryContext, RequestEnvelope, ResponsePolicy


class RuleBasedPolicyEngine:
    def select(self, request: RequestEnvelope, emotion: EmotionState, memory: MemoryContext) -> ResponsePolicy:
        _ = (request, memory)
        if emotion.stability == "fragile" or emotion.activation_level == "high":
            return ResponsePolicy(
                mode="reflection",
                max_tokens=80,
                temperature=0.7,
                allowed_speech_acts=["reflect", "validate", "wonder"],
                disallowed_speech_acts=["advise", "diagnose", "optimize"],
            )
        return ResponsePolicy(
            mode="soft-question",
            max_tokens=120,
            temperature=0.8,
            allowed_speech_acts=["reflect", "validate", "question"],
            disallowed_speech_acts=["diagnose"],
        )
