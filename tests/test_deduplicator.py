"""Unit tests for StreamDeduplicator module."""

import unittest
from ann_data.deduplicator import StreamDeduplicator


class TestDeduplicator(unittest.TestCase):

    def setUp(self):
        self.dedup = StreamDeduplicator(threshold=0.8, num_perm=128)

    def test_identical_documents(self):
        doc1 = "Thuật toán HNSW cho phép tìm kiếm láng giềng gần đúng với tốc độ cao."
        doc2 = "Thuật toán HNSW cho phép tìm kiếm láng giềng gần đúng với tốc độ cao."
        
        self.assertFalse(self.dedup.is_duplicate("id1", doc1))
        self.assertTrue(self.dedup.is_duplicate("id2", doc2))

    def test_near_duplicates(self):
        # Only 1 minor word differs in a long sentence (~90% overlap)
        doc1 = "Thành viên nhóm nghiên cứu tiến hành thu thập và làm sạch mười triệu bản ghi văn bản tiếng Việt."
        doc2 = "Thành viên nhóm nghiên cứu tiến hành thu thập và làm sạch 10 triệu bản ghi văn bản tiếng Việt."
        
        self.assertFalse(self.dedup.is_duplicate("id1", doc1))
        self.assertTrue(self.dedup.is_duplicate("id2", doc2))

    def test_distinct_documents(self):
        doc1 = "Giá vàng thế giới hôm nay tăng vọt do biến động kinh tế toàn cầu."
        doc2 = "Đội tuyển bóng đá quốc gia giành chiến thắng kịch tính ở những phút cuối trận đấu."
        
        self.assertFalse(self.dedup.is_duplicate("id1", doc1))
        self.assertFalse(self.dedup.is_duplicate("id2", doc2))

    def test_stream_filter_and_stats(self):
        stream = [
            ("d1", "Nội dung bài báo số 1 về xử lý ngôn ngữ tự nhiên."),
            ("d2", "Nội dung bài báo số 1 về xử lý ngôn ngữ tự nhiên."),  # Dup
            ("d3", "Nội dung bài báo số 2 về trí tuệ nhân tạo thị giác."),
            ("d4", "Nội dung bài báo số 1 về xử lý ngôn ngữ tự nhiên."),  # Dup
        ]
        
        unique_results = list(self.dedup.filter_stream(stream))
        self.assertEqual(len(unique_results), 2)
        
        stats = self.dedup.stats
        self.assertEqual(stats["total_seen"], 4)
        self.assertEqual(stats["total_duplicates"], 2)
        self.assertEqual(stats["unique_kept"], 2)

    def test_reset(self):
        doc = "Văn bản mẫu để kiểm tra reset."
        self.assertFalse(self.dedup.is_duplicate("d1", doc))
        self.dedup.reset()
        self.assertEqual(self.dedup.stats["total_seen"], 0)
        self.assertFalse(self.dedup.is_duplicate("d1_again", doc))


if __name__ == "__main__":
    unittest.main()
