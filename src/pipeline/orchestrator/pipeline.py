from pipeline.contracts.models import RequestEnvelope, SafeResponse
from pipeline.stages.emotion_engine import HeuristicEmotionEngine
from pipeline.stages.input_gateway import DefaultInputGateway
from pipeline.stages.llm_client import OllamaStubClient
from pipeline.stages.memory_manager import InMemoryMemoryManager
from pipeline.stages.policy_engine import RuleBasedPolicyEngine
from pipeline.stages.prompt_builder import DefaultPromptBuilder
from pipeline.stages.safety_processor import DefaultSafetyProcessor


class EmotivePipeline:
    def __init__(self) -> None:
        self.input_gateway = DefaultInputGateway()
        self.emotion_engine = HeuristicEmotionEngine()
        self.memory_manager = InMemoryMemoryManager()
        self.policy_engine = RuleBasedPolicyEngine()
        self.prompt_builder = DefaultPromptBuilder()
        self.llm_client = OllamaStubClient()
        self.safety_processor = DefaultSafetyProcessor()

    def run(self, request: RequestEnvelope) -> SafeResponse:
        normalized = self.input_gateway.normalize(request)
        emotion = self.emotion_engine.infer(normalized)
        memory = self.memory_manager.resolve(normalized, emotion)
        policy = self.policy_engine.select(normalized, emotion, memory)
        prompt = self.prompt_builder.build(normalized, emotion, memory, policy)
        generated = self.llm_client.generate(prompt)
        safe = self.safety_processor.validate(generated, policy)
        return safe
