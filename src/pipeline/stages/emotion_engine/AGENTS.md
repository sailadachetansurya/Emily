# Emotion Engine Stage

## Purpose

Rule-based and NLP-based emotion perception, plus training pipeline and dataset preparation for the NLP emotion model.

## Ownership

All files in `src/pipeline/stages/emotion_engine/` belong to this doc.

## Local Contracts

- **Heuristic path**: `HeuristicEmotionEngine` uses keyword rules; deterministic, no external deps
- **NLP path**: `SampleNLPEmotionModel` uses tokenizer → encoder → projection head; lightweight, inspectable
- **Trained model path**: `TrainedEmotionModel` loads a JSON artifact; uses Naive Bayes–style classification
- **Dataset prep**: `dataset_prep.py` normalizes HF datasets (`dair-ai/emotion`, `Alignment-Lab-AI/EmotionDialogue`) into unified JSONL
- **Training**: `train_nlp_emotion_model.py` trains categorical models + valence token scores from JSONL
- Model selection is driven by `config.emotion_model_kind`: `"heuristic"` (default) or `"nlp_sample"`

## Work Guidance

- All emotion models must implement `infer(request_or_text) -> EmotionState`
- The `EmotionState` contract fields: `emotional_valence` (float, -1..1), `activation_level`, `social_orientation`, `stability`, `signals` (dict)
- Training data JSONL schema: `text`, `valence`, `activation`, `social_orientation`, `stability`
- `EMOTION_STATE_MAP` in `dataset_prep.py` is the canonical mapping from dataset labels to EmotionState values
- When adding new emotion categories, update `EMOTION_STATE_MAP`, `DAIR_AI_LABELS`, and `EMOTION_SYNONYMS` together
- `nlp_emotion_model.py` architecture classes (`WhitespaceTokenizer`, `LexicalFeatureEncoder`, `EmotionProjectionHead`) are intentionally lightweight stubs for swappability

## Verification

- `python -m pytest tests/test_pipeline_core.py -k emotion` covers heuristic and NLP model classification
- `python -m pytest tests/test_nlp_training.py` covers training round-trip
- `python -m pytest tests/test_dataset_prep.py` covers dataset normalization
