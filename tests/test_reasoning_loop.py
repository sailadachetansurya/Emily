import json
import unittest
from unittest.mock import MagicMock, patch

from pipeline.contracts.models import GenerationResult, PromptBundle, ResponsePolicy
from pipeline.stages.llm_client import LocalLLMClient
from pipeline.stages.reasoning_loop.critic import PolicyCritiqueEvaluator
from pipeline.stages.reasoning_loop.models import CritiqueResult, ReasoningTrace
from pipeline.stages.reasoning_loop.orchestrator import ReasoningLoopConfig, ReasoningLoopOrchestrator
from pipeline.stages.reasoning_loop.prompts import (
    build_critique_prompt,
    build_enhanced_system_prompt,
    build_reasoning_prompt,
    build_tightened_prompt,
)


def make_policy(**overrides) -> ResponsePolicy:
    defaults = dict(
        mode="reflection",
        max_tokens=80,
        temperature=0.7,
        allowed_speech_acts=["reflect", "validate"],
        disallowed_speech_acts=["diagnose", "advise"],
        explanation="Test policy",
        confidence=0.8,
    )
    defaults.update(overrides)
    return ResponsePolicy(**defaults)


def make_prompt(**overrides) -> PromptBundle:
    defaults = dict(
        system_prompt="You are Emily the emotive AI.",
        user_prompt="I feel anxious.",
        context_blocks=["Emotion: valence=-0.5", "Memory: none"],
        generation_params={"max_tokens": 80, "temperature": 0.7},
        do_not_constraints=["DO NOT use diagnostic language."],
    )
    defaults.update(overrides)
    return PromptBundle(**defaults)


def make_generation(text: str = "It sounds like you are carrying a lot.") -> GenerationResult:
    return GenerationResult(raw_text=text, metadata={})


class TestShouldActivate(unittest.TestCase):
    def test_activate_above_threshold(self) -> None:
        config = ReasoningLoopConfig(enabled=True, activation_threshold=0.5)
        llm = MagicMock(spec=LocalLLMClient)
        orchestrator = ReasoningLoopOrchestrator(llm, config)
        self.assertTrue(orchestrator.should_activate({"emotional_risk": 0.7}))

    def test_activate_at_threshold(self) -> None:
        config = ReasoningLoopConfig(enabled=True, activation_threshold=0.5)
        llm = MagicMock(spec=LocalLLMClient)
        orchestrator = ReasoningLoopOrchestrator(llm, config)
        self.assertTrue(orchestrator.should_activate({"emotional_risk": 0.5}))

    def test_below_threshold(self) -> None:
        config = ReasoningLoopConfig(enabled=True, activation_threshold=0.5)
        llm = MagicMock(spec=LocalLLMClient)
        orchestrator = ReasoningLoopOrchestrator(llm, config)
        self.assertFalse(orchestrator.should_activate({"emotional_risk": 0.3}))

    def test_disabled(self) -> None:
        config = ReasoningLoopConfig(enabled=False, activation_threshold=0.0)
        llm = MagicMock(spec=LocalLLMClient)
        orchestrator = ReasoningLoopOrchestrator(llm, config)
        self.assertFalse(orchestrator.should_activate({"emotional_risk": 1.0}))

    def test_missing_key(self) -> None:
        config = ReasoningLoopConfig(enabled=True, activation_threshold=0.5)
        llm = MagicMock(spec=LocalLLMClient)
        orchestrator = ReasoningLoopOrchestrator(llm, config)
        self.assertFalse(orchestrator.should_activate({}))


class TestParseReasoning(unittest.TestCase):
    def test_valid_json(self) -> None:
        llm = MagicMock(spec=LocalLLMClient)
        config = ReasoningLoopConfig()
        orchestrator = ReasoningLoopOrchestrator(llm, config)
        raw = json.dumps({
            "chosen_approach": "reflect",
            "rationale": "User shows fragile stability.",
            "risk_assessment": "Avoid advisory tone.",
        })
        trace = orchestrator._parse_reasoning(raw)
        self.assertEqual(trace.chosen_approach, "reflect")
        self.assertEqual(trace.rationale, "User shows fragile stability.")
        self.assertEqual(trace.risk_assessment, "Avoid advisory tone.")

    def test_invalid_json_returns_default(self) -> None:
        llm = MagicMock(spec=LocalLLMClient)
        config = ReasoningLoopConfig()
        orchestrator = ReasoningLoopOrchestrator(llm, config)
        trace = orchestrator._parse_reasoning("not valid json {{{")
        self.assertEqual(trace.chosen_approach, "reflect")
        self.assertIn("parse failure", trace.rationale)

    def test_strips_markdown_fences(self) -> None:
        llm = MagicMock(spec=LocalLLMClient)
        config = ReasoningLoopConfig()
        orchestrator = ReasoningLoopOrchestrator(llm, config)
        raw = '```json\n{"chosen_approach": "validate", "rationale": "test", "risk_assessment": "none"}\n```'
        trace = orchestrator._parse_reasoning(raw)
        self.assertEqual(trace.chosen_approach, "validate")


