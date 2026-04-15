from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

from pipeline.contracts.models import PromptBundle
from pipeline.stages.llm_client.errors import OllamaContractError, OllamaResponseParseError


OLLAMA_PROMPT_REQUEST_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["model", "prompt", "stream", "options"],
    "properties": {
        "model": {"type": "string"},
        "prompt": {"type": "string"},
        "stream": {"type": "boolean"},
        "options": {"type": "object"},
    },
}

OLLAMA_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["model", "response", "done"],
    "properties": {
        "model": {"type": "string"},
        "response": {"type": "string"},
        "done": {"type": "boolean"},
        "total_duration": {"type": ["integer", "null"]},
        "load_duration": {"type": ["integer", "null"]},
        "prompt_eval_count": {"type": ["integer", "null"]},
        "eval_count": {"type": ["integer", "null"]},
    },
}


@dataclass(frozen=True)
class OllamaPromptRequest:
    model: str
    system_prompt: str
    user_prompt: str
    context_blocks: list[str] = field(default_factory=list)
    do_not_constraints: list[str] = field(default_factory=list)
    options: dict[str, Any] = field(default_factory=dict)
    stream: bool = False

    @classmethod
    def from_prompt_bundle(cls, model: str, prompt: PromptBundle, stream: bool = False) -> "OllamaPromptRequest":
        return cls(
            model=model,
            system_prompt=prompt.system_prompt,
            user_prompt=prompt.user_prompt,
            context_blocks=list(prompt.context_blocks),
            do_not_constraints=list(prompt.do_not_constraints),
            options=dict(prompt.generation_params),
            stream=stream,
        )

    def render_prompt(self) -> str:
        blocks = [f"SYSTEM:\n{self.system_prompt}"]
        blocks.extend(f"CONTEXT:\n{block}" for block in self.context_blocks)
        blocks.extend(self.do_not_constraints)
        blocks.append(f"USER:\n{self.user_prompt}")
        return "\n\n".join(blocks)

    def to_payload(self) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "prompt": self.render_prompt(),
            "stream": self.stream,
            "options": self.options,
        }
        validate_schema(
            payload,
            OLLAMA_PROMPT_REQUEST_SCHEMA,
            stage="ollama_contract",
            part="request_payload",
            error_message="Failed to build Ollama prompt payload",
        )
        return payload


@dataclass(frozen=True)
class OllamaResponseContract:
    model: str
    response: str
    done: bool = True
    total_duration: int | None = None
    load_duration: int | None = None
    prompt_eval_count: int | None = None
    eval_count: int | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "OllamaResponseContract":
        validate_schema(
            payload,
            OLLAMA_RESPONSE_SCHEMA,
            stage="ollama_contract",
            part="response_payload",
            error_message="Failed to parse Ollama non-streaming response payload",
        )
        return cls(
            model=str(payload.get("model", "")),
            response=str(payload.get("response", "")),
            done=bool(payload.get("done", True)),
            total_duration=payload.get("total_duration"),
            load_duration=payload.get("load_duration"),
            prompt_eval_count=payload.get("prompt_eval_count"),
            eval_count=payload.get("eval_count"),
            raw=dict(payload),
        )

    @classmethod
    def from_stream_chunks(cls, chunks: Iterable[str | bytes | dict[str, Any]]) -> "OllamaResponseContract":
        response_parts: list[str] = []
        last_payload: dict[str, Any] | None = None
        seen_done = False
        for index, chunk in enumerate(chunks, start=1):
            payload = parse_stream_chunk(chunk, index=index)
            last_payload = payload
            part = str(payload.get("response", ""))
            if part:
                response_parts.append(part)
            if payload.get("done") is True:
                seen_done = True
                break
        if last_payload is None:
            raise OllamaResponseParseError(
                stage="ollama_contract",
                part="stream_chunks",
                detail="No streaming chunks were provided by the Ollama response.",
                hint="Ensure stream=true and the response body contains newline-delimited JSON chunks.",
            )
        if not seen_done:
            raise OllamaResponseParseError(
                stage="ollama_contract",
                part="stream_chunks",
                detail="The Ollama stream ended without a final chunk where done=true.",
                hint="Check the provider connection, request timeout, and whether the stream was truncated.",
            )
        return cls(
            model=str(last_payload.get("model", "")),
            response="".join(response_parts).strip(),
            done=bool(last_payload.get("done", True)),
            total_duration=last_payload.get("total_duration"),
            load_duration=last_payload.get("load_duration"),
            prompt_eval_count=last_payload.get("prompt_eval_count"),
            eval_count=last_payload.get("eval_count"),
            raw=dict(last_payload),
        )

    def to_generation_text(self) -> str:
        return self.response.strip()


