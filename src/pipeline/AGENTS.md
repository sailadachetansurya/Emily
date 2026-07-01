# Pipeline Package

## Purpose

Core emotive AI pipeline: modular stages wired through an orchestrator, producing emotionally attuned responses via deterministic policy control.

## Ownership

All code under `src/pipeline/` belongs to this doc.

## Local Contracts

- Package entry: `pipeline` (installed via `pyproject.toml` with `package-dir = {"" = "src"}`)
- Stage protocol interfaces live in `contracts/interfaces.py` — every stage must satisfy its Protocol
- Shared data models live in `contracts/models.py` — immutable dataclasses, no side effects
- Orchestrator (`orchestrator/pipeline.py`) owns stage wiring; individual stages must not import each other across stage boundaries
- Config loading (`config/runtime.py`) validates against a fixed schema; unknown fields are rejected
- Telemetry (`telemetry/recorder.py`) emits JSONL; stages do not write telemetry directly

## Work Guidance

- Prefer adding new stages as new subdirectories under `stages/` with their own `__init__.py` exporting public API
- New models or interfaces go in `contracts/`; keep `contracts/` free of implementation logic
- Backward-compatible aliases use the pattern `class NewName(OldName): """Backward-compatible alias."""`
- When the pipeline orchestrator adds a new stage, update the trace list and the `__init__` wiring together

## Verification

- `python -m pytest tests/` must pass (uses `PYTHONPATH=src`)

## Child DOX Index

- `stages/emotion_engine/` — Emotion perception, NLP training, dataset preparation
- `stages/reasoning_loop/` — Internal reasoning/self-critique loop with activation gating
- `stages/input_gateway/` — Input normalization (single file, no child doc needed)
- `stages/memory_manager/` — Factual and emotional memory stores (single file each, no child doc needed)
- `stages/policy_engine/` — Deterministic policy selection (single file, no child doc needed)
- `stages/prompt_builder/` — Prompt assembly (single file, no child doc needed)
- `stages/safety_processor/` — Output pruning and speech-act validation (single file, no child doc needed)
- `stages/llm_client/` — Pluggable LLM backends (Ollama, llama.cpp) behind abstract `LLMClient` protocol
- `config/` — Runtime configuration and validation (single file + errors, no child doc needed)
- `contracts/` — Shared models and protocol interfaces (no child doc needed)
- `evaluation/` — Evaluation harness (single file, no child doc needed)
- `orchestrator/` — Pipeline wiring and runner (no child doc needed)
- `telemetry/` — JSONL telemetry sink (single file, no child doc needed)
