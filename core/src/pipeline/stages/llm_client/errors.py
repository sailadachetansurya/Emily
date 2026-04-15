from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OllamaError(Exception):
    stage: str
    part: str
    detail: str
    hint: str = ""

    def __str__(self) -> str:
        suffix = f" Hint: {self.hint}" if self.hint else ""
        return f"[{self.stage}::{self.part}] {self.detail}{suffix}"


class OllamaContractError(OllamaError):
    pass


class OllamaConfigurationError(OllamaError):
    pass


class OllamaResponseParseError(OllamaError):
    pass


class OllamaTransportError(OllamaError):
    pass
