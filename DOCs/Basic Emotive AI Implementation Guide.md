# Basic Emotive AI Implementation Guide

## Goal
Build a practical emotive AI system using a constrained pipeline without the advanced control model (no RL central mind).

## Scope
This guide focuses on:
- Offline or local-first deployment
- Deterministic orchestration and safety
- Emotion-aware conversational behavior
- Fast iteration without model retraining

This guide excludes:
- Reinforcement learning controllers
- Autonomous policy self-optimization
- Training a new foundation model from scratch

## Recommended Baseline Stack
- LLM runtime: Ollama
- Base model: Mistral or Llama-family instruction model
- Orchestration: Flowise, LangFlow, or n8n
- Vector database: Chroma
- Memory store: small factual profile + emotional continuity summaries
- Optional classifier: lightweight emotion detector

## Core Architecture
Use this fixed pipeline:

User Input
-> Emotional Perception Layer
-> Conversation State and Memory
-> Emotive Response Policy
-> LLM Generation
-> Post-Processing (tone and safety)
-> Final Response

## Design Principles That Make This Work
- Constrain behavior first, then generate text.
- Keep policy deterministic, not LLM-decided.
- Keep memory compact and structured.
- Optimize for emotional attunement, not maximum correctness.
- Never allow responses to promote dependency or exclusivity.

## Implementation Process

## Step 1: Define Product Behavior
Decide what "good" interaction means before coding.

Create a behavior spec containing:
- Target tone: calm, warm, non-clinical
- Verbosity target: short to medium replies
- Allowed speech acts: reflect, validate, soft question, gentle reframe
- Disallowed speech acts: diagnose, command, pressure, exclusivity
- Escalation rules: when to switch to safety or human-support language

Output artifact:
- behavior-policy.md

## Step 2: Build Emotion Perception Layer
Convert user text into a limited emotional state representation.

Use either:
- Rule-based feature extractor for initial version, or
- Small classifier if you already have labeled examples

Recommended output schema:
- emotional_valence: -1.0 to +1.0
- activation_level: low, medium, high
- social_orientation: withdrawn, neutral, reaching
- stability: stable, fragile, volatile

Implementation rules:
- Keep schema low-dimensional and stable.
- Do not pass raw classifier chain-of-thought to the LLM.
- Pass only normalized labels and confidence bands.

Output artifact:
- emotion-state.json

## Step 3: Implement Dual Memory
Use two memory channels instead of one large chat history.

Factual memory (small, stable):
- Name, preferences, recurring factual details
- Strict size limits and update rules

Emotional continuity memory (larger, summarized):
- Recurring emotional themes
- Known soothing triggers and agitation triggers
- Unresolved emotional threads

Implementation rules:
- Store summaries, not raw long transcripts.
- Refresh summaries periodically (for example every N turns).
- Add recency and confidence metadata.

Output artifacts:
- factual-profile.json
- emotional-summary-index (vector DB)

## Step 4: Build Deterministic Response Policy
Create a rules engine that chooses response mode before generation.

Example response modes:
- reflection
- validation
- soft-question
- brief-presence
- gentle-redirection

Each mode should map to a parameter bundle:
- max_tokens
- temperature
- penalties
- allowed speech acts
- disallowed speech acts

Implementation rules:
- Policy decides mode; LLM does not choose mode.
- Advice is blocked unless user explicitly asks.
- High-volatility states force conservative modes.

Output artifact:
- policy-mapper.json

## Step 5: Assemble Prompt Construction
Prompt should combine:
- Stable system instructions
- Current emotional state summary
- Relevant factual memory snippet
- Relevant emotional continuity snippet
- Selected response mode constraints

Prompt rules:
- Keep instructions short and consistent across turns.
- Prefer constraints over style-heavy wording.
- Include one explicit do-not list in every generation request.

Output artifact:
- prompt-template.md

## Step 6: Configure LLM Generation
Use a smaller or mid-sized model with controlled generation settings.

