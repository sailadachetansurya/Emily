# Working Index — Emily Emotive AI Pipeline

A point-by-point record of everything implemented in this project.

---

## 1. Core Pipeline Architecture

**Files:** `src/pipeline/orchestrator/pipeline.py`, `src/pipeline/contracts/`

- Flat sequential pipeline: Input Gateway → Emotion Engine → Memory Manager → Policy Engine → Prompt Builder → LLM Client → Safety Processor → Output
- Protocol-based stage interfaces in `contracts/interfaces.py` — every stage satisfies a Protocol
- Shared data models in `contracts/models.py` — immutable dataclasses (`RequestEnvelope`, `EmotionState`, `MemoryContext`, `ResponsePolicy`, `PromptBundle`, `GenerationResult`, `SafeResponse`, etc.)
- Orchestrator wires all stages, collects `StageTrace` entries per stage, emits them to telemetry

---

## 2. Input Gateway

**File:** `src/pipeline/stages/input_gateway/input_normalizer.py`

- `DefaultInputGateway` — normalizes user input by stripping whitespace and collapsing spaces
- First stage in the pipeline; produces a clean `RequestEnvelope`

---

## 3. Emotion Engine

**Files:** `src/pipeline/stages/emotion_engine/`

### 3a. Heuristic Classifier
- `HeuristicEmotionEngine` / `HeuristicEmotionClassifier` — keyword-rule-based emotion detection
- Rules for anxiety, sadness, anger, and positive emotions
- Adjusts valence with exclamation/question boosts
- Supports a plugin escape hatch via `EmotionClassifierPlugin` protocol

### 3b. Sample NLP Model
- `SampleNLPEmotionModel` — lightweight tokenizer → encoder → projection head architecture
- `WhitespaceTokenizer`, `LexicalFeatureEncoder`, `EmotionProjectionHead`
- Produces `EmotionState` with valence, activation, social orientation, stability, and signal dict

### 3c. Trained Model
- `TrainedEmotionModel` — loads a JSON artifact trained from labeled JSONL data
- Naive Bayes–style categorical prediction for activation, social orientation, stability
- Token-averaged valence prediction
- `EmotionModelTrainer` — trains from JSONL, saves artifact

### 3d. Dataset Preparation
- `dataset_prep.py` — normalizes Hugging Face datasets (`dair-ai/emotion`, `Alignment-Lab-AI/EmotionDialogue`) into unified JSONL
- Canonical `EMOTION_STATE_MAP` mapping dataset labels to `EmotionState` values
- Handles nested dialogue structures, multiple text/label key formats
- `prepare_from_hf()` — end-to-end: fetch, normalize, split, write JSONL, generate summary

---

## 4. Memory Manager

**Files:** `src/pipeline/stages/memory_manager/`

- `DualMemoryManager` — owns both factual and emotional memory stores
- `FactualMemoryStore` — key-value store with confidence-based trimming (max 32 items)
- `EmotionalMemoryStore` — embedding-based similarity search with recency weighting (max 64 items)
- Hash-based embedding for emotional records (lightweight, no external deps)
- `resolve()` produces `MemoryContext` with factual facts, emotional summary, and matched emotional records
- `InMemoryMemoryManager` — backward-compatible alias

---

## 5. Policy Engine

**File:** `src/pipeline/stages/policy_engine/response_policy_selector.py`

- `PolicyEngine` / `DeterministicPolicyEngine` / `RuleBasedPolicyEngine` — score-based policy selection
- Scores three dimensions: `emotional_risk`, `presence_need`, `redirection_need`
- Four policy modes: `reflection`, `soft_question`, `brief_presence`, `gentle_redirection`
- Each mode defines: allowed/disallowed speech acts, max tokens, temperature
- `PolicyDecision` returned with policy, score breakdown, and explanation
- Config-driven mode parameters via `configs/policy_config.json`

---

## 6. Prompt Builder

**File:** `src/pipeline/stages/prompt_builder/prompt_assembler.py`

