from __future__ import annotations

from dataclasses import dataclass, field

from pipeline.contracts.models import RequestEnvelope
from pipeline.orchestrator.pipeline import EmotivePipeline


@dataclass
class EvaluationCase:
    name: str
    user_input: str
    expected_keywords: list[str] = field(default_factory=list)


@dataclass
class EvaluationResult:
    name: str
    response_text: str
    passed: bool
    notes: list[str] = field(default_factory=list)


class EvaluationHarness:
    def __init__(self, pipeline: EmotivePipeline | None = None) -> None:
        self.pipeline = pipeline or EmotivePipeline()

    def run_case(self, case: EvaluationCase, user_id: str = "eval-user") -> EvaluationResult:
        request = RequestEnvelope(request_id=f"eval-{case.name}", user_id=user_id, user_input=case.user_input, trace_id=f"trace-{case.name}")
        result = self.pipeline.run(request)
        response_text = result.response.text
        notes: list[str] = []
        passed = True
        for keyword in case.expected_keywords:
            if keyword.lower() not in response_text.lower():
                passed = False
                notes.append(f"Missing keyword: {keyword}")
        return EvaluationResult(name=case.name, response_text=response_text, passed=passed, notes=notes)

    def run_suite(self, cases: list[EvaluationCase]) -> list[EvaluationResult]:
        return [self.run_case(case) for case in cases]
