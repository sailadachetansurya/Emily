from pipeline.contracts.models import PromptBundle, ResponsePolicy

from .models import CritiqueResult, ReasoningTrace


def build_reasoning_prompt(
    policy_mode: str,
    allowed_acts: list[str],
    disallowed_acts: list[str],
    emotion_summary: str,
    memory_summary: str,
    user_input: str,
) -> str:
    allowed = ", ".join(allowed_acts) or "none"
    disallowed = ", ".join(disallowed_acts) or "none"
    return (
        "You are Emily's internal reasoning module. "
        "Given the emotional context below, decide the best response approach.\n\n"
        f"Policy mode: {policy_mode}\n"
        f"Allowed speech acts: {allowed}\n"
        f"Disallowed speech acts: {disallowed}\n"
        f"Emotion context: {emotion_summary}\n"
        f"Memory context: {memory_summary}\n"
        f"User said: {user_input}\n\n"
        "Output ONLY a JSON object with these keys:\n"
        "- chosen_approach: one of the allowed speech acts that best fits\n"
        "- rationale: one sentence explaining why this approach fits the emotional context\n"
        "- risk_assessment: one sentence naming the biggest thing to avoid in the response\n\n"
        "Do not include any other text."
    )


def build_critique_prompt(
    policy_mode: str,
    allowed_acts: list[str],
    disallowed_acts: list[str],
    response_text: str,
    reasoning_rationale: str,
) -> str:
    allowed = ", ".join(allowed_acts) or "none"
    disallowed = ", ".join(disallowed_acts) or "none"
    return (
        "You are Emily's policy compliance critic. "
        "Evaluate this response against the policy rules.\n\n"
        f"Policy mode: {policy_mode}\n"
        f"Allowed speech acts: {allowed}\n"
        f"Disallowed speech acts: {disallowed}\n"
        f"Expected approach: {reasoning_rationale}\n\n"
        f"Response to evaluate:\n{response_text}\n\n"
        "Output ONLY a JSON object with these keys:\n"
        "- compliant: true or false\n"
        "- violations: list of specific policy violations found (empty if compliant)\n"
        "- suggested_fix: one sentence describing how to fix violations (empty if compliant)\n"
        "- score: float from 0.0 (total violation) to 1.0 (fully compliant)\n\n"
        "Do not include any other text."
    )


def build_enhanced_system_prompt(
    original_system: str,
    trace: ReasoningTrace,
) -> str:
    return (
        f"{original_system}\n\n"
        f"Based on internal analysis: {trace.rationale}. "
        f"Risk to avoid: {trace.risk_assessment}. "
        f"Prioritize {trace.chosen_approach} speech acts in your response."
    )


def build_tightened_prompt(
    original_bundle: PromptBundle,
    critique: CritiqueResult,
    trace: ReasoningTrace,
) -> PromptBundle:
    tightened_constraints = list(original_bundle.do_not_constraints)
    for violation in critique.violations:
        tightened_constraints.append(f"DO NOT: {violation}")
    if critique.suggested_fix:
        tightened_constraints.append(f"Instead: {critique.suggested_fix}")

    adjusted_params = dict(original_bundle.generation_params)
    current_temp = adjusted_params.get("temperature", 0.7)
    adjusted_params["temperature"] = max(0.1, current_temp - 0.1)

    return PromptBundle(
        system_prompt=build_enhanced_system_prompt(original_bundle.system_prompt, trace),
        user_prompt=original_bundle.user_prompt,
        context_blocks=list(original_bundle.context_blocks),
        generation_params=adjusted_params,
        do_not_constraints=tightened_constraints,
    )
