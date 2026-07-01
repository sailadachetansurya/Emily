from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

DAIR_AI_SPLITS = {
    "train": "split/train-00000-of-00001.parquet",
    "validation": "split/validation-00000-of-00001.parquet",
    "test": "split/test-00000-of-00001.parquet",
}

DAIR_AI_LABELS = {
    0: "sadness",
    1: "joy",
    2: "love",
    3: "anger",
    4: "fear",
    5: "surprise",
}

EMOTION_STATE_MAP = {
    "anger": {"valence": -0.7, "activation": "high", "social_orientation": "reaching", "stability": "volatile"},
    "fear": {"valence": -0.8, "activation": "high", "social_orientation": "withdrawn", "stability": "fragile"},
    "sadness": {"valence": -0.8, "activation": "low", "social_orientation": "withdrawn", "stability": "fragile"},
    "joy": {"valence": 0.85, "activation": "high", "social_orientation": "reaching", "stability": "stable"},
    "love": {"valence": 0.7, "activation": "medium", "social_orientation": "reaching", "stability": "stable"},
    "surprise": {"valence": 0.05, "activation": "high", "social_orientation": "neutral", "stability": "volatile"},
    "neutral": {"valence": 0.0, "activation": "medium", "social_orientation": "neutral", "stability": "stable"},
}

EMOTION_SYNONYMS = {
    "angry": "anger", "frustrated": "anger", "frustration": "anger",
    "annoyed": "anger", "furious": "anger", "jealous": "anger", "disgusted": "anger",
    "afraid": "fear", "fearful": "fear", "scared": "fear",
    "terrified": "fear", "anxious": "fear", "apprehensive": "fear",
    "happy": "joy", "happiness": "joy", "glad": "joy",
    "excited": "joy", "proud": "joy", "grateful": "joy", "confident": "joy",
    "joyful": "joy", "hopeful": "joy", "impressed": "joy",
    "content": "joy", "caring": "joy", "trusting": "joy", "faithful": "joy",
    "loving": "love",
    "sad": "sadness", "depressed": "sadness", "lonely": "sadness",
    "disappointed": "sadness", "guilty": "sadness", "nostalgic": "sadness",
    "embarrassed": "sadness", "devastated": "sadness", "sentimental": "sadness",
    "ashamed": "sadness",
    "surprised": "surprise",
    "neutral": "neutral", "prepared": "neutral", "anticipating": "neutral",
}

TEXT_KEYS = ["text", "utterance", "message", "content", "prompt", "response", "reply", "dialogue", "conversation", "conversations"]
LABEL_KEYS = ["emotion", "label", "labels", "emotion_label", "emotion_labels", "sentiment"]


@dataclass(frozen=True)
class PreparedSplit:
    name: str
    dataframe: pd.DataFrame
    source_count: int
    kept_count: int
    skipped_count: int


class DatasetPrepError(Exception):
    pass


