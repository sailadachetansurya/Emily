# Emily — Emotive AI Pipeline

A modular emotive AI pipeline with deterministic policy control, internal reasoning loops, and fit-space output projection. Designed for emotionally safe, contextually attuned responses via local LLM inference.

## Architecture

```
User Input
  → Input Gateway (normalization)
  → Emotion Engine (heuristic + NLP perception)
  → Dual Memory (factual + emotional stores)
  → Policy Engine (deterministic mode selection)
  → Prompt Builder (structured prompt assembly)
  → Reasoning Loop (optional self-critique, gated by emotional risk)
  → LLM Client (local Ollama)
  → Safety Processor (speech-act pruning + fit-space projection)
  → Final Response
```

## Quick Start

### Pipeline (CLI)

```bash
$env:PYTHONPATH='src'
python -m pipeline.orchestrator.runner
```

### Web Control Panel

```bash
$env:PYTHONPATH='src'
python server.py
```

Open `http://localhost:8000` for the interactive control panel with:
- **Overview** — pipeline status, quick run, recent jobs
- **Pipeline** — run input, configure reasoning loop
- **Training** — dataset preparation, model training
- **Settings** — runtime config, theme selection (5 themes)
- **Logs** — telemetry viewer

### Dataset Preparation

```bash
python run_prepare_emotion_dataset.py
```

Fetches `dair-ai/emotion` and `Alignment-Lab-AI/EmotionDialogue` from Hugging Face, normalizes into training JSONL.

### Model Training

```bash
python run_train_nlp_emotion_model.py
```

Trains the NLP emotion classifier from `dataset/emotion_train.jsonl` → `models/emotion_model.json`.

## Structure

```
configs/                          Runtime configuration
  config.json                     Main config (model, endpoints, feature flags)
  config.schema.json              JSON Schema reference
  policy_config.json              Per-mode policy overrides
  safety_config.json              Forbidden phrases, max sentences

dataset/                          Training data
  emotion_train.jsonl             Training split
  emotion_validation.jsonl        Validation split
  emotion_test.jsonl              Test split
  processed/                      Per-source normalized intermediates

src/pipeline/                     Core pipeline package
  contracts/                      Shared models and protocol interfaces
  config/                         Runtime config loader and validation
  orchestrator/                   Pipeline wiring and runner
  stages/
    emotion_engine/               Heuristic + NLP emotion perception, training, dataset prep
    input_gateway/                Input normalization
    memory_manager/               Factual and emotional memory stores
    policy_engine/                Deterministic policy selection
    prompt_builder/               Prompt assembly
    llm_client/                   Local Ollama-compatible client
    safety_processor/             Output pruning and speech-act validation
    reasoning_loop/               Internal self-critique loop (optional)
  telemetry/                      JSONL telemetry sink
  evaluation/                     Evaluation harness

templates/                        Web panel page templates
static/                           CSS, JS assets
server.py                         FastAPI web server
index.html                        Legacy single-page control panel
```

## Configuration

Key fields in `configs/config.json`:

| Field | Default | Description |
|---|---|---|
| `model_name` | `mistral` | Ollama model name |
| `ollama_base_url` | `http://localhost:11434` | Ollama endpoint |
| `emotion_model_kind` | `heuristic` | `heuristic` or `nlp_sample` |
| `reasoning_loop_enabled` | `false` | Enable self-critique loop |
| `reasoning_loop_max_iterations` | `2` | Max critique-regen cycles |
| `reasoning_loop_activation_threshold` | `0.5` | Emotional risk to trigger loop |

## Themes

The web control panel supports 5 visual themes:
- **Modern Minimalist** — grayscale, clean, default
- **Sunset Boulevard** — warm burnt orange and coral
- **Ocean Depths** — deep navy and teal
- **Midnight Galaxy** — cosmic purple and lavender
- **Arctic Frost** — ice blue and steel

## Testing

```bash
$env:PYTHONPATH='src'
python -m unittest discover tests -v
```

40 tests covering pipeline core, reasoning loop, NLP training, and dataset preparation.

## Features

### Error Reporting
Structured error display with error type, pipeline stage, component, detail, and hint. Errors from `ConfigValidationError`, `OllamaError`, and other pipeline exceptions are captured with full context and rendered in the UI with styled badges.

### State Persistence
Job state persists across page navigation via localStorage + server sync. Running jobs are re-polled automatically when you return to a page. The `GET /api/jobs` endpoint returns all server-side jobs for reconciliation.

### Summary Logging
Every pipeline run appends a structured entry to `Summary.md` with timestamp, input, response, safety notes, and stage trace table. The file is append-only and accumulates history across runs.

## Design Notes

- The policy layer is deterministic and explainable — every response mode comes with a score breakdown and rationale
- The reasoning loop internalizes policy constraints through self-reflection, reducing post-hoc safety interventions
- The safety processor remains as a final safety net with fit-space projection
- The LLM client falls back to a safe default when Ollama is unavailable
- All stages communicate through typed dataclasses; no shared mutable state
- See `workingindex.md` for a detailed point-by-point record of everything implemented
