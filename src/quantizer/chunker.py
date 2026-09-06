"""Bộ phân tách đoạn văn bản (Text Chunking) phục vụ tìm kiếm ngữ nghĩa chính xác."""

from typing import Dict, List


class TextChunker:
    """Chia nhỏ văn bản toàn văn dài thành các đoạn văn ngắn có độ dài cố định kèm vùng gối đầu (overlap)."""

    def __init__(self, chunk_size: int = 300, chunk_overlap: int = 50):
        """
        Tham số:
            chunk_size: Số lượng từ tối đa trong mỗi đoạn văn (chunk).
            chunk_overlap: Số lượng từ gối đầu giữa hai đoạn kế tiếp để giữ mạch ngữ cảnh.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(self, doc_id: str, title: str, full_text: str) -> List[Dict[str, any]]:
        """
        Phân tách một tài liệu toàn văn thành danh sách các đoạn (chunks).

        Tham số:
            doc_id: Định danh tài liệu gốc.
            title: Tiêu đề tài liệu.
            full_text: Toàn bộ nội dung bài viết.

        Trả về:
            Danh sách các dict chứa thông tin từng đoạn.
        """
        words = full_text.split()
        total_words = len(words)

        # Nếu bài viết ngắn hơn hoặc bằng kích thước một chunk, giữ nguyên 1 chunk duy nhất
        if total_words <= self.chunk_size:
            return [{
                "chunk_id": f"{doc_id}_c0",
                "doc_id": doc_id,
                "title": title,
                "chunk_index": 0,
                "text": full_text,
                "token_count": total_words,
            }]

        chunks = []
        step = max(self.chunk_size - self.chunk_overlap, 1)
        chunk_idx = 0

        for start_idx in range(0, total_words, step):
            end_idx = min(start_idx + self.chunk_size, total_words)
            chunk_words = words[start_idx:end_idx]
            
            # Nếu đoạn cuối quá ngắn so với chunk_size và đã có đoạn trước thì bỏ qua để tránh phân mảnh
            min_tail = max(3, self.chunk_size // 4)
            if len(chunk_words) < min_tail and chunks:
                break

            chunk_text = " ".join(chunk_words)
            chunks.append({
                "chunk_id": f"{doc_id}_c{chunk_idx}",
                "doc_id": doc_id,
                "title": title,
                "chunk_index": chunk_idx,
                "text": chunk_text,
                "token_count": len(chunk_words),
            })
            chunk_idx += 1

        return chunks
