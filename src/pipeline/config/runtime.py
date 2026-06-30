from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from pipeline.config.errors import ConfigValidationError


RUNTIME_CONFIG_SCHEMA: dict[str, object] = {
    "stage": "config_loader",
    "part": "config.json",
    "required": [
        "model_name",
        "ollama_base_url",
        "request_timeout_seconds",
        "ollama_stream",
        "ollama_generate_path",
        "telemetry_path",
        "max_factual_items",
        "max_emotional_items",
    ],
    "allowed": [
        "model_name",
        "ollama_base_url",
        "request_timeout_seconds",
        "ollama_stream",
        "ollama_generate_path",
        "emotion_model_kind",
        "telemetry_path",
        "max_factual_items",
        "max_emotional_items",
        "reasoning_loop_enabled",
        "reasoning_loop_max_iterations",
        "reasoning_loop_activation_threshold",
        "llm_provider",
        "llamacpp_base_url",
        "llamacpp_n_tokens",
        "episodic_max_exchanges",
        "episodic_ttl_hours",
        "episodic_max_episodes",
    ],
}


@dataclass(frozen=True)
class RuntimeConfig:
    model_name: str = "mistral"
    ollama_base_url: str = "http://localhost:11434"
    request_timeout_seconds: int = 30
    ollama_stream: bool = False
    ollama_generate_path: str = "/api/generate"
    emotion_model_kind: str = "heuristic"
    telemetry_path: str = "logs/pipeline-telemetry.jsonl"
    max_factual_items: int = 32
    max_emotional_items: int = 64
    reasoning_loop_enabled: bool = False
    reasoning_loop_max_iterations: int = 2
    reasoning_loop_activation_threshold: float = 0.5
    llm_provider: str = "ollama"
    llamacpp_base_url: str = "http://localhost:8080"
    llamacpp_n_tokens: int = 256
    episodic_max_exchanges: int = 10
    episodic_ttl_hours: int = 24
    episodic_max_episodes: int = 50


