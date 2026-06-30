# Configs

## Purpose

Runtime JSON configuration files that control pipeline behavior, policy parameters, and safety constraints.

## Ownership

All files in `configs/` belong to this doc.

## Local Contracts

- `config.json` — Main runtime config; validated by `ConfigLoader` against a fixed schema
- `config.schema.json` — JSON Schema for `config.json` (documentation/reference)
- `policy_config.json` — Policy mode overrides (max_tokens, temperature per mode)
- `safety_config.json` — Forbidden phrases and max sentence count for output pruning
- `pipeline_config.json` — Pipeline-level settings (if present)

## Work Guidance

- `config.json` fields are validated at startup; unknown fields are rejected with `ConfigValidationError`
- Required fields: `model_name`, `ollama_base_url`, `request_timeout_seconds`, `ollama_stream`, `ollama_generate_path`, `telemetry_path`, `max_factual_items`, `max_emotional_items`
- Optional fields: `emotion_model_kind` (must be `"heuristic"` or `"nlp_sample"`)
- Policy config modes: `reflection`, `soft_question`, `brief_presence`, `gentle_redirection`
- Safety config keys: `forbidden_phrases` (list of strings), `max_sentences` (int)
- When adding new config fields, update both `RUNTIME_CONFIG_SCHEMA` in `config/runtime.py` and `config.schema.json`

## Verification

- `python -m pytest tests/test_pipeline_core.py -k config` covers config validation
