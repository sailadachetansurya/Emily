from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class JsonTelemetrySink:
    output_path: str = "logs/pipeline-telemetry.jsonl"
    _buffer: list[dict[str, object]] = field(default_factory=list)

    def emit(self, trace_name: str, payload: dict[str, object]) -> None:
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "trace_name": trace_name,
            "payload": payload,
        }
        self._buffer.append(record)
        path = Path(self.output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