def validate_schema(payload: dict[str, Any], schema: dict[str, Any], stage: str, part: str, error_message: str) -> None:
    if not isinstance(payload, dict):
        raise OllamaContractError(
            stage=stage,
            part=part,
            detail=f"{error_message}: expected a JSON object, got {type(payload).__name__}.",
            hint="Verify the Ollama endpoint is returning JSON and not an HTML/error page.",
        )
    required_fields = schema.get("required", [])
    for field_name in required_fields:
        if field_name not in payload:
            raise OllamaContractError(
                stage=stage,
                part=part,
                detail=f"{error_message}: missing required field '{field_name}'.",
                hint="Check the Ollama request/response shape and ensure the field name matches the contract.",
            )
    properties = schema.get("properties", {})
    for field_name, field_schema in properties.items():
        if field_name not in payload:
            continue
        expected_types = field_schema.get("type")
        if not isinstance(expected_types, list):
            expected_types = [expected_types]
        if not matches_json_type(payload[field_name], expected_types):
            expected = ", ".join(str(item) for item in expected_types)
            raise OllamaContractError(
                stage=stage,
                part=part,
                detail=f"{error_message}: field '{field_name}' has invalid type '{type(payload[field_name]).__name__}'. Expected {expected}.",
                hint="Inspect the Ollama payload or adjust the local contract if the upstream schema changed.",
            )


def matches_json_type(value: Any, expected_types: Sequence[str]) -> bool:
    for expected_type in expected_types:
        if expected_type == "string" and isinstance(value, str):
            return True
        if expected_type == "boolean" and isinstance(value, bool):
            return True
        if expected_type == "integer" and isinstance(value, int) and not isinstance(value, bool):
            return True
        if expected_type == "number" and isinstance(value, (int, float)) and not isinstance(value, bool):
            return True
        if expected_type == "object" and isinstance(value, dict):
            return True
        if expected_type == "array" and isinstance(value, list):
            return True
        if expected_type == "null" and value is None:
            return True
    return False


def parse_stream_chunk(chunk: str | bytes | dict[str, Any], index: int) -> dict[str, Any]:
    if isinstance(chunk, dict):
        payload = chunk
    else:
        try:
            if isinstance(chunk, bytes):
                chunk = chunk.decode("utf-8")
            chunk = chunk.strip()
            if not chunk:
                raise ValueError("empty chunk")
            import json

            payload = json.loads(chunk)
        except Exception as exc:
            raise OllamaResponseParseError(
                stage="ollama_contract",
                part=f"stream_chunk_{index}",
                detail=f"Failed to parse streaming chunk {index}: {exc}.",
                hint="Check that the Ollama stream returns newline-delimited JSON chunks.",
            ) from exc
    validate_schema(
        payload,
        {
            "type": "object",
            "required": ["response", "done"],
            "properties": {
                "model": {"type": ["string", "null"]},
                "response": {"type": "string"},
                "done": {"type": "boolean"},
                "total_duration": {"type": ["integer", "null"]},
                "load_duration": {"type": ["integer", "null"]},
                "prompt_eval_count": {"type": ["integer", "null"]},
                "eval_count": {"type": ["integer", "null"]},
            },
        },
        stage="ollama_contract",
        part=f"stream_chunk_{index}",
        error_message=f"Failed to validate Ollama streaming chunk {index}",
    )
    return payload
