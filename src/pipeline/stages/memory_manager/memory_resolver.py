from dataclasses import dataclass

from pipeline.contracts.models import EmotionState, MemoryContext, RequestEnvelope
from pipeline.stages.memory_manager.emotional_memory import EmotionalMemoryStore
from pipeline.stages.memory_manager.episodic_memory import EpisodicMemoryStore, EpisodicMemoryConfig
from pipeline.stages.memory_manager.factual_memory import FactualMemoryStore


@dataclass
class MemorySignals:
    factual_keys: list[str]
    emotional_summary: str
    emotional_matches: list[dict[str, object]]


class DualMemoryManager:
    """Owns factual, emotional, and episodic memory stores."""

    def __init__(
        self,
        factual_store: FactualMemoryStore | None = None,
        emotional_store: EmotionalMemoryStore | None = None,
        episodic_store: EpisodicMemoryStore | None = None,
    ) -> None:
        self.factual_store = factual_store or FactualMemoryStore()
        self.emotional_store = emotional_store or EmotionalMemoryStore()
        self.episodic_store = episodic_store or EpisodicMemoryStore()

    def resolve(self, request: RequestEnvelope, emotion: EmotionState) -> MemoryContext:
        emotional_query = self.build_emotional_query(request, emotion)
        emotional_matches = self.emotional_store.query(request.user_id, emotional_query, top_k=3)
        emotional_summary = self.emotional_store.summarize(request.user_id)
        factual_facts = self.factual_store.get_all(request.user_id)
        episodic_summary = self.episodic_store.get_context_summary(request.user_id)
        episodic_facts = self.episodic_store.get_facts(request.user_id)

        all_facts = dict(factual_facts)
        for fact in episodic_facts[-5:]:
            key = fact[:40]
            all_facts[key] = fact

        combined_emotional = emotional_summary
        if episodic_summary and episodic_summary != "No episodic memory yet.":
            combined_emotional = f"{episodic_summary} | {emotional_summary}" if emotional_summary != "No emotional memory yet." else episodic_summary

        return MemoryContext(
            factual_facts=all_facts,
            emotional_summary=combined_emotional,
            emotional_records=[self.record_to_dict(record) for record in emotional_matches],
        )

    def record_exchange(
        self,
        user_id: str,
        user_input: str,
        response: str,
        emotion_state: EmotionState | None = None,
    ) -> None:
        emotion_dict = {}
        if emotion_state:
            emotion_dict = {
                "valence": emotion_state.emotional_valence,
                "activation": emotion_state.activation_level,
                "stability": emotion_state.stability,
            }
        self.episodic_store.record_exchange(user_id, user_input, response, emotion_dict)

    def remember_fact(self, user_id: str, key: str, value: str, confidence: float = 1.0) -> None:
        self.factual_store.upsert(user_id, key, value, confidence=confidence)

    def remember_emotional_summary(self, user_id: str, summary: str, themes: list[str] | None = None, triggers: list[str] | None = None, recency_weight: float = 1.0) -> None:
        self.emotional_store.add_summary(user_id, summary, themes=themes, triggers=triggers, recency_weight=recency_weight)

    def build_emotional_query(self, request: RequestEnvelope, emotion: EmotionState) -> str:
        signal_bits = [request.user_input, emotion.social_orientation, emotion.stability]
        signal_bits.extend(f"{key}:{value}" for key, value in emotion.signals.items())
        return " ".join(signal_bits)

    def record_to_dict(self, record) -> dict[str, object]:
        return {
            "record_id": record.record_id,
            "summary": record.summary,
            "themes": list(record.themes),
            "triggers": list(record.triggers),
            "recency_weight": record.recency_weight,
            "updated_at": record.updated_at,
        }


class InMemoryMemoryManager(DualMemoryManager):
    """Backward-compatible alias for the pipeline."""
