from dataclasses import dataclass, field
from datetime import datetime, timezone
from math import sqrt
from re import findall

from pipeline.contracts.models import EmotionalMemoryRecord


@dataclass
class EmotionalMemoryStore:
    max_items: int = 64
    embedding_dim: int = 32
    _records: dict[str, list[EmotionalMemoryRecord]] = field(default_factory=dict)

    def add_summary(
        self,
        user_id: str,
        summary: str,
        themes: list[str] | None = None,
        triggers: list[str] | None = None,
        recency_weight: float = 1.0,
    ) -> EmotionalMemoryRecord:
        record = EmotionalMemoryRecord(
            record_id=self._build_record_id(user_id),
            summary=summary,
            embedding=self.embed(summary),
            themes=themes or [],
            triggers=triggers or [],
            recency_weight=recency_weight,
            updated_at=self._now(),
        )
        records = self._records.setdefault(user_id, [])
        records.append(record)
        self._trim(user_id)
        return record

    def query(self, user_id: str, text: str, top_k: int = 3) -> list[EmotionalMemoryRecord]:
        records = self._records.get(user_id, [])
        if not records:
            return []
        query_embedding = self.embed(text)
        ranked = sorted(
            records,
            key=lambda record: self.score(query_embedding, record.embedding) * record.recency_weight,
            reverse=True,
        )
        return ranked[:top_k]

    def summarize(self, user_id: str) -> str:
        records = self._records.get(user_id, [])
        if not records:
            return "No emotional memory yet."
        recent = sorted(records, key=lambda record: record.updated_at, reverse=True)[:3]
        return " | ".join(record.summary for record in recent)

    def embed(self, text: str) -> list[float]:
        tokens = findall(r"[a-z0-9']+", text.lower())
        vector = [0.0] * self.embedding_dim
        for token in tokens:
            index = sum(ord(ch) for ch in token) % self.embedding_dim
            vector[index] += 1.0
        norm = sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def score(self, left: list[float], right: list[float]) -> float:
        return sum(a * b for a, b in zip(left, right))

    def _trim(self, user_id: str) -> None:
        records = self._records.get(user_id, [])
        if len(records) <= self.max_items:
            return
        records.sort(key=lambda record: (record.recency_weight, record.updated_at), reverse=True)
        del records[self.max_items :]

    def _build_record_id(self, user_id: str) -> str:
        return f"{user_id}-{len(self._records.get(user_id, [])) + 1}"

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()
