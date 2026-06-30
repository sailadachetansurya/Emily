# Dataset

## Purpose

Training datasets for the NLP emotion model, prepared from Hugging Face sources into unified JSONL format.

## Ownership

All files in `dataset/` belong to this doc.

## Local Contracts

- Raw data sources: `dair-ai/emotion` (parquet splits), `Alignment-Lab-AI/EmotionDialogue` (JSONL)
- Prep script: `run_prepare_emotion_dataset.py` → calls `dataset_prep.prepare_from_hf()`
- Output format: JSONL with fields `text`, `emotion_label`, `valence`, `activation`, `social_orientation`, `stability`, `source`, `split`
- Training uses: `dataset/emotion_train.jsonl`
- Evaluation uses: `dataset/emotion_validation.jsonl`, `dataset/emotion_test.jsonl`
- Processed intermediates: `dataset/processed/dair_ai_*.jsonl`, `dataset/processed/emotion_dialogue.jsonl`
- Summary: `dataset/dataset_summary.json`

## Work Guidance

- Each JSONL line must have all five training fields: `text`, `valence`, `activation`, `social_orientation`, `stability`
- Valence is a float in [-1.0, 1.0]; activation is `low`/`medium`/`high`; social_orientation is `withdrawn`/`neutral`/`reaching`; stability is `stable`/`fragile`/`volatile`
- The training launcher expects `dataset/emotion_train.jsonl` to exist before running
- When adding new data sources, add a new `normalize_*_frame()` function in `dataset_prep.py` and update `prepare_from_hf()`

## Verification

- `python -m pytest tests/test_dataset_prep.py` covers normalization