def prepare_from_hf(output_dir: str | Path = "dataset") -> dict[str, Path]:
    base_dir = Path(output_dir)
    processed_dir = base_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    prepared_outputs: dict[str, Path] = {}

    dair_train = normalize_dair_ai_frame(
        pd.read_parquet(f"hf://datasets/dair-ai/emotion/{DAIR_AI_SPLITS['train']}"),
        split_name="train",
        source_name="dair-ai/emotion",
    )
    dair_validation = normalize_dair_ai_frame(
        pd.read_parquet(f"hf://datasets/dair-ai/emotion/{DAIR_AI_SPLITS['validation']}"),
        split_name="validation",
        source_name="dair-ai/emotion",
    )
    dair_test = normalize_dair_ai_frame(
        pd.read_parquet(f"hf://datasets/dair-ai/emotion/{DAIR_AI_SPLITS['test']}"),
        split_name="test",
        source_name="dair-ai/emotion",
    )
    dialogue = normalize_emotion_dialogue_frame(
        pd.read_json("hf://datasets/Alignment-Lab-AI/EmotionDialogue/conversations.jsonl", lines=True),
        split_name="train",
        source_name="Alignment-Lab-AI/EmotionDialogue",
    )

    prepared_outputs["processed/dair_ai_train.jsonl"] = write_jsonl(dair_train.dataframe, processed_dir / "dair_ai_train.jsonl")
    prepared_outputs["processed/dair_ai_validation.jsonl"] = write_jsonl(dair_validation.dataframe, processed_dir / "dair_ai_validation.jsonl")
    prepared_outputs["processed/dair_ai_test.jsonl"] = write_jsonl(dair_test.dataframe, processed_dir / "dair_ai_test.jsonl")
    prepared_outputs["processed/emotion_dialogue.jsonl"] = write_jsonl(dialogue.dataframe, processed_dir / "emotion_dialogue.jsonl")

    train_df = pd.concat([dair_train.dataframe, dialogue.dataframe], ignore_index=True)
    validation_df = dair_validation.dataframe.copy()
    test_df = dair_test.dataframe.copy()

    prepared_outputs["emotion_train.jsonl"] = write_jsonl(train_df, base_dir / "emotion_train.jsonl")
    prepared_outputs["emotion_validation.jsonl"] = write_jsonl(validation_df, base_dir / "emotion_validation.jsonl")
    prepared_outputs["emotion_test.jsonl"] = write_jsonl(test_df, base_dir / "emotion_test.jsonl")

    summary = {
        "sources": {
            "dair-ai/emotion": {
                "train_rows": dair_train.kept_count,
                "validation_rows": dair_validation.kept_count,
                "test_rows": dair_test.kept_count,
            },
            "Alignment-Lab-AI/EmotionDialogue": {
                "train_rows": dialogue.kept_count,
            },
        },
        "outputs": {name: str(path) for name, path in prepared_outputs.items()},
    }
    (base_dir / "dataset_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return prepared_outputs


def normalize_dair_ai_frame(frame: pd.DataFrame, split_name: str, source_name: str) -> PreparedSplit:
    if "text" not in frame.columns or "label" not in frame.columns:
        raise DatasetPrepError(f"{source_name} {split_name} must contain 'text' and 'label' columns.")

    records: list[dict[str, Any]] = []
    skipped = 0
    for _, row in frame.iterrows():
        text = safe_string(row.get("text"))
        label_name = normalize_emotion_label(row.get("label"))
        if not text or not label_name:
            skipped += 1
            continue
        records.append(build_prepared_record(text=text, label_name=label_name, split_name=split_name, source_name=source_name))

    dataframe = pd.DataFrame(records)
    return PreparedSplit(name=split_name, dataframe=dataframe, source_count=len(frame), kept_count=len(dataframe), skipped_count=skipped)


def normalize_emotion_dialogue_frame(frame: pd.DataFrame, split_name: str, source_name: str) -> PreparedSplit:
    records: list[dict[str, Any]] = []
    skipped = 0
    for _, row in frame.iterrows():
        row_dict = row.to_dict()
        label_name = extract_label(row_dict)
        text = extract_text(row_dict)

        if not label_name and "conversations" in row_dict:
            convs = row_dict["conversations"]
            if isinstance(convs, list) and convs:
                system_msg = convs[0]
                if isinstance(system_msg, dict) and system_msg.get("from") == "system":
                    sys_val = str(system_msg.get("value", ""))
                    if ":" in sys_val:
                        potential_label = sys_val.split(":", 1)[0].strip().lower()
                        resolved = EMOTION_SYNONYMS.get(potential_label, potential_label)
                        if resolved in EMOTION_STATE_MAP:
                            label_name = resolved

        if not text and "conversations" in row_dict:
            convs = row_dict["conversations"]
            if isinstance(convs, list):
                user_parts = []
                for msg in convs:
                    if isinstance(msg, dict) and msg.get("from") in ("human", "user"):
                        val = str(msg.get("value", "")).strip()
                        if val:
                            user_parts.append(val)
                if user_parts:
                    text = " ".join(user_parts[:3])

        if text and ":" in text:
            prefix = text.split(":", 1)[0].strip().lower()
            resolved_prefix = EMOTION_SYNONYMS.get(prefix, prefix)
            if resolved_prefix in EMOTION_STATE_MAP and len(prefix) < 20:
                text = text.split(":", 1)[1].strip()

        if not text or not label_name:
            skipped += 1
            continue
        records.append(build_prepared_record(text=text, label_name=label_name, split_name=split_name, source_name=source_name))

    dataframe = pd.DataFrame(records)
    return PreparedSplit(name=split_name, dataframe=dataframe, source_count=len(frame), kept_count=len(dataframe), skipped_count=skipped)


def build_prepared_record(text: str, label_name: str, split_name: str, source_name: str) -> dict[str, Any]:
    state = EMOTION_STATE_MAP.get(label_name, EMOTION_STATE_MAP["neutral"])
    return {
        "text": text,
        "emotion_label": label_name,
        "valence": state["valence"],
        "activation": state["activation"],
        "social_orientation": state["social_orientation"],
        "stability": state["stability"],
        "source": source_name,
        "split": split_name,
    }


def normalize_emotion_label(value: Any) -> str | None:
    if is_missing_value(value):
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if int(value) in DAIR_AI_LABELS:
            return DAIR_AI_LABELS[int(value)]
        return None
    if isinstance(value, list):
        for item in value:
            normalized = normalize_emotion_label(item)
            if normalized:
                return normalized
        return None
    if isinstance(value, dict):
        for key in LABEL_KEYS + TEXT_KEYS:
            if key in value:
                normalized = normalize_emotion_label(value[key])
                if normalized:
                    return normalized
        for nested in value.values():
            normalized = normalize_emotion_label(nested)
            if normalized:
                return normalized
        return None
    label = str(value).strip().lower()
    if not label:
        return None
    label = EMOTION_SYNONYMS.get(label, label)
    if label in EMOTION_STATE_MAP:
        return label
    if label in {"positive", "neg", "negative"}:
        return "joy" if label == "positive" else "sadness"
    return None


def extract_label(value: dict[str, Any]) -> str | None:
    for key in LABEL_KEYS:
        if key in value:
            label = normalize_emotion_label(value[key])
            if label:
                return label
    return None


def extract_text(value: dict[str, Any]) -> str | None:
    for key in TEXT_KEYS:
        if key in value:
            text = flatten_text(value[key])
            if text:
                return text
    for nested in value.values():
        text = flatten_text(nested)
        if text:
            return text
    return None


def flatten_text(value: Any) -> str | None:
    fragments: list[str] = []
    collect_text_fragments(value, fragments)
    text = " ".join(fragment.strip() for fragment in fragments if fragment and fragment.strip())
    return text or None


def collect_text_fragments(value: Any, fragments: list[str]) -> None:
    if is_missing_value(value):
        return
    if isinstance(value, str):
        if value.strip():
            fragments.append(value)
        return
    if isinstance(value, dict):
        preferred_keys = ["text", "utterance", "message", "content", "value", "prompt", "response", "reply"]
        if any(key in value for key in preferred_keys):
            for key in preferred_keys:
                if key in value:
                    collect_text_fragments(value[key], fragments)
            return
        for nested_key, nested_value in value.items():
            if nested_key in {"emotion", "label", "labels", "sentiment"}:
                continue
            collect_text_fragments(nested_value, fragments)
        return
    if isinstance(value, list):
        for item in value:
            collect_text_fragments(item, fragments)
        return
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return
    text = str(value).strip()
    if text:
        fragments.append(text)


def safe_string(value: Any) -> str | None:
    if is_missing_value(value):
        return None
    text = str(value).strip()
    return text or None


def is_missing_value(value: Any) -> bool:
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except Exception:
        return False


def write_jsonl(frame: pd.DataFrame, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_json(path, orient="records", lines=True, force_ascii=False)
    return path
