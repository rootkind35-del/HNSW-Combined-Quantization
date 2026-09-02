"""Unit tests for HuggingFaceLoader module."""

import unittest
from unittest.mock import patch
from ann_data.loaders.hf_loader import HuggingFaceLoader


class TestHuggingFaceLoader(unittest.TestCase):

    def setUp(self):
        self.loader = HuggingFaceLoader(
            dataset_name="fsnaix/vietnamese-corpus-large",
            split="train",
            text_column="text",
        )

    def test_offline_fallback(self):
        with patch.object(self.loader, "_load_dataset_stream", return_value=None):
            items = list(self.loader.stream(limit=5))
            self.assertEqual(items, [])

    def test_streaming_with_mock_dataset(self):
        mock_data = [
            {"text": "Bản ghi tiếng Việt thứ nhất trên Hugging Face."},
            {"text": "Bản ghi tiếng Việt thứ hai về tìm kiếm vector."},
            {"text": "Bản ghi tiếng Việt thứ ba về mô hình ngôn ngữ."},
            {"text": ""},  # Empty, should be skipped
            {"invalid_col": "Không có cột text"},  # Missing text column
        ]

        with patch.object(self.loader, "_load_dataset_stream", return_value=iter(mock_data)):
            results = list(self.loader.stream(limit=2))
            self.assertEqual(len(results), 2)
            doc_id, text = results[0]
            self.assertTrue(doc_id.startswith("hf_train_"))
            self.assertIn("Bản ghi tiếng Việt thứ nhất", text)

    def test_custom_id_column(self):
        loader_with_id = HuggingFaceLoader(
            dataset_name="test-corpus",
            id_column="custom_id",
            text_column="content",
        )
        mock_data = [
            {"custom_id": "doc_999", "content": "Nội dung kiểm tra custom ID."},
        ]
        with patch.object(loader_with_id, "_load_dataset_stream", return_value=iter(mock_data)):
            results = list(loader_with_id.stream())
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0][0], "doc_999")
            self.assertEqual(results[0][1], "Nội dung kiểm tra custom ID.")


if __name__ == "__main__":
    unittest.main()
