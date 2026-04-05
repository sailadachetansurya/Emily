from typing import Protocol

from .models import (
    EmotionState,
    GenerationResult,
    MemoryContext,
    PromptBundle,
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


class SafetyProcessor(Protocol):
    def validate(self, generation: GenerationResult, policy: ResponsePolicy) -> SafeResponse:
        ...
