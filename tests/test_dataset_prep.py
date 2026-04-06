import unittest

import pandas as pd

from pipeline.stages.emotion_engine.dataset_prep import (
    normalize_dair_ai_frame,
    normalize_emotion_dialogue_frame,
)


class DatasetPrepTests(unittest.TestCase):
    def test_normalize_dair_ai_frame_maps_labels(self) -> None:
        frame = pd.DataFrame(
            [
                {"text": "I feel sad", "label": 0},
                {"text": "I feel happy", "label": 1},
            ]
        )

        prepared = normalize_dair_ai_frame(frame, split_name="train", source_name="dair-ai/emotion")

        self.assertEqual(prepared.kept_count, 2)
        self.assertEqual(prepared.dataframe.iloc[0]["emotion_label"], "sadness")
        self.assertEqual(prepared.dataframe.iloc[1]["emotion_label"], "joy")
        self.assertIn("valence", prepared.dataframe.columns)

    def test_normalize_emotion_dialogue_frame_extracts_nested_text_and_label(self) -> None:
        frame = pd.DataFrame(
            [
                {
                    "conversations": [
                        {"from": "human", "value": "I feel anxious and worried"},
                        {"from": "assistant", "value": "I am listening"},
                    ],
                    "emotion": "fear",
                },
                {
                    "conversation": {
                        "turns": [
                            {"speaker": "user", "text": "I am so happy today!"},
                            {"speaker": "assistant", "text": "That is wonderful"},
                        ]
                    },
                    "label": "joy",
                },
            ]
        )

        prepared = normalize_emotion_dialogue_frame(frame, split_name="train", source_name="Alignment-Lab-AI/EmotionDialogue")

        self.assertEqual(prepared.kept_count, 2)
        self.assertIn("anxious", prepared.dataframe.iloc[0]["text"])
        self.assertEqual(prepared.dataframe.iloc[0]["emotion_label"], "fear")
        self.assertEqual(prepared.dataframe.iloc[1]["emotion_label"], "joy")
        self.assertTrue((prepared.dataframe["source"] == "Alignment-Lab-AI/EmotionDialogue").all())


if __name__ == "__main__":
    unittest.main()
