from pipeline.contracts.models import GenerationResult, ResponsePolicy, SafeResponse


class DefaultSafetyProcessor:
    def validate(self, generation: GenerationResult, policy: ResponsePolicy) -> SafeResponse:
        text = generation.raw_text
        notes: list[str] = []

        forbidden = ["you should", "you need to", "always", "never"]
        for phrase in forbidden:
            if phrase in text.lower():
                notes.append(f"Removed forbidden phrase: {phrase}")
                text = text.replace(phrase, "")

        for disallowed in policy.disallowed_speech_acts:
            if disallowed == "diagnose" and "diagnosis" in text.lower():
                notes.append("Potential diagnostic framing removed")
                text = "I hear you, and I want to stay present with what you are feeling right now."

        return SafeResponse(text=text.strip(), was_regenerated=False, safety_notes=notes)