class ConfigLoader:
    def __init__(self, config_path: str = "configs/config.json") -> None:
        self.config_path = Path(config_path)

    def load(self) -> RuntimeConfig:
        if not self.config_path.exists():
            return RuntimeConfig()
        payload = self._load_json()
        self.validate(payload)
        return RuntimeConfig(
            model_name=payload.get("model_name", "mistral"),
            ollama_base_url=payload.get("ollama_base_url", "http://localhost:11434"),
            request_timeout_seconds=payload.get("request_timeout_seconds", 30),
            ollama_stream=payload.get("ollama_stream", False),
            ollama_generate_path=payload.get("ollama_generate_path", "/api/generate"),
            emotion_model_kind=payload.get("emotion_model_kind", "heuristic"),
            telemetry_path=payload.get("telemetry_path", "logs/pipeline-telemetry.jsonl"),
            max_factual_items=payload.get("max_factual_items", 32),
            max_emotional_items=payload.get("max_emotional_items", 64),
            reasoning_loop_enabled=payload.get("reasoning_loop_enabled", False),
            reasoning_loop_max_iterations=payload.get("reasoning_loop_max_iterations", 2),
            reasoning_loop_activation_threshold=payload.get("reasoning_loop_activation_threshold", 0.5),
            llm_provider=payload.get("llm_provider", "ollama"),
            llamacpp_base_url=payload.get("llamacpp_base_url", "http://localhost:8080"),
            llamacpp_n_tokens=payload.get("llamacpp_n_tokens", 256),
            episodic_max_exchanges=payload.get("episodic_max_exchanges", 10),
            episodic_ttl_hours=payload.get("episodic_ttl_hours", 24),
            episodic_max_episodes=payload.get("episodic_max_episodes", 50),
        )

    def validate(self, payload: dict[str, object]) -> None:
        required = RUNTIME_CONFIG_SCHEMA["required"]
        if not isinstance(payload, dict):
            raise ConfigValidationError(
                stage="config_loader",
                part="config.json",
                detail=f"Config must be a JSON object, got {type(payload).__name__}.",
                hint="Use a flat JSON object with the required API and runtime fields.",
            )
        for field_name in required:
            if field_name not in payload:
                raise ConfigValidationError(
                    stage="config_loader",
                    part=field_name,
                    detail=f"Missing required config field '{field_name}'.",
                    hint="Add the missing field to configs/config.json before starting the pipeline.",
                )

        allowed = set(RUNTIME_CONFIG_SCHEMA["allowed"])
        unexpected_fields = [field_name for field_name in payload.keys() if field_name not in allowed]
        if unexpected_fields:
            raise ConfigValidationError(
                stage="config_loader",
                part="config.json",
                detail=f"Unexpected config fields found: {', '.join(sorted(unexpected_fields))}.",
                hint="Remove unknown keys from configs/config.json so the runtime stays inspectable.",
            )

        self._validate_string(payload, "model_name")
        self._validate_string(payload, "ollama_base_url")
        self._validate_string(payload, "ollama_generate_path")
        if "emotion_model_kind" in payload:
            self._validate_string(payload, "emotion_model_kind")
        self._validate_string(payload, "telemetry_path")
        self._validate_bool(payload, "ollama_stream")
        self._validate_int(payload, "request_timeout_seconds", minimum=1)
        self._validate_int(payload, "max_factual_items", minimum=1)
        self._validate_int(payload, "max_emotional_items", minimum=1)

        if "reasoning_loop_enabled" in payload:
            self._validate_bool(payload, "reasoning_loop_enabled")
        if "reasoning_loop_max_iterations" in payload:
            self._validate_int(payload, "reasoning_loop_max_iterations", minimum=1)
        if "reasoning_loop_activation_threshold" in payload:
            self._validate_float(payload, "reasoning_loop_activation_threshold", minimum=0.0, maximum=1.0)

        emotion_model_kind = payload.get("emotion_model_kind", "heuristic")
        if isinstance(emotion_model_kind, str) and emotion_model_kind not in {"heuristic", "nlp_sample"}:
            raise ConfigValidationError(
                stage="config_loader",
                part="emotion_model_kind",
                detail="Config field 'emotion_model_kind' must be 'heuristic' or 'nlp_sample'.",
                hint="Use the heuristic model for rules-based emotion detection or nlp_sample for the sample NLP model.",
            )

    def _load_json(self) -> dict[str, object]:
        try:
            return json.loads(self.config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ConfigValidationError(
                stage="config_loader",
                part="config.json",
                detail=f"Failed to parse config.json: {exc}.",
                hint="Fix the JSON syntax in configs/config.json.",
            ) from exc

    def _validate_string(self, payload: dict[str, object], field_name: str) -> None:
        value = payload.get(field_name)
        if not isinstance(value, str) or not value.strip():
            raise ConfigValidationError(
                stage="config_loader",
                part=field_name,
                detail=f"Config field '{field_name}' must be a non-empty string.",
                hint="Set a valid string value in configs/config.json.",
            )

    def _validate_bool(self, payload: dict[str, object], field_name: str) -> None:
        value = payload.get(field_name)
        if not isinstance(value, bool):
            raise ConfigValidationError(
                stage="config_loader",
                part=field_name,
                detail=f"Config field '{field_name}' must be a boolean.",
                hint="Set true or false in configs/config.json.",
            )

    def _validate_int(self, payload: dict[str, object], field_name: str, minimum: int | None = None) -> None:
        value = payload.get(field_name)
        if not isinstance(value, int) or isinstance(value, bool):
            raise ConfigValidationError(
                stage="config_loader",
                part=field_name,
                detail=f"Config field '{field_name}' must be an integer.",
                hint="Set a whole number value in configs/config.json.",
            )
        if minimum is not None and value < minimum:
            raise ConfigValidationError(
                stage="config_loader",
                part=field_name,
                detail=f"Config field '{field_name}' must be at least {minimum}.",
                hint="Increase the configured value in configs/config.json.",
            )

    def _validate_float(self, payload: dict[str, object], field_name: str, minimum: float | None = None, maximum: float | None = None) -> None:
        value = payload.get(field_name)
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ConfigValidationError(
                stage="config_loader",
                part=field_name,
                detail=f"Config field '{field_name}' must be a number.",
                hint="Set a numeric value in configs/config.json.",
            )
        if minimum is not None and value < minimum:
            raise ConfigValidationError(
                stage="config_loader",
                part=field_name,
                detail=f"Config field '{field_name}' must be at least {minimum}.",
                hint="Increase the configured value in configs/config.json.",
            )
        if maximum is not None and value > maximum:
            raise ConfigValidationError(
                stage="config_loader",
                part=field_name,
                detail=f"Config field '{field_name}' must be at most {maximum}.",
                hint="Decrease the configured value in configs/config.json.",
            )
