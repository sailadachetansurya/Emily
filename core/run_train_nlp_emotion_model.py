from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC_PATH = ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from pipeline.stages.emotion_engine.train_nlp_emotion_model import train_from_jsonl


DATASET_PATH = Path("dataset") / "emotion_train.jsonl"
OUTPUT_PATH = Path("models") / "emotion_model.json"


def main() -> None:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Training dataset not found at {DATASET_PATH}. Place your JSONL file in the dataset folder with the name emotion_train.jsonl."
        )
    output_path = train_from_jsonl(DATASET_PATH, OUTPUT_PATH)
    print(f"Saved trained emotion model to {output_path}")


if __name__ == "__main__":
    main()