- `PromptAssembler` / `DefaultPromptBuilder` — composes `PromptBundle` from state, memory, and policy
- System prompt includes Emily personality + allowed/disallowed speech acts
- Context blocks: emotion state, factual memory, emotional continuity, emotional matches
- Generation params: max_tokens, temperature, mode, top_p, presence/frequency penalty
- DO NOT constraints: diagnostic language, authority claims, unasked advice, disallowed speech acts

---

## 7. LLM Client

**Files:** `src/pipeline/stages/llm_client/`

- `LocalLLMClient` — HTTP client for local Ollama API
- Supports both streaming and non-streaming modes
- `OllamaPromptRequest` / `OllamaResponseContract` — typed request/response contracts with JSON schema validation
- Stream chunk parsing with done-sentinel detection
- `fallback_generation()` — returns a safe default when Ollama is unavailable
- `OllamaStubClient` — wrapper for backward compatibility
- Structured error hierarchy: `OllamaError`, `OllamaContractError`, `OllamaConfigurationError`, `OllamaResponseParseError`, `OllamaTransportError`

---

## 8. Safety Processor

**File:** `src/pipeline/stages/safety_processor/response_guard.py`

- `OutputPruner` — single-pass post-processing of LLM output
- Pattern filters: strips forbidden phrases ("you should", "diagnose", etc.)
- Speech-act classification via string matching (question, reflect, advice, presence, statement)
- Fit-space projection: `force_reflection()`, `force_soft_question()`, `force_presence()`
- Style normalization: truncates to max sentences (default 4)
- `ProjectionSafetyProcessor` / `DefaultSafetyProcessor` — wraps prune output into `SafeResponse`
- `was_regenerated` field plumbed but currently hardcoded to False (reserved for future use)

---

## 9. Reasoning Loop (Self-Critique)

**Files:** `src/pipeline/stages/reasoning_loop/`

- `ReasoningLoopOrchestrator` — wraps LLM generation with internal reasoning and optional critique
- **Activation gating**: only engages when `emotional_risk >= threshold` and `enabled` config is True
- **Reasoning step**: LLM produces JSON with `chosen_approach`, `rationale`, `risk_assessment`
- **Enhanced generation**: reasoning trace injected into system prompt
- **Critique step**: LLM evaluates its own output against policy rules (`PolicyCritiqueEvaluator`)
- **Regeneration loop**: if critique finds violations, tighten prompt and regenerate (max N iterations)
- **Fail-open design**: parse failures produce safe defaults, never block production
- Stage-internal models (`ReasoningTrace`, `CritiqueResult`, `IterationRecord`) not exported to contracts
- Config: `reasoning_loop_enabled`, `reasoning_loop_max_iterations`, `reasoning_loop_activation_threshold`
- Iteration data attached to `GenerationResult.metadata["reasoning_loop"]` for telemetry

---

## 10. Telemetry

**File:** `src/pipeline/telemetry/recorder.py`

- `JsonTelemetrySink` — appends JSONL records with timestamp, trace name, and payload
- Called by orchestrator after each stage completes
- Log path configurable via `configs/config.json`

---

## 11. Evaluation Harness

**File:** `src/pipeline/evaluation/harness.py`

- `EvaluationHarness` — runs test cases through the full pipeline
- `EvaluationCase` — name, user input, expected keywords
- `EvaluationResult` — response text, pass/fail, notes
- Keyword-matching quality check

---

## 12. Configuration System

**Files:** `src/pipeline/config/runtime.py`, `configs/`

- `RuntimeConfig` — frozen dataclass with all pipeline settings
- `ConfigLoader` — validates `config.json` against a fixed schema
- Rejects unknown fields, validates types and ranges
- Required fields: model_name, ollama_base_url, request_timeout_seconds, ollama_stream, ollama_generate_path, telemetry_path, max_factual_items, max_emotional_items
- Optional fields: emotion_model_kind, reasoning_loop_*
- `configs/policy_config.json` — per-mode parameter overrides
- `configs/safety_config.json` — forbidden phrases, max sentences
- `configs/config.schema.json` — JSON Schema reference

---

## 13. Web Control Panel