Recommended defaults:
- max_tokens: 60 to 140
- temperature: 0.6 to 0.9 by mode
- repetition control: moderate
- stop conditions: configured for concise turn-taking

Implementation rules:
- Avoid long exhaustive answers unless explicitly requested.
- Keep first pass concise and emotionally present.

Output artifact:
- generation-config.yaml

## Step 7: Add Post-Processing and Safety Filters
Apply deterministic checks after generation.

Pattern filters should:
- Block command-heavy phrasing like "you should" and "you need to"
- Remove diagnostic framing
- Remove exclusivity language

Speech-act validator should:
- Classify output as reflection, question, advice, reassurance, or other
- Compare against allowed acts from selected mode
- Regenerate with stricter constraints if violated

Safety style transformation should:
- Replace hard refusal tone with softer supportive wording
- Preserve boundaries and policy constraints

Output artifacts:
- response-filters.yaml
- speech-act-validator.json

## Step 8: Orchestrate the Full Flow
Implement one execution graph in Flowise, LangFlow, or n8n.

Required nodes:
- Input ingestion
- Emotion perception
- Memory retrieval and summarization
- Policy mode selection
- Prompt assembly
- LLM call
- Post-processing filters
- Output and telemetry

Implementation rules:
- Keep each node deterministic except LLM generation.
- Add retry path only for policy violations.
- Log every selected mode and filter action.

Output artifact:
- pipeline-flow.json

## Step 9: Evaluation and Readiness Checks
Define launch criteria before public usage.

Quality metrics:
- Emotional attunement score (human rubric)
- Over-advice rate
- Verbosity drift
- Policy violation rate
- Regeneration frequency

Safety metrics:
- Exclusivity phrase incidence
- Harmful certainty incidence
- Authority drift incidence

Readiness gates:
- No critical safety violations in evaluation set
- Stable mode selection under repeated prompts
- Consistent response pacing across long sessions

Output artifact:
- eval-report.md

## Operational Considerations
- Keep all policies versioned and auditable.
- Separate policy files from prompt files.
- Use feature flags for any major behavior changes.
- Start with manual review for sensitive conversation cohorts.
- Build rollback paths for policy and filter updates.

## Common Failure Modes and Fixes
- Failure: Replies become too helpful or solution-heavy.
  Fix: tighten disallowed speech acts and lower max tokens.

- Failure: Model becomes repetitive.
  Fix: increase memory diversity and tune repetition controls.

- Failure: Inconsistent emotional continuity.
  Fix: improve summary refresh cadence and retrieval ranking.

- Failure: Safety tone sounds robotic.
  Fix: adjust post-processing templates while preserving boundaries.

## Minimum Viable Milestone Plan
- Milestone 1: Emotion schema + deterministic policy + basic prompting
- Milestone 2: Dual memory + retrieval tuning + post-generation filters
- Milestone 3: Evaluation harness + telemetry + safety hardening

## Final Checklist
- Behavior policy is explicit and testable.
- Emotion state schema is compact and stable.
- Memory is dual-channel and summarized.
- Response mode is selected deterministically before generation.
- Post-processing blocks forbidden patterns reliably.
- Evaluation covers quality and safety before rollout.

## Suggested Folder Structure
- docs/behavior-policy.md
- configs/policy-mapper.json
- configs/generation-config.yaml
- configs/response-filters.yaml
- prompts/prompt-template.md
- memory/factual-profile-schema.json
- memory/emotional-summary-schema.json
- flows/pipeline-flow.json
- reports/eval-report.md

## Custom Orchestration For Maximum Control
If you want strict control over execution, latency, and resource usage, replace visual workflow tools with a custom orchestrator service.

## What You Gain
- Full control over scheduling, retries, and backpressure
- Fine-grained memory and token budgets per stage
- Deterministic ordering with explicit state transitions
- Easier profiling and cost attribution per pipeline component

## Recommended Runtime Shape
Use a single coordinator process with explicit modules:
- input-gateway
- emotion-engine
- memory-manager
- policy-engine
- prompt-builder
- llm-client
- safety-processor
- telemetry-writer

