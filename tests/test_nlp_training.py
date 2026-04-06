import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pipeline.stages.emotion_engine.train_nlp_emotion_model import EmotionModelTrainer, TrainedEmotionModel, train_from_jsonl


class EmotionTrainingTests(unittest.TestCase):
    def test_train_and_load_trained_model(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            data_path = Path(tmp_dir) / "emotion_data.jsonl"
            output_path = Path(tmp_dir) / "trained_emotion_model.json"
            rows = [
                {"text": "I feel worried and anxious", "valence": -0.7, "activation": "high", "social_orientation": "reaching", "stability": "fragile"},
                {"text": "I am lonely and sad", "valence": -0.8, "activation": "low", "social_orientation": "withdrawn", "stability": "fragile"},
                {"text": "I am excited and happy", "valence": 0.8, "activation": "high", "social_orientation": "reaching", "stability": "stable"},
            ]
            data_path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")

            saved_path = train_from_jsonl(data_path, output_path)
            self.assertTrue(saved_path.exists())

            model = TrainedEmotionModel.load(saved_path)
            emotion = model.classify("I feel anxious and worried about this")

            self.assertEqual(emotion.stability, "fragile")
            self.assertEqual(emotion.activation_level, "high")
            self.assertLess(emotion.emotional_valence, 0.0)

    def test_trainer_rejects_invalid_rows(self) -> None:
        trainer = EmotionModelTrainer()
        with self.assertRaises(Exception):
            trainer.parse_example({"text": "hello"}, line_number=1)


if __name__ == "__main__":
    unittest.main()
