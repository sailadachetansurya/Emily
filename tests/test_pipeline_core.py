import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pipeline.contracts.models import EmotionState, MemoryContext, RequestEnvelope
from pipeline.config.errors import ConfigValidationError
from pipeline.config.runtime import ConfigLoader
from pipeline.orchestrator.pipeline import EmotivePipeline
from pipeline.stages.emotion_engine import HeuristicEmotionEngine, SampleNLPEmotionModel
from pipeline.stages.llm_client import OLLAMA_PROMPT_REQUEST_SCHEMA, OLLAMA_RESPONSE_SCHEMA, LocalLLMClient
from pipeline.stages.llm_client.contracts import OllamaPromptRequest, OllamaResponseContract
from pipeline.stages.llm_client.errors import OllamaContractError, OllamaResponseParseError
from pipeline.stages.memory_manager import DualMemoryManager
from pipeline.stages.policy_engine import DeterministicPolicyEngine
from pipeline.stages.prompt_builder import PromptAssembler
from pipeline.stages.safety_processor import ProjectionSafetyProcessor


class PipelineCoreTests(unittest.TestCase):
    def test_prompt_assembler_uses_emily_system_prompt(self) -> None:
        assembler = PromptAssembler()
        request = RequestEnvelope(request_id="req-1", user_id="user-1", user_input="I feel unsure.", trace_id="trace-1")
        emotion = EmotionState(emotional_valence=-0.2, activation_level="medium", social_orientation="neutral", stability="stable")
        memory = MemoryContext(factual_facts={"name": "Emily"}, emotional_summary="User is uncertain.")
        policy = DeterministicPolicyEngine().select(request, emotion, memory)

        prompt = assembler.build(request, emotion, memory, policy)

        self.assertIn("Emily the emotive AI", prompt.system_prompt)
        self.assertIn("DO NOT use diagnostic language.", prompt.do_not_constraints)
        self.assertEqual(prompt.generation_params["mode"], policy.mode)

    def test_policy_engine_is_deterministic(self) -> None:
        engine = DeterministicPolicyEngine()
        request = RequestEnvelope(request_id="req-2", user_id="user-2", user_input="I am scared and overwhelmed.", trace_id="trace-2")
        emotion = EmotionState(emotional_valence=-0.6, activation_level="high", social_orientation="reaching", stability="fragile")
        memory = MemoryContext(factual_facts={}, emotional_summary="fragile context")

        decision = engine.decide(request, emotion, memory)

        self.assertEqual(decision.policy.mode, "reflection")
        self.assertGreaterEqual(decision.policy.confidence, 0.55)
        self.assertIn("emotional_risk", decision.score_breakdown)

    def test_emotion_engine_heuristics_are_stable(self) -> None:
        engine = HeuristicEmotionEngine()
        request = RequestEnvelope(request_id="req-3", user_id="user-3", user_input="I feel lonely and anxious!!", trace_id="trace-3")

        emotion = engine.infer(request)

        self.assertEqual(emotion.stability, "fragile")
        self.assertEqual(emotion.activation_level, "high")
        self.assertLess(emotion.emotional_valence, 0.0)
        self.assertIn("anxiety", emotion.signals)

    def test_dual_memory_manager_returns_structured_context(self) -> None:
        manager = DualMemoryManager()
        manager.remember_fact("user-4", "name", "Emily")
        manager.remember_emotional_summary("user-4", "User often feels overwhelmed.", themes=["overwhelm"], triggers=["work"], recency_weight=0.9)
        request = RequestEnvelope(request_id="req-4", user_id="user-4", user_input="I feel overwhelmed at work.", trace_id="trace-4")
        emotion = EmotionState(emotional_valence=-0.4, activation_level="high", social_orientation="reaching", stability="fragile", signals={"work": 1.0})

        memory = manager.resolve(request, emotion)

        self.assertEqual(memory.factual_facts["name"], "Emily")
        self.assertTrue(memory.emotional_records)
        self.assertIn("overwhelmed", memory.emotional_summary)

    def test_ollama_contract_round_trip(self) -> None:
        prompt_request = OllamaPromptRequest(
            model="mistral",
            system_prompt="You are Emily the emotive AI.",
            user_prompt="How are you?",
            context_blocks=["Emotion: neutral"],
            do_not_constraints=["DO NOT use diagnostic language."],
            options={"temperature": 0.7, "max_tokens": 80},
        )
        payload = prompt_request.to_payload()
        response = OllamaResponseContract.from_payload({"model": "mistral", "response": "I am here with you.", "done": True})

        self.assertEqual(payload["model"], "mistral")
        self.assertIn("SYSTEM:", payload["prompt"])
        self.assertEqual(response.to_generation_text(), "I am here with you.")

    def test_ollama_contract_schemas_are_strict(self) -> None:
        self.assertIn("required", OLLAMA_PROMPT_REQUEST_SCHEMA)
        self.assertIn("required", OLLAMA_RESPONSE_SCHEMA)
        self.assertIn("stream", OLLAMA_PROMPT_REQUEST_SCHEMA["properties"])
        self.assertIn("done", OLLAMA_RESPONSE_SCHEMA["properties"])

    def test_stream_response_contract_joins_chunks(self) -> None:
        response = OllamaResponseContract.from_stream_chunks([
            '{"model":"mistral","response":"Hello","done":false}',
            '{"model":"mistral","response":" there","done":true,"eval_count":4}',
        ])

        self.assertEqual(response.to_generation_text(), "Hello there")
        self.assertTrue(response.done)

    def test_stream_response_contract_raises_on_missing_done(self) -> None:
        with self.assertRaises(OllamaResponseParseError) as context:
            OllamaResponseContract.from_stream_chunks(['{"model":"mistral","response":"Hello","done":false}'])

        self.assertIn("stream_chunks", str(context.exception))

    def test_contract_error_message_includes_stage_and_part(self) -> None:
        error = OllamaContractError(stage="ollama_contract", part="request_payload", detail="Missing field.", hint="Fix the config.")
        self.assertIn("ollama_contract", str(error))
        self.assertIn("request_payload", str(error))
        self.assertIn("Fix the config.", str(error))

    def test_config_loader_reads_config_json(self) -> None:
        config = ConfigLoader().load()
        self.assertEqual(config.ollama_generate_path, "/api/generate")
        self.assertFalse(config.ollama_stream)

    def test_config_loader_rejects_unexpected_fields(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "config.json"
            config_path.write_text(
                '{"model_name":"mistral","ollama_base_url":"http://localhost:11434","request_timeout_seconds":30,"ollama_stream":false,"ollama_generate_path":"/api/generate","telemetry_path":"logs/pipeline-telemetry.jsonl","max_factual_items":32,"max_emotional_items":64,"unexpected":true}',
                encoding="utf-8",
            )
            loader = ConfigLoader(str(config_path))

            with self.assertRaises(ConfigValidationError) as context:
                loader.load()

            self.assertIn("unexpected", str(context.exception))

    def test_config_loader_rejects_missing_fields(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "config.json"
            config_path.write_text('{"model_name":"mistral"}', encoding="utf-8")
            loader = ConfigLoader(str(config_path))

            with self.assertRaises(ConfigValidationError) as context:
                loader.load()

            self.assertIn("ollama_base_url", str(context.exception))

    def test_sample_nlp_emotion_model_detects_emotion(self) -> None:
        model = SampleNLPEmotionModel()

        emotion = model.classify("I am very anxious and worried!!")

        self.assertEqual(emotion.stability, "fragile")
        self.assertEqual(emotion.activation_level, "high")
        self.assertLess(emotion.emotional_valence, 0.0)
        self.assertGreater(emotion.signals["exclamation_count"], 0.0)

    def test_pipeline_can_use_nlp_sample_emotion_model(self) -> None:
        loader = ConfigLoader()
        config = loader.load()
        self.assertIn(config.emotion_model_kind, ["heuristic", "nlp_sample"])

        pipeline = EmotivePipeline()
        pipeline.config = type(pipeline.config)(
            model_name=pipeline.config.model_name,
            ollama_base_url=pipeline.config.ollama_base_url,
            request_timeout_seconds=pipeline.config.request_timeout_seconds,
            ollama_stream=pipeline.config.ollama_stream,
            ollama_generate_path=pipeline.config.ollama_generate_path,
            emotion_model_kind="nlp_sample",
            telemetry_path=pipeline.config.telemetry_path,
            max_factual_items=pipeline.config.max_factual_items,
            max_emotional_items=pipeline.config.max_emotional_items,
        )
        pipeline.emotion_engine = pipeline.build_emotion_engine()

        request = RequestEnvelope(request_id="req-nlp", user_id="user-nlp", user_input="I am really scared and worried about this!!!", trace_id="trace-nlp")
        emotion = pipeline.emotion_engine.infer(request)

        self.assertEqual(emotion.stability, "fragile")
        self.assertEqual(emotion.activation_level, "high")

    def test_local_llm_client_uses_configured_endpoint_and_stream_flag(self) -> None:
        client = LocalLLMClient(model_name="mistral", base_url="http://localhost:11434", generate_path="/api/chat", stream=True)
        request = RequestEnvelope(request_id="req-x", user_id="user-x", user_input="Hi", trace_id="trace-x")
        emotion = EmotionState()
        memory = MemoryContext()
        policy = DeterministicPolicyEngine().select(request, emotion, memory)
        prompt = PromptAssembler().build(request, emotion, memory, policy)

        payload = client.build_request_contract(prompt).to_payload()

        self.assertEqual(payload["stream"], True)
        self.assertEqual(client.generate_path, "/api/chat")

    def test_output_pruning_projects_to_fit_space(self) -> None:
        pruner = ProjectionSafetyProcessor()
        generation = type("Generation", (), {"raw_text": "You should try this and I can diagnose it.", "metadata": {}})()
        policy = type("Policy", (), {"allowed_speech_acts": ["reflect", "validate"], "disallowed_speech_acts": ["diagnose"], "mode": "reflection"})()

        result = pruner.validate(generation, policy)

        self.assertNotIn("you should", result.text.lower())
        self.assertNotIn("diagnose", result.text.lower())
        self.assertLessEqual(len(result.text.split(".")), 4)

    def test_pipeline_smoke_returns_traces(self) -> None:
        pipeline = EmotivePipeline()
        request = RequestEnvelope(request_id="req-5", user_id="user-5", user_input="I have been feeling lonely and anxious lately.", trace_id="trace-5")

        result = pipeline.run(request)

        self.assertTrue(result.response.text)
        self.assertGreaterEqual(len(result.traces), 7)
        self.assertEqual(result.traces[-1].stage_name, "output_pruning")


if __name__ == "__main__":
    unittest.main()