class TestCritiqueEvaluator(unittest.TestCase):
    def test_parse_valid_critique(self) -> None:
        llm = MagicMock(spec=LocalLLMClient)
        evaluator = PolicyCritiqueEvaluator(llm)
        raw = json.dumps({
            "compliant": False,
            "violations": ["uses advisory language"],
            "suggested_fix": "Remove 'you should'.",
            "score": 0.4,
        })
        result = evaluator._parse_critique(raw)
        self.assertFalse(result.compliant)
        self.assertEqual(result.violations, ["uses advisory language"])
        self.assertAlmostEqual(result.score, 0.4)

    def test_parse_invalid_returns_compliant(self) -> None:
        llm = MagicMock(spec=LocalLLMClient)
        evaluator = PolicyCritiqueEvaluator(llm)
        result = evaluator._parse_critique("garbage output")
        self.assertTrue(result.compliant)
        self.assertEqual(result.score, 1.0)

    def test_strips_markdown_fences(self) -> None:
        llm = MagicMock(spec=LocalLLMClient)
        evaluator = PolicyCritiqueEvaluator(llm)
        raw = '```json\n{"compliant": true, "violations": [], "suggested_fix": "", "score": 1.0}\n```'
        result = evaluator._parse_critique(raw)
        self.assertTrue(result.compliant)


class TestPrompts(unittest.TestCase):
    def test_reasoning_prompt_contains_policy(self) -> None:
        prompt = build_reasoning_prompt(
            policy_mode="reflection",
            allowed_acts=["reflect", "validate"],
            disallowed_acts=["diagnose"],
            emotion_summary="valence=-0.5",
            memory_summary="none",
            user_input="I feel anxious.",
        )
        self.assertIn("reflection", prompt)
        self.assertIn("reflect", prompt)
        self.assertIn("diagnose", prompt)
        self.assertIn("I feel anxious.", prompt)

    def test_critique_prompt_contains_response(self) -> None:
        prompt = build_critique_prompt(
            policy_mode="reflection",
            allowed_acts=["reflect"],
            disallowed_acts=["advise"],
            response_text="You should try this.",
            reasoning_rationale="User needs validation.",
        )
        self.assertIn("You should try this.", prompt)
        self.assertIn("User needs validation.", prompt)

    def test_enhanced_prompt_injects_trace(self) -> None:
        trace = ReasoningTrace(
            reasoning_text="",
            chosen_approach="reflect",
            rationale="User is fragile.",
            risk_assessment="Avoid advice.",
        )
        enhanced = build_enhanced_system_prompt("You are Emily.", trace)
        self.assertIn("User is fragile.", enhanced)
        self.assertIn("Avoid advice.", enhanced)
        self.assertIn("reflect", enhanced)

    def test_tightened_prompt_adds_constraints(self) -> None:
        bundle = make_prompt()
        critique = CritiqueResult(
            compliant=False,
            violations=["contains advisory language"],
            suggested_fix="Use reflection instead.",
        )
        trace = ReasoningTrace(
            reasoning_text="",
            chosen_approach="reflect",
            rationale="test",
            risk_assessment="test",
        )
        tightened = build_tightened_prompt(bundle, critique, trace)
        self.assertTrue(any("advisory language" in c for c in tightened.do_not_constraints))
        self.assertTrue(any("reflection instead" in c for c in tightened.do_not_constraints))
        self.assertLess(tightened.generation_params["temperature"], bundle.generation_params["temperature"])


