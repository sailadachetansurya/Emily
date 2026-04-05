from pipeline.contracts.models import EmotionState, MemoryContext, RequestEnvelope


class InMemoryMemoryManager:
    def __init__(self) -> None:
        self._facts: dict[str, list[str]] = {}
        self._emotion_summaries: dict[str, str] = {}

    def resolve(self, request: RequestEnvelope, emotion: EmotionState) -> MemoryContext:
        facts = self._facts.get(request.user_id, ["No stored user facts yet."])
        summary = self._emotion_summaries.get(
            request.user_id,
            f"Current tendency: valence={emotion.emotional_valence}, stability={emotion.stability}",
        )
        return MemoryContext(factual_facts=facts, emotional_summary=summary)
