# Reasoning Loop Stage

## Purpose

Optional internal reasoning/self-critique loop that has the LLM reason about its response approach before generating, then optionally critiques the output — reducing the safety processor's post-hoc intervention rate.

## Ownership

All files in `src/pipeline/stages/reasoning_loop/` belong to this doc.

## Local Contracts

- **Activation**: gated by `emotional_risk >= config.activation_threshold` and `config.enabled`
- **Reasoning step**: LLM produces JSON with `chosen_approach`, `rationale`, `risk_assessment`
- **Enhanced generation**: reasoning trace injected into system prompt
- **Critique step**: LLM evaluates response against policy rules, returns JSON with `compliant`, `violations`, `suggested_fix`, `score`
- **Regeneration**: if critique finds violations, tighten prompt and regenerate (max N iterations)
- **Fail-open**: parse failures in reasoning or critique produce safe defaults, never block production
- Stage-internal models (`ReasoningTrace`, `CritiqueResult`, `IterationRecord`) are not exported to `contracts/models.py`

## Work Guidance

- All LLM calls in this stage use the existing `LocalLLMClient` — no new providers
- The `process()` method returns `GenerationResult` with iteration data in `metadata["reasoning_loop"]`
- The `should_activate()` method accepts `score_breakdown: dict` (not `PolicyDecision`) to avoid cross-stage imports
- Config fields: `reasoning_loop_enabled`, `reasoning_loop_max_iterations`, `reasoning_loop_activation_threshold`

## Verification

- `python -m pytest tests/test_reasoning_loop.py` covers activation, parsing, critique, and full loop
