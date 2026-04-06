from __future__ import annotations

import json
from dataclasses import dataclass
from json import JSONDecodeError
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pipeline.contracts.models import GenerationResult, PromptBundle
from pipeline.stages.llm_client.contracts import OllamaPromptRequest, OllamaResponseContract
from pipeline.stages.llm_client.errors import (
    OllamaConfigurationError,
    OllamaContractError,
    OllamaResponseParseError,
    OllamaTransportError,
)


@dataclass
class LocalLLMClient:
    model_name: str = "mistral"
    base_url: str = "http://localhost:11434"
    timeout_seconds: int = 30
    generate_path: str = "/api/generate"
    stream: bool = False

    def __post_init__(self) -> None:
        if not self.model_name.strip():
            raise OllamaConfigurationError(
                stage="ollama_client",
                part="model_name",
                detail="The Ollama model name is empty.",
                hint="Set 'model_name' in configs/config.json to a valid local model name such as 'mistral'.",
            )
        if not self.base_url.strip():
            raise OllamaConfigurationError(
                stage="ollama_client",
                part="base_url",
                detail="The Ollama base URL is empty.",
                hint="Set 'ollama_base_url' in configs/config.json to the local Ollama endpoint.",
            )
        if self.timeout_seconds <= 0:
            raise OllamaConfigurationError(
                stage="ollama_client",
                part="timeout_seconds",
                detail="The request timeout must be greater than zero.",
                hint="Increase 'request_timeout_seconds' in configs/config.json.",
            )

    def generate(self, prompt: PromptBundle) -> GenerationResult:
        request_contract = self.build_request_contract(prompt)
        try:
            if self.stream:
                response_contract = self._post_stream(self.generate_path, request_contract.to_payload())
            else:
                response_payload = self._post_json(self.generate_path, request_contract.to_payload())
                response_contract = self.build_response_contract(response_payload)
            return GenerationResult(
                raw_text=response_contract.to_generation_text(),
                metadata={
                    "provider": "ollama",
                    "model": self.model_name,
                    "done": response_contract.done,
                    "stream": self.stream,
                    "endpoint": self.generate_path,
                },
            )
        except (OllamaContractError, OllamaResponseParseError, OllamaConfigurationError) as exc:
            return self.fallback_generation(prompt, error=exc)
        except (HTTPError, URLError, JSONDecodeError, OSError, ValueError) as exc:
            transport_error = OllamaTransportError(
                stage="ollama_client",
                part="transport",
                detail=f"Failed to contact Ollama at '{self.base_url}{self.generate_path}': {exc}.",
                hint="Check the local Ollama service, the model name, and the API path in configs/config.json.",
            )
            return self.fallback_generation(prompt, error=transport_error)

    def compose_prompt(self, prompt: PromptBundle) -> str:
        return self.build_request_contract(prompt).render_prompt()

    def build_request_contract(self, prompt: PromptBundle) -> OllamaPromptRequest:
        return OllamaPromptRequest.from_prompt_bundle(self.model_name, prompt, stream=self.stream)

    def build_response_contract(self, payload: dict[str, object]) -> OllamaResponseContract:
        if not isinstance(payload, dict):
            raise OllamaContractError(
                stage="ollama_client",
                part="response_payload",
                detail="Ollama returned a non-object payload for a non-streaming request.",
                hint="Verify the local Ollama endpoint and confirm the request path is correct.",
            )
        return OllamaResponseContract.from_payload(payload)

    def _post_json(self, path: str, payload: dict[str, object]) -> dict[str, object]:
        data = json.dumps(payload).encode("utf-8")
        request = Request(
            f"{self.base_url}{path}",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=self.timeout_seconds) as response:
            raw = response.read().decode("utf-8")
            try:
                parsed = json.loads(raw)
            except JSONDecodeError as exc:
                raise OllamaResponseParseError(
                    stage="ollama_client",
                    part="json_response",
                    detail=f"Failed to decode Ollama JSON response: {exc}.",
                    hint="Make sure the endpoint returns valid JSON and not an HTML error page.",
                ) from exc
            if not isinstance(parsed, dict):
                raise OllamaContractError(
                    stage="ollama_client",
                    part="json_response",
                    detail="The Ollama response was decoded but it was not a JSON object.",
                    hint="The response contract expects an object containing model, response, and done fields.",
                )
            return parsed

    def _post_stream(self, path: str, payload: dict[str, object]) -> OllamaResponseContract:
        data = json.dumps(payload).encode("utf-8")
        request = Request(
            f"{self.base_url}{path}",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                return OllamaResponseContract.from_stream_chunks(response)
        except JSONDecodeError as exc:
            raise OllamaResponseParseError(
                stage="ollama_client",
                part="stream_response",
                detail=f"Failed to decode Ollama stream chunk: {exc}.",
                hint="Check that stream chunks are newline-delimited JSON objects.",
            ) from exc

    def fallback_generation(self, prompt: PromptBundle, error: Exception | None = None) -> GenerationResult:
        _ = prompt
        reply = "That sounds heavy. I am here with you. Do you want to share what feels most present right now?"
        metadata = {"provider": "fallback", "model": self.model_name, "stream": self.stream, "endpoint": self.generate_path}
        if error is not None:
            metadata["error"] = str(error)
            metadata["error_type"] = type(error).__name__
        return GenerationResult(raw_text=reply, metadata=metadata)


class OllamaStubClient:
    def __init__(self, *args, **kwargs) -> None:
        self.client = LocalLLMClient(*args, **kwargs)

    def generate(self, prompt: PromptBundle) -> GenerationResult:
        return self.client.generate(prompt)