**Files:** `server.py`, `templates/`, `static/`

### Backend (FastAPI)
- Page routes: `/` (Overview), `/pipeline`, `/training`, `/config`, `/logs`
- API routes: `/api/pipeline/run`, `/api/dataset/prepare`, `/api/model/train`, `/api/jobs/{id}`, `/api/config`, `/api/telemetry`, `/api/status`
- Background job system with thread-based execution and polling
- Serves static files from `static/` directory

### Frontend
- 5 separate pages with shared sidebar navigation
- Minimalist Hermes-like design: grayscale palette, generous white space, clean typography
- DejaVu Sans typography, subtle borders, no decorative color
- Theme system with 5 themes: Modern Minimalist, Sunset Boulevard, Ocean Depths, Midnight Galaxy, Arctic Frost
- Theme switching via CSS custom properties, persisted in localStorage
- Real-time job tracking with status polling
- Interactive config editor with inline save

---

## 14. DOX Framework

**Files:** `AGENTS.md` (root + children)

- Root `AGENTS.md` — project-wide instructions, global preferences, Child DOX Index
- `src/pipeline/AGENTS.md` — pipeline package contracts, stage wiring rules
- `src/pipeline/stages/emotion_engine/AGENTS.md` — emotion perception, training, dataset prep
- `src/pipeline/stages/reasoning_loop/AGENTS.md` — reasoning loop contracts and verification
- `configs/AGENTS.md` — configuration schema and validation rules
- `dataset/AGENTS.md` — dataset preparation workflow and format specs

---

## 15. Test Suite

**Files:** `tests/`

- `test_pipeline_core.py` — 17 tests covering prompt assembly, policy determinism, emotion heuristics, memory resolution, Ollama contracts, config validation, NLP model, output pruning, pipeline smoke
- `test_reasoning_loop.py` — 19 tests covering activation gating, reasoning parsing, critique evaluation, prompt construction, full loop with mock LLM
- `test_nlp_training.py` — 2 tests covering training round-trip and invalid row rejection
- `test_dataset_prep.py` — 2 tests covering dair-ai and emotion dialogue normalization
- **Total: 40 tests, all passing**

---

## 16. Training Scripts

**Files:** `run_prepare_emotion_dataset.py`, `run_train_nlp_emotion_model.py`

- `run_prepare_emotion_dataset.py` — fetches and normalizes HF datasets into training JSONL
- `run_train_nlp_emotion_model.py` — trains the NLP emotion model from labeled JSONL
- Both scripts manipulate `sys.path` for standalone execution

---

## 17. Comprehensive Error Reporting

**Files:** `server.py`, `static/app.js`, `static/styles.css`

- `ErrorDetail` dataclass captures structured error info: `stage`, `part`, `detail`, `hint`, `error_type`, `traceback`
- `_extract_error()` introspects pipeline exceptions (`ConfigValidationError`, `OllamaError`, etc.) to extract structured fields
- `Job` dataclass now includes `error_detail: ErrorDetail | None`, `started_at`, `finished_at`, `duration_ms`
- `_job_to_dict()` serializes full error details for API responses
- Frontend `formatError()` renders structured errors with type badge, stage/part context, and hint
- CSS classes `.error`, `.err-type`, `.err-stage`, `.err-part` for styled error display
- Output containers get `.error` class on failure with red border highlight

---

## 18. State Persistence Across Tabs

**Files:** `server.py` (`GET /api/jobs`), `static/app.js`

- **Problem:** Navigating between pages cleared the JavaScript `jobs` Map, losing track of running jobs
- **Solution:** Two-layer persistence:
  1. **localStorage:** Job data serialized to `emily-jobs` key on every update; restored on page load via `loadJobsFromStorage()`
  2. **Server sync:** `GET /api/jobs` endpoint returns all server-side jobs; `syncJobsFromServer()` merges server state with local state on page load
- Running jobs are re-polled automatically after sync
- Job list sorted: running jobs first, then by most recent `started_at`
- `addJob()` and `updateJob()` both call `saveJobsToStorage()` to keep localStorage current
- `pollJob()` error handling: if polling fails, job status updated to failed with error message

