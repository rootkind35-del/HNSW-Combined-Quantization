"""Unit tests for Vietnamese tokenizer module."""

import unittest
from ann_data.tokenizer import PyViTokenizer, WhitespaceTokenizer, segment_text


class TestTokenizer(unittest.TestCase):

    def setUp(self):
        self.pyvi_tokenizer = PyViTokenizer()
        self.ws_tokenizer = WhitespaceTokenizer()

    def test_pyvi_compound_words(self):
        sample = "Trí tuệ nhân tạo và học máy"
        segmented = self.pyvi_tokenizer.tokenize(sample)
        # Vietnamese compound words should be underscored
        self.assertIn("Trí_tuệ", segmented)
        self.assertIn("nhân_tạo", segmented)

    def test_tokenize_to_list(self):
        sample = "Công nghệ thông tin phát triển"
        tokens = self.pyvi_tokenizer.tokenize_to_list(sample)
        self.assertIsInstance(tokens, list)
        self.assertTrue(len(tokens) > 0)
        self.assertIn("Công_nghệ", tokens)

    def test_whitespace_fallback_tokenizer(self):
        sample = "Hệ thống tìm kiếm vector"
        tokens = self.ws_tokenizer.tokenize_to_list(sample)
        self.assertEqual(tokens, ["Hệ", "thống", "tìm", "kiếm", "vector"])

    def test_convenience_function(self):
        sample = "Đại học Bách Khoa"
        result = segment_text(sample)
        self.assertTrue(len(result) > 0)

    def test_empty_input(self):
        self.assertEqual(self.pyvi_tokenizer.tokenize(""), "")
        self.assertEqual(self.pyvi_tokenizer.tokenize(None), "")
        self.assertEqual(self.pyvi_tokenizer.tokenize_to_list(""), [])


if __name__ == "__main__":
    unittest.main()
