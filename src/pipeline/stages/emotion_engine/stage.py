from pipeline.contracts.models import EmotionState, RequestEnvelope


class HeuristicEmotionEngine:
    def infer(self, request: RequestEnvelope) -> EmotionState:
        text = request.user_input.lower()
        if any(word in text for word in ["anxious", "worried", "scared"]):
            return EmotionState(-0.4, "high", "reaching", "fragile")
        if any(word in text for word in ["sad", "lonely", "empty"]):
            return EmotionState(-0.5, "low", "withdrawn", "fragile")
        if any(word in text for word in ["happy", "good", "excited"]):
            return EmotionState(0.6, "medium", "reaching", "stable")
        return EmotionState()
