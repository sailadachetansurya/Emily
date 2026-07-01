from typing import Protocol

from .models import (
    EmotionState,
    GenerationResult,
    MemoryContext,
    PromptBundle,
    PrunedResponse,
    RequestEnvelope,
    ResponsePolicy,
    SafeResponse,
)


class InputGateway(Protocol):
    def normalize(self, request: RequestEnvelope) -> RequestEnvelope:
        ...


class EmotionEngine(Protocol):
    def infer(self, request: RequestEnvelope) -> EmotionState:
        ...


class MemoryManager(Protocol):
    def resolve(self, request: RequestEnvelope, emotion: EmotionState) -> MemoryContext:
        ...


class PolicyEngine(Protocol):
    def select(self, request: RequestEnvelope, emotion: EmotionState, memory: MemoryContext) -> ResponsePolicy:
        ...


class PromptBuilder(Protocol):
    def build(self, request: RequestEnvelope, emotion: EmotionState, memory: MemoryContext, policy: ResponsePolicy) -> PromptBundle:
        ...


class LLMClient(Protocol):
    def generate(self, prompt: PromptBundle) -> GenerationResult:
        ...

    def fallback_generation(self, prompt: PromptBundle, error: Exception | None = None) -> GenerationResult:
        ...


class SafetyProcessor(Protocol):
    def validate(self, generation: GenerationResult, policy: ResponsePolicy) -> SafeResponse:
        ...


class OutputPruner(Protocol):
    def prune(self, generation: GenerationResult, policy: ResponsePolicy) -> PrunedResponse:
        ...


class ReasoningLoop(Protocol):
    def should_activate(self, score_breakdown: dict[str, float]) -> bool:
        ...

    def process(
        self, prompt: PromptBundle, policy: ResponsePolicy, score_breakdown: dict[str, float]
    ) -> GenerationResult:
        ...


class TelemetrySink(Protocol):
    def emit(self, trace_name: str, payload: dict[str, object]) -> None:
        ...