class TestReasoningLoopProcess(unittest.TestCase):
    def test_passes_first_try(self) -> None:
        llm = MagicMock(spec=LocalLLMClient)
        reasoning_response = json.dumps({
            "chosen_approach": "reflect",
            "rationale": "User is fragile.",
            "risk_assessment": "Avoid advice.",
        })
        compliant_response = "It sounds like you are carrying a lot."
        critique_response = json.dumps({
            "compliant": True,
            "violations": [],
            "suggested_fix": "",
            "score": 1.0,
        })
        llm.generate.side_effect = [
            GenerationResult(raw_text=reasoning_response, metadata={}),
            GenerationResult(raw_text=compliant_response, metadata={}),
            GenerationResult(raw_text=critique_response, metadata={}),
        ]
        config = ReasoningLoopConfig(enabled=True, max_iterations=2, activation_threshold=0.0)
        orchestrator = ReasoningLoopOrchestrator(llm, config)
        policy = make_policy()
        prompt = make_prompt()

        result = orchestrator.process(prompt, policy, {"emotional_risk": 0.8})

        self.assertEqual(result.raw_text, compliant_response)
        self.assertTrue(result.metadata["reasoning_loop"]["activated"])
        self.assertEqual(result.metadata["reasoning_loop"]["iterations"], 1)

    def test_triggers_regeneration(self) -> None:
        llm = MagicMock(spec=LocalLLMClient)
        reasoning_response = json.dumps({
            "chosen_approach": "reflect",
            "rationale": "User is fragile.",
            "risk_assessment": "Avoid advice.",
        })
        bad_response = "You should try meditation."
        critique_response = json.dumps({
            "compliant": False,
            "violations": ["advisory language"],
            "suggested_fix": "Use reflection.",
            "score": 0.3,
        })
        good_response = "It sounds like this feels heavy."
        compliant_critique = json.dumps({
            "compliant": True,
            "violations": [],
            "suggested_fix": "",
            "score": 1.0,
        })
        llm.generate.side_effect = [
            GenerationResult(raw_text=reasoning_response, metadata={}),
            GenerationResult(raw_text=bad_response, metadata={}),
            GenerationResult(raw_text=critique_response, metadata={}),
            GenerationResult(raw_text=good_response, metadata={}),
            GenerationResult(raw_text=compliant_critique, metadata={}),
        ]
        config = ReasoningLoopConfig(enabled=True, max_iterations=2, activation_threshold=0.0)
        orchestrator = ReasoningLoopOrchestrator(llm, config)
        policy = make_policy()
        prompt = make_prompt()

        result = orchestrator.process(prompt, policy, {"emotional_risk": 0.8})

        self.assertEqual(result.raw_text, good_response)
        self.assertEqual(result.metadata["reasoning_loop"]["iterations"], 2)
        self.assertEqual(result.metadata["reasoning_loop"]["final_variant"], "tightened")

    def test_max_iterations_respected(self) -> None:
        llm = MagicMock(spec=LocalLLMClient)
        reasoning_response = json.dumps({
            "chosen_approach": "reflect",
            "rationale": "test",
            "risk_assessment": "test",
        })
        bad_response = "Bad response."
        noncompliant_critique = json.dumps({
            "compliant": False,
            "violations": ["violation"],
            "suggested_fix": "fix it",
            "score": 0.2,
        })
        llm.generate.side_effect = [
            GenerationResult(raw_text=reasoning_response, metadata={}),
            GenerationResult(raw_text=bad_response, metadata={}),
            GenerationResult(raw_text=noncompliant_critique, metadata={}),
            GenerationResult(raw_text="Worse response.", metadata={}),
            GenerationResult(raw_text=noncompliant_critique, metadata={}),
        ]
        config = ReasoningLoopConfig(enabled=True, max_iterations=2, activation_threshold=0.0)
        orchestrator = ReasoningLoopOrchestrator(llm, config)
        policy = make_policy()
        prompt = make_prompt()

        result = orchestrator.process(prompt, policy, {"emotional_risk": 0.8})

        self.assertEqual(result.raw_text, "Worse response.")
        self.assertEqual(result.metadata["reasoning_loop"]["iterations"], 2)

    def test_single_iteration_no_critique(self) -> None:
        llm = MagicMock(spec=LocalLLMClient)
        reasoning_response = json.dumps({
            "chosen_approach": "reflect",
            "rationale": "test",
            "risk_assessment": "test",
        })
        response = "It sounds like you are hurting."
        llm.generate.side_effect = [
            GenerationResult(raw_text=reasoning_response, metadata={}),
            GenerationResult(raw_text=response, metadata={}),
        ]
        config = ReasoningLoopConfig(enabled=True, max_iterations=1, activation_threshold=0.0)
        orchestrator = ReasoningLoopOrchestrator(llm, config)
        policy = make_policy()
        prompt = make_prompt()

        result = orchestrator.process(prompt, policy, {"emotional_risk": 0.8})

        self.assertEqual(result.raw_text, response)
        self.assertEqual(llm.generate.call_count, 2)


if __name__ == "__main__":
    unittest.main()
