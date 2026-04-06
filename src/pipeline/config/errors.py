from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ConfigValidationError(Exception):
    stage: str
    part: str
    detail: str
    hint: str = ""

    def __str__(self) -> str:
        suffix = f" Hint: {self.hint}" if self.hint else ""
        return f"[{self.stage}::{self.part}] {self.detail}{suffix}"