Request lifecycle:
1. Accept request and assign request_id
2. Build execution context (budgets, deadlines, policy version)
3. Run each stage with stage-level timeout and fallback
4. Validate output against policy constraints
5. Persist logs, metrics, and memory updates atomically

## Control Plane vs Data Plane
Separate decisions from execution.

Control plane responsibilities:
- Versioned policy loading
- Dynamic budget rules (CPU, RAM, token, latency)
- Feature flags and rollout controls
- Kill-switch for unsafe or degraded modes

Data plane responsibilities:
- Actual request processing
- LLM and vector DB calls
- Post-processing and response delivery

This separation makes failure handling and rollback much cleaner.

## Resource Management Model
Define hard budgets before processing begins.

Per-request budget envelope:
- max_total_latency_ms
- max_total_tokens
- max_memory_reads
- max_regeneration_attempts

Per-stage budget examples:
- emotion stage: low CPU, strict timeout
- memory retrieval: bounded top_k and strict context size
- generation: token cap by mode
- post-processing: deterministic, no unbounded loops

Budget enforcement rules:
- If stage exceeds timeout, invoke fallback mode immediately
- If token budget is near limit, force concise response mode
- If memory retrieval overflows context, keep highest relevance plus recency

## Scheduling and Concurrency
Use a priority queue with admission control.

Recommended policy:
- Separate queues for interactive vs background tasks
- Concurrency caps per model instance
- Warm pool for LLM workers
- Circuit breaker for downstream dependency failures

Backpressure strategy:
- Queue length threshold triggers degraded mode
- Degraded mode skips non-critical enrichments
- Hard saturation returns graceful retry response

## Deterministic State Machine
Represent pipeline as a finite state machine.

Example states:
- received
- emotion_scored
- memory_resolved
- policy_selected
- generated
- safety_validated
- completed
- failed

Requirements:
- Every transition has a guard condition
- Every failure has a fallback transition
- All transitions are logged with timestamp and reason

## Failure Handling and Fallbacks
Define fallback behavior per stage.

Examples:
- Emotion model failure -> fallback to neutral emotional state
- Memory store unavailable -> run with short-term context only
- LLM timeout -> retry once with lower max_tokens
- Safety validation failure -> regenerate with strict mode then safe template

Do not chain unlimited retries. Use bounded retries with clear terminal states.

## Observability and Auditing
Capture structured telemetry for each request.

Minimum logs:
- request_id, user_session_id, pipeline_version
- stage start/end timestamps
- selected response mode and policy version
- token usage in/out
- filter and regeneration events
- final safety status

Minimum dashboards:
- p50/p95 latency by stage
- token usage by mode
- regeneration rate and causes
- policy violation trends
- safety filter trigger frequency

## Configuration Strategy
Keep behavior configurable without code edits.

Recommended config files:
- configs/runtime-budgets.yaml
- configs/queue-policy.yaml
- configs/fallback-rules.yaml
- configs/feature-flags.yaml

Operational rules:
- Version and checksum all configs
- Rollout config changes gradually
- Keep one-command rollback path

## Security and Data Governance
- Encrypt stored memory and logs at rest
- Minimize personal data in telemetry
- Apply retention limits for conversation artifacts
- Keep policy and safety events immutable for audit

## Suggested Implementation Sequence
1. Build the deterministic state machine and request envelope.
2. Integrate emotion, memory, policy, generation, and safety stages.
3. Add budget enforcement and bounded retries.
4. Add telemetry and dashboards.
5. Add degraded mode and dependency circuit breakers.
6. Load test, then tighten budgets from real traces.

## Practical Rule Of Thumb
Custom orchestration is worth it when your priority is predictable behavior under load, strict resource control, and production-grade observability. If your current scale is low, start with this architecture but keep interfaces simple so you can iterate quickly.

## Offline LLM Strategy (Fine-Tunable and Customizable)
If you want full local control, treat the LLM as a pluggable local provider and keep your orchestration logic provider-agnostic.