---

## 19. Pipeline Summary Logging

**Files:** `server.py` (`_write_summary()`), `Summary.md`

- After every pipeline run, `_write_summary()` appends a structured markdown entry to `Summary.md`
- Each entry includes:
  - Timestamp (UTC)
  - User input
  - Pipeline response text
  - Safety notes (if any)
  - Stage trace table (stage name + status)
- File is append-only — accumulates history across runs
- Summary path exposed via `GET /api/status`

---

## 20. Job Timing and Metadata

**Files:** `server.py`

- `Job.started_at` — ISO timestamp when job thread starts
- `Job.finished_at` — ISO timestamp when job completes or fails
- `Job.duration_ms` — elapsed time in milliseconds
- All three fields serialized in API responses and displayed in the job list
- `_run_job()` uses `finally` block to guarantee timing is captured even on failure

---

## 21. llama.cpp Client (Ollama Alternative)

**Files:** `src/pipeline/stages/llm_client/llamacpp_client.py`, `src/pipeline/orchestrator/pipeline.py`

- `LlamaCppClient` — HTTP client for llama.cpp's OpenAI-compatible API (`/v1/chat/completions`)
- Same interface as `LocalLLMClient` — implements `generate(PromptBundle) -> GenerationResult`
- Converts `PromptBundle` to OpenAI chat messages format (system + context + constraints + user)
- Config: `llm_provider` (`ollama` | `llamacpp`), `llamacpp_base_url`, `llamacpp_n_tokens`
- Pipeline selects client via `build_llm_client()` based on `config.llm_provider`
- Health endpoint checks both Ollama and llama.cpp, reports which is active

---

## 22. Episodic Memory

**Files:** `src/pipeline/stages/memory_manager/episodic_memory.py`, `src/pipeline/stages/memory_manager/memory_resolver.py`

- `EpisodicMemoryStore` — stores user exchanges as episodes with facts and distilled summaries
- `Exchange` dataclass — user_input, response, timestamp, emotion_snapshot
- `Episode` dataclass — episode_id, user_id, exchanges list, facts list, distilled_summary
- **Recording**: after each pipeline run, `DualMemoryManager.record_exchange()` stores the exchange
- **Fact extraction**: personal markers ("my name is", "i work", "i feel", etc.) extracted from user input
- **Auto-distillation**: after `episodic_max_exchanges` (default 10) exchanges, episode is compressed:
  - Keeps facts mentioned more than once or all if few facts
  - Generates distilled summary from kept facts
  - Clears raw exchanges (saves memory)
- **Episode TTL**: new episode starts after `episodic_ttl_hours` (default 24) hours
- **Context resolution**: `get_context_summary()` returns last 3 episodes' summaries for prompt injection
- **Fact merging**: episodic facts merged with factual memory in `MemoryContext`
- Config: `episodic_max_exchanges`, `episodic_ttl_hours`, `episodic_max_episodes`

---

## 23. Model Readiness Dashboard

**Files:** `server.py` (`GET /api/health`), `templates/pages.py`, `static/styles.css`

- Health endpoint checks all pipeline components: Heuristic Emotion, NLP Emotion, Trained Model, Ollama, llama.cpp, Reasoning Loop
- Reports status: ready, offline, missing, disabled, wrong_model, blocked
- Overview page shows health grid with status indicators and details
- Active LLM provider highlighted based on `llm_provider` config

---

## 24. Stage Progress Tracking

**Files:** `src/pipeline/orchestrator/pipeline.py`, `server.py`, `templates/pages.py`, `static/styles.css`, `static/app.js`

- Pipeline accepts `stage_callback` — called before each stage with stage name
- Job tracks `current_stage` and `stages_completed` in real-time
- Frontend polls job status and updates animated stage progress visualization
- 7-stage visual tracker: Input → Emotion → Memory → Policy → Prompt → LLM → Safety
- Steps transition: pending (gray) → active (pulsing) → done (filled) → failed (red)
- Auto-hides 3 seconds after completion
