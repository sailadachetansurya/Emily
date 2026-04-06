# Emotive Pipeline Baseline

This workspace contains a modular emotive AI pipeline with deterministic policy control and output pruning into a constrained fit space.

## Architecture
User Input -> Emotion Perception Layer -> Dual Memory System -> Deterministic Policy Mapper -> Prompt Constructor -> LLM Generation -> Output Pruning / Fit Space Projection -> Final Response

## Structure
- DOCs/: design notes and implementation guides
- configs/: runtime JSON configuration files
- src/pipeline/contracts/: shared models and protocol interfaces
- src/pipeline/stages/emotion_engine/: rule-based emotion perception
- src/pipeline/stages/memory_manager/: factual and emotional memory stores
- src/pipeline/stages/policy_engine/: deterministic policy selection
- src/pipeline/stages/prompt_builder/: prompt assembly utilities
- src/pipeline/stages/llm_client/: local Ollama-compatible client
- src/pipeline/stages/safety_processor/: output pruning and speech-act validation
- src/pipeline/orchestrator/: pipeline wiring and execution trace
- src/pipeline/telemetry/: JSONL telemetry sink
- src/pipeline/evaluation/: simple evaluation harness

## Run
1. Ensure the virtual environment is active.
2. Run:

```bash
$env:PYTHONPATH='src'; python -m pipeline.orchestrator.runner
```

## Implementation Notes
- The policy layer is deterministic and explainable.
- The LLM client is local-first and falls back to a stubbed response if Ollama is unavailable.
- The output pruner enforces speech-act constraints and sentence limits before returning the final response.
- Telemetry is written to `logs/pipeline-telemetry.jsonl`.
