# Dataset Folder

Put all training datasets for Emily here.

Prepare the datasets from Hugging Face with:

```powershell
e:/Code/Emily/.venv/Scripts/python.exe .\run_prepare_emotion_dataset.py
```

This will create:
- `dataset/emotion_train.jsonl`
- `dataset/emotion_validation.jsonl`
- `dataset/emotion_test.jsonl`
- `dataset/processed/dair_ai_train.jsonl`
- `dataset/processed/dair_ai_validation.jsonl`
- `dataset/processed/dair_ai_test.jsonl`
- `dataset/processed/emotion_dialogue.jsonl`
- `dataset/dataset_summary.json`

The training launcher then uses:
- `dataset/emotion_train.jsonl`

Each line should be one JSON object with these fields:
- `text`
- `valence`
- `activation`
- `social_orientation`
- `stability`

Example:
```json
{"text":"I feel anxious and worried","valence":-0.7,"activation":"high","social_orientation":"reaching","stability":"fragile"}
```

Sources used:
- `dair-ai/emotion` parquet splits via `pd.read_parquet("hf://datasets/dair-ai/emotion/...")`
- `Alignment-Lab-AI/EmotionDialogue/conversations.jsonl` via `pd.read_json(..., lines=True)`

The prep script normalizes both datasets into the same training schema so the NLP model can train on a single unified JSONL file.
