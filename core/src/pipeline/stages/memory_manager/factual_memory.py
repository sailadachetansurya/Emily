from dataclasses import dataclass, field
from datetime import datetime, timezone

from pipeline.contracts.models import FactualMemoryRecord


@dataclass
class FactualMemoryStore:
    max_items: int = 32
    _records: dict[str, dict[str, FactualMemoryRecord]] = field(default_factory=dict)

    def upsert(self, user_id: str, key: str, value: str, confidence: float = 1.0) -> None:
        user_records = self._records.setdefault(user_id, {})
        user_records[key] = FactualMemoryRecord(
            key=key,
            value=value,
            confidence=confidence,
            updated_at=self._now(),
        )
        self._trim(user_id)

    def get_all(self, user_id: str) -> dict[str, str]:
        user_records = self._records.get(user_id, {})
        return {key: record.value for key, record in user_records.items()}

    def _trim(self, user_id: str) -> None:
        user_records = self._records.get(user_id, {})
        if len(user_records) <= self.max_items:
            return
        ordered = sorted(user_records.values(), key=lambda record: (record.confidence, record.updated_at))
        to_drop = len(user_records) - self.max_items
        for record in ordered[:to_drop]:
            user_records.pop(record.key, None)

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()
