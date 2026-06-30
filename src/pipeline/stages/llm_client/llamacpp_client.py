from __future__ import annotations

import json
from dataclasses import dataclass
from json import JSONDecodeError
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pipeline.contracts.models import GenerationResult, PromptBundle
from pipeline.stages.llm_client.errors import (
    OllamaConfigurationError,
    OllamaContractError,
    OllamaTransportError,
)


@dataclass
class LlamaCppClient:
    model_name: str = "local"
    base_url: str = "http://localhost:8080"
    timeout_seconds: int = 60
    n_tokens: int = 256
    temperature: float = 0.7
    stream: bool = False

    def __post_init__(self) -> None:
        if not self.base_url.strip():
            raise OllamaConfigurationError(
                stage="llamacpp_client",
                part="base_url",
                detail="The llama.cpp base URL is empty.",
                hint="Set 'llamacpp_base_url' in configs/config.json to the llama.cpp server endpoint.",
            )
        if self.timeout_seconds <= 0:
            raise OllamaConfigurationError(
                stage="llamacpp_client",
                part="timeout_seconds",
                detail="The request timeout must be greater than zero.",
                hint="Increase 'request_timeout_seconds' in configs/config.json.",
            )

    def generate(self, prompt: PromptBundle) -> GenerationResult:
        payload = self._build_payload(prompt)
        try:
            response_text = self._post_json(payload)
            return GenerationResult(
                raw_text=response_text,
                metadata={
                    "provider": "llamacpp",
                    "model": self.model_name,
                    "endpoint": f"{self.base_url}/v1/chat/completions",
                    "stream": False,
                },
            )
        except (OllamaContractError, OllamaTransportError):
            raise
        except (HTTPError, URLError, JSONDecodeError, OSError, ValueError) as exc:
            raise OllamaTransportError(
                stage="llamacpp_client",
                part="transport",
                detail=f"Failed to contact llama.cpp at '{self.base_url}/v1/chat/completions': {exc}.",
                hint="Check the llama.cpp server and the URL in configs/config.json.",
            ) from exc

    def _build_payload(self, prompt: PromptBundle) -> dict:
        messages = [{"role": "system", "content": prompt.system_prompt}]
        for block in prompt.context_blocks:
            messages.append({"role": "system", "content": block})
        for constraint in prompt.do_not_constraints:
            messages.append({"role": "system", "content": constraint})
        messages.append({"role": "user", "content": prompt.user_prompt})

        params = dict(prompt.generation_params)
        return {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": params.get("max_tokens", self.n_tokens),
            "temperature": params.get("temperature", self.temperature),
            "stream": False,
        }

    def _post_json(self, payload: dict) -> str:
        data = json.dumps(payload).encode("utf-8")
        request = Request(
            f"{self.base_url}/v1/chat/completions",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=self.timeout_seconds) as response:
            raw = response.read().decode("utf-8")
            parsed = json.loads(raw)
            if not isinstance(parsed, dict):
                raise OllamaContractError(
                    stage="llamacpp_client",
                    part="response",
                    detail="llama.cpp returned a non-object response.",
                    hint="Verify the llama.cpp endpoint is returning JSON.",
                )
            choices = parsed.get("choices", [])
            if not choices:
                raise OllamaContractError(
                    stage="llamacpp_client",
                    part="response",
                    detail="llama.cpp returned no choices.",
                    hint="Check the request payload and model availability.",
                )
            message = choices[0].get("message", {})
            return str(message.get("content", ""))
