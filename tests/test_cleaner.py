"""Unit tests for TextCleaner module."""

import unittest
from ann_data.cleaner import TextCleaner, clean_text


class TestTextCleaner(unittest.TestCase):

    def setUp(self):
        self.cleaner = TextCleaner()

    def test_strip_html(self):
        raw = "<div><h1>Tiêu đề</h1><p>Nội dung có <a href='https://example.com'>liên kết</a>.</p></div>"
        cleaned = self.cleaner.clean_html(raw)
        self.assertNotIn("<div>", cleaned)
        self.assertNotIn("</a>", cleaned)
        self.assertIn("Tiêu đề", cleaned)
        self.assertIn("Nội dung có", cleaned)

    def test_unicode_nfc_normalization(self):
        # NFD representation of "Tiếng Việt"
        nfd_text = "Ti\u00ea\u0301ng Vi\u00ea\u0323t"
        normalized = self.cleaner.clean_unicode(nfd_text)
        expected = "Tiếng Việt"
        self.assertEqual(normalized, expected)

    def test_remove_urls(self):
        sample = "Tham khảo tại https://vnexpress.net hoặc www.dantri.com.vn để biết chi tiết."
        cleaned = self.cleaner.clean_urls(sample)
        self.assertNotIn("https://", cleaned)
        self.assertNotIn("www.dantri.com.vn", cleaned)
        self.assertIn("Tham khảo tại", cleaned)

    def test_normalize_whitespace(self):
        sample = "   Dòng 1 \t\t  Dòng 2   \n\n  Dòng 3   "
        cleaned = self.cleaner.normalize_whitespace(sample)
        self.assertEqual(cleaned, "Dòng 1 Dòng 2 Dòng 3")

    def test_full_clean_pipeline(self):
        raw = " <p>Xin chào! Truy cập http://test.vn để xem bản ghi 10.000.000 văn bản.</p> "
        result = self.cleaner.clean(raw)
        self.assertNotIn("<p>", result)
        self.assertNotIn("http://test.vn", result)
        self.assertIn("Xin chào!", result)
        self.assertIn("10.000.000", result)

    def test_empty_and_none_inputs(self):
        self.assertEqual(clean_text(""), "")
        self.assertEqual(clean_text(None), "")


if __name__ == "__main__":
    unittest.main()
