from dataclasses import dataclass

from pipeline.contracts.models import EmotionState, MemoryContext, RequestEnvelope
from pipeline.stages.memory_manager.emotional_memory import EmotionalMemoryStore
from pipeline.stages.memory_manager.factual_memory import FactualMemoryStore


@dataclass
class MemorySignals:
    factual_keys: list[str]
    emotional_summary: str
    emotional_matches: list[dict[str, object]]


class DualMemoryManager:
    """Owns factual and emotional memory without storing raw conversation transcripts long-term."""

    def __init__(self, factual_store: FactualMemoryStore | None = None, emotional_store: EmotionalMemoryStore | None = None) -> None:
        self.factual_store = factual_store or FactualMemoryStore()
        self.emotional_store = emotional_store or EmotionalMemoryStore()

    def resolve(self, request: RequestEnvelope, emotion: EmotionState) -> MemoryContext:
        emotional_query = self.build_emotional_query(request, emotion)
        emotional_matches = self.emotional_store.query(request.user_id, emotional_query, top_k=3)
        emotional_summary = self.emotional_store.summarize(request.user_id)
        factual_facts = self.factual_store.get_all(request.user_id)
        return MemoryContext(
            factual_facts=factual_facts,
            emotional_summary=emotional_summary,
            emotional_records=[self.record_to_dict(record) for record in emotional_matches],
        )

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
