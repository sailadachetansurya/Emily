# NLP Emotion Model Training Essentials

## Purpose

This document is the practical reference for training and operating the current NLP emotion model used by Emily.

It covers:
- What the current NLP model is and is not
- Data requirements and dataset schema
- Dataset preparation pipeline from Hugging Face
- End-to-end training workflow
- Model artifact structure and loading
- Inference behavior and integration with the pipeline
- Common errors and how to fix them
- Recommended next upgrades

## Scope and Current Model Type

The current trained model is a lightweight lexical classifier designed for transparency and fast iteration.

It predicts:
- `activation`
- `social_orientation`
- `stability`

It also predicts:
- `valence` using token-level average score estimation

Important:
- This is not a transformer-based deep model.
- It is intentionally inspectable and deterministic enough for controlled pipeline behavior.
- It is suitable as a baseline and for local/offline experimentation.

## Code Locations

Core architecture and inference:
- `src/pipeline/stages/emotion_engine/nlp_emotion_model.py`

Trainer and trained-model runtime:
- `src/pipeline/stages/emotion_engine/train_nlp_emotion_model.py`

Dataset preparation from HF:
- `src/pipeline/stages/emotion_engine/dataset_prep.py`

Zero-argument dataset prep launcher:
- `run_prepare_emotion_dataset.py`

Zero-argument training launcher:
- `run_train_nlp_emotion_model.py`

Dataset docs and outputs:
- `dataset/README.md`
- `dataset/emotion_train.jsonl`
- `dataset/emotion_validation.jsonl`
- `dataset/emotion_test.jsonl`

Model artifact output:
- `models/emotion_model.json`

## Architecture Essentials

### 1. Tokenizer

Current tokenizer:
- `WhitespaceTokenizer`

Behavior:
- Splits by whitespace
- Strips punctuation from token edges
- Lowercases tokens

### 2. Feature Encoder

Current encoder:
- `LexicalFeatureEncoder`

Produces:
- token count
- question count
- exclamation count
- lexicon hit counts (anxiety, sadness, anger, positive, uncertainty, intensity)

### 3. Projection Head

Current projection:
- `EmotionProjectionHead`

Maps features to:
- `emotional_valence` in range [-1.0, 1.0]
- `activation_level` (low/medium/high)
- `social_orientation` (withdrawn/neutral/reaching)
- `stability` (stable/fragile/volatile)

## Training Data Contract

Each JSONL row must include:
- `text` (string)
- `valence` (float, range [-1.0, 1.0])
- `activation` (one of: low, medium, high)
- `social_orientation` (one of: withdrawn, neutral, reaching)
- `stability` (one of: stable, fragile, volatile)

Example:

```json
{"text":"I feel anxious and worried","valence":-0.7,"activation":"high","social_orientation":"reaching","stability":"fragile"}
```

Validation is strict and fail-fast in `EmotionModelTrainer.parse_example`.

## Dataset Preparation Workflow

The prep flow reads and normalizes:
- `dair-ai/emotion` (parquet splits)
- `Alignment-Lab-AI/EmotionDialogue` (`conversations.jsonl`)

It writes:
- unified split files in `dataset/`
- source-normalized files in `dataset/processed/`
- summary metadata in `dataset/dataset_summary.json`

Run:

```powershell
e:/Code/Emily/.venv/Scripts/python.exe .\run_prepare_emotion_dataset.py
```

Expected output includes:
- `dataset/emotion_train.jsonl`
- `dataset/emotion_validation.jsonl`
- `dataset/emotion_test.jsonl`
- `dataset/processed/*.jsonl`

## Training Workflow

### Fast path (recommended)

Run the zero-argument training launcher:

```powershell
e:/Code/Emily/.venv/Scripts/python.exe .\run_train_nlp_emotion_model.py
```

It uses:
- input: `dataset/emotion_train.jsonl`
- output: `models/emotion_model.json`

### Direct trainer CLI path

You can run the trainer module directly:

```powershell
$env:PYTHONPATH='src'
e:/Code/Emily/.venv/Scripts/python.exe -m pipeline.stages.emotion_engine.train_nlp_emotion_model --data dataset/emotion_train.jsonl --output models/emotion_model.json
```

## What the Trainer Learns

The trainer builds:
- Naive Bayes style token statistics per categorical target
  - activation
  - social_orientation
  - stability
- Token-level valence scores

Under the hood:
- label priors from counts
- token likelihoods with additive smoothing
- score aggregation in log space

## Model Artifact Structure

Saved artifact fields:
- `architecture`
- `tokenizer`
- `categorical_models`
- `valence_token_scores`
- `metadata`

`categorical_models` contains per-field:
- `labels`
- `label_counts`
- `token_counts`
- `token_totals`
- `vocabulary`

## Runtime Inference

Runtime class:
- `TrainedEmotionModel`

Typical use:
- load artifact
- `classify(text)` for direct text
- `infer(request_or_text)` for pipeline-compatible call sites

Inference output type:
- `EmotionState`

Returned signal example:
- `token_count`

## Integration with Emotive Pipeline

Pipeline supports selecting emotion model kind at runtime.

Typical mode values:
- `heuristic`
- `nlp_sample`

If using trained artifacts, wire a trained model instance where the emotion engine is constructed.

## Troubleshooting

### Error: `ModuleNotFoundError: No module named 'pipeline'`

Cause:
- Running a script that imports `pipeline` without adding `src` to import path.

Fix options:
- Use launchers that self-bootstrap `src` path.
- Or set `PYTHONPATH=src` before module execution.

### Error: `Training data file not found`

Cause:
- Missing `dataset/emotion_train.jsonl`.

Fix:
- Run dataset prep launcher first.
- Verify working directory is repository root.

### Error: `invalid activation/social_orientation/stability label`

Cause:
- Data labels do not match allowed sets.

Fix:
- Normalize labels to allowed values before training.

### Error: `valence must be between -1.0 and 1.0`

Cause:
- Out-of-range valence in JSONL rows.

Fix:
- Clamp or clean values in dataset prep/cleaning stage.

## Practical Quality Checklist

Before training:
- `dataset/emotion_train.jsonl` exists and is non-empty
- Labels are in valid controlled vocab
- Valence values are in range
- Dataset has mixed classes, not single-label dominated

After training:
- `models/emotion_model.json` exists
- Load and run smoke inference on 5-10 manual prompts
- Verify outputs look emotionally coherent

## Recommended Next Upgrades

1. Add dataset inspection report before training:
- label distribution
- average text length
- null/invalid row counts

2. Improve lexical features:
- negation handling (for example, "not happy")
- phrase-level n-grams
- uncertainty and intensity weighting refinements

3. Add held-out evaluation metrics:
- macro F1 for categorical fields
- MAE for valence
- confusion matrices

4. Add model version metadata:
- dataset hash
- train timestamp
- code version

5. Add artifact registry convention:
- `models/emotion_model_<date>_<tag>.json`

## Minimal End-to-End Command Sequence

```powershell
# 1) Prepare datasets
 e:/Code/Emily/.venv/Scripts/python.exe .\run_prepare_emotion_dataset.py

# 2) Train model
 e:/Code/Emily/.venv/Scripts/python.exe .\run_train_nlp_emotion_model.py

# 3) (Optional) Run tests
 $env:PYTHONPATH='src'; e:/Code/Emily/.venv/Scripts/python.exe -m unittest discover -s tests -p 'test_*.py'
```

This sequence is the baseline operational loop for the current NLP emotion training stack.
