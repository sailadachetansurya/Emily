from dataclasses import asdict

from pipeline.config.runtime import ConfigLoader
from pipeline.contracts.models import PipelineResult, RequestEnvelope, SafeResponse, StageTrace
from pipeline.stages.emotion_engine import HeuristicEmotionClassifier, SampleNLPEmotionModel
from pipeline.stages.input_gateway import DefaultInputGateway
from pipeline.stages.llm_client import LocalLLMClient
from pipeline.stages.memory_manager import DualMemoryManager
from pipeline.stages.policy_engine import DeterministicPolicyEngine
from pipeline.stages.prompt_builder import DefaultPromptBuilder
from pipeline.stages.reasoning_loop import ReasoningLoopConfig, ReasoningLoopOrchestrator
from pipeline.stages.safety_processor import ProjectionSafetyProcessor
from pipeline.telemetry.recorder import JsonTelemetrySink


class EmotivePipeline:
    def __init__(self) -> None:
        self.config = ConfigLoader().load()
        self.input_gateway = DefaultInputGateway()
        self.emotion_engine = self.build_emotion_engine()
        self.memory_manager = DualMemoryManager()
        self.policy_engine = DeterministicPolicyEngine()
        self.prompt_builder = DefaultPromptBuilder()
        self.llm_client = LocalLLMClient(
            model_name=self.config.model_name,
            base_url=self.config.ollama_base_url,
            timeout_seconds=self.config.request_timeout_seconds,
            generate_path=self.config.ollama_generate_path,
            stream=self.config.ollama_stream,
        )
        self.safety_processor = ProjectionSafetyProcessor()
        self.telemetry = JsonTelemetrySink(output_path=self.config.telemetry_path)
        self.reasoning_loop = ReasoningLoopOrchestrator(
            llm_client=self.llm_client,
            config=ReasoningLoopConfig(
                enabled=self.config.reasoning_loop_enabled,
                max_iterations=self.config.reasoning_loop_max_iterations,
                activation_threshold=self.config.reasoning_loop_activation_threshold,
            ),
        )

    def build_emotion_engine(self):
        if self.config.emotion_model_kind == "nlp_sample":
            return SampleNLPEmotionModel()
        return HeuristicEmotionClassifier()

    def run(self, request: RequestEnvelope) -> PipelineResult:
        traces: list[StageTrace] = []
        normalized = self.input_gateway.normalize(request)
        traces.append(StageTrace(stage_name="input_gateway", status="ok", metadata={"request": asdict(normalized)}))
        emotion = self.emotion_engine.infer(normalized)
        traces.append(StageTrace(stage_name="emotion_perception", status="ok", metadata={"emotion": asdict(emotion)}))
        memory = self.memory_manager.resolve(normalized, emotion)
        traces.append(StageTrace(stage_name="dual_memory", status="ok", metadata={"memory": asdict(memory)}))
        decision = self.policy_engine.decide(normalized, emotion, memory)
        policy = decision.policy
        traces.append(StageTrace(stage_name="policy_mapper", status="ok", metadata={"policy": asdict(policy), "scores": decision.score_breakdown}))
        prompt = self.prompt_builder.build(normalized, emotion, memory, policy)
        traces.append(StageTrace(stage_name="prompt_constructor", status="ok", metadata={"prompt": asdict(prompt)}))
        if self.reasoning_loop.should_activate(decision.score_breakdown):
            generated = self.reasoning_loop.process(prompt, policy, decision.score_breakdown)
            traces.append(StageTrace(
                stage_name="reasoning_loop",
                status="ok",
                metadata=generated.metadata.get("reasoning_loop", {}),
            ))
        else:
            generated = self.llm_client.generate(prompt)
        traces.append(StageTrace(stage_name="llm_generation", status="ok", metadata={"generation": asdict(generated)}))
        safe = self.safety_processor.validate(generated, policy)
        traces.append(StageTrace(stage_name="output_pruning", status="ok", metadata={"response": asdict(safe)}))
        for trace in traces:
            self.telemetry.emit(trace.stage_name, trace.metadata | {"status": trace.status})
        return PipelineResult(request_id=request.request_id, response=safe, traces=traces)