## Target Outcomes
- All inference runs locally (no external API dependency)
- Model behavior can be customized through prompt, adapters, and optional fine-tuning
- Context injection and call passing remain controlled by your orchestrator
- Easy provider swap without rewriting pipeline logic

## Recommended Local Setup
- Runtime provider: Ollama (primary)
- Optional alternate providers: llama.cpp server, vLLM local deployment
- Embeddings: local embedding model through Ollama or sentence-transformers local runtime
- Vector DB: Chroma (local persistence)

## Provider Abstraction Layer
Define one internal interface and map all providers to it.

Core interface methods:
- generate(request)
- embed(texts)
- health()
- load_model(model_id)
- unload_model(model_id)

Request envelope fields:
- model_id
- system_prompt
- user_prompt
- context_blocks
- generation_params
- safety_mode
- trace_id

This keeps call passing stable even if you switch model runtimes.

## Ollama Call-Passing Pattern
For generation, route through your orchestrator, not directly from clients.

Suggested flow:
1. Orchestrator receives user request
2. Policy engine selects mode and generation constraints
3. Memory manager selects context blocks
4. Prompt builder composes final request envelope
5. LLM client sends request to local Ollama endpoint
6. Safety processor validates response
7. Orchestrator returns final output

Implementation notes:
- Use local HTTP endpoint with strict timeout and retry budget.
- Pass context as explicit blocks from your retrieval stage, not implicit chat dump.
- Keep prompt assembly deterministic and versioned.

## Model Customization Ladder (Low Risk to High Risk)
1. Prompt and policy tuning
- Fastest and safest path
- Best for tone, pacing, verbosity, and response style

2. Retrieval tuning (RAG quality)
- Improves domain grounding without changing model weights
- Best for private and frequently changing knowledge

3. Adapter tuning (LoRA/QLoRA)
- Useful when behavior consistency is insufficient via prompts alone
- Keep adapters task-focused and small

4. Full fine-tuning
- Use only when adapter performance is clearly insufficient
- Requires stricter data curation and evaluation controls

## Fine-Tuning Readiness Checklist
Before tuning weights, confirm:
- You have enough high-quality conversation examples for target behavior
- Prompt plus policy baseline is already stable
- Evaluation set includes both quality and safety cases
- You can compare tuned model against baseline using the same pipeline tests

If these are not met, improve policy and retrieval first.

## Data Requirements For Tuning
- Curated conversational samples aligned with desired tone
- Explicit labels for allowed and disallowed speech acts
- Negative examples (what not to say)
- Safety edge cases and boundary scenarios

Data hygiene rules:
- Remove sensitive identifiers
- Normalize formatting and metadata
- Deduplicate near-identical turns
- Keep train and eval sets strictly separated

## Runtime Resource Controls (Local Models)
- Pin per-model concurrency limits
- Set per-request token caps by response mode
- Enable model warm pool for common models
- Use model-level circuit breaker when latency spikes
- Prefer quantized models for predictable local throughput

## Multi-Model Routing (Optional)
Use deterministic routing rules for efficiency.

Example policy:
- Small model for reflection and short turns
- Medium model for complex emotional context
- Fallback model for timeout or overload scenarios

Routing keys:
- current mode
- context length
- volatility flag
- latency budget remaining

## Evaluation For Local Customized Models
Track these separately for each model or adapter version:
- emotional attunement score
- over-advice rate
- safety filter trigger rate
- latency p95
- token cost equivalent (local compute proxy)

Promotion rule:
- Only promote a tuned model if it improves attunement without degrading safety metrics.

## Deployment and Versioning
- Version model, adapter, prompt, and policy independently
- Record all four versions in request telemetry
- Support fast rollback to previous stable model bundle

Suggested bundle id format:
- model_bundle = model_version + adapter_version + prompt_version + policy_version

## Practical Recommendation
Start with Ollama plus strong policy constraints and RAG. Add LoRA only after you observe repeated behavior gaps that prompt and retrieval tuning cannot fix. Keep your orchestrator in control of call passing, context assembly, and safety so model changes do not break system behavior.
