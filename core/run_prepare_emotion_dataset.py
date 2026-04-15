from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC_PATH = ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from pipeline.stages.emotion_engine.dataset_prep import prepare_from_hf


def main() -> None:
    outputs = prepare_from_hf(Path("dataset"))
    print("Prepared datasets:")
    for name, path in outputs.items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
