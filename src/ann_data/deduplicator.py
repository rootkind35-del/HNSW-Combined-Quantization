"""Module lọc trùng lặp dữ liệu lớn bằng giải thuật MinHash và Locality Sensitive Hashing (LSH)."""

from typing import Dict, Generator, Iterable, List, Optional, Tuple
from datasketch import MinHash, MinHashLSH


class StreamDeduplicator:
    """
    Bộ lọc trùng lặp văn bản thời gian thực dạng luồng (Streaming Deduplicator):
    Sử dụng dấu vân tay MinHash kết hợp cấu trúc băm cục bộ LSH để phát hiện và loại bỏ
    các tài liệu trùng lặp hoàn toàn hoặc gần trùng lặp (Near-Duplicates) dựa trên độ tương đồng Jaccard.
    """

    def __init__(
        self,
        threshold: float = 0.8,
        num_perm: int = 128,
        lowercase: bool = True,
        shingle_size: int = 1,
    ):
        """
        Khởi tạo bộ lọc trùng lặp.

        Tham số:
            threshold: Ngưỡng tương đồng Jaccard để coi 2 văn bản là trùng lặp (mặc định 0.8 tức 80%).
            num_perm: Số lượng hàm băm hoán vị MinHash (càng cao độ phân giải càng chính xác).
            lowercase: Nếu True, chuyển chữ thường trước khi tạo shingle.
            shingle_size: Kích thước cụm từ ghép N-gram shingles (mặc định 1 tức từng từ).
        """
        self.threshold = threshold
        self.num_perm = num_perm
        self.lowercase = lowercase
        self.shingle_size = shingle_size
        
        self.lsh = MinHashLSH(threshold=self.threshold, num_perm=self.num_perm)
        self.total_seen = 0
        self.total_duplicates = 0

    def _extract_shingles(self, text: str) -> List[str]:
        """Trích xuất danh sách các cụm từ N-gram (shingles) từ chuỗi văn bản đầu vào."""
        normalized = text.lower() if self.lowercase else text
        tokens = normalized.split()
        if not tokens:
            return []
        if self.shingle_size <= 1:
            return tokens
        
        shingles = []
        for i in range(len(tokens) - self.shingle_size + 1):
            shingles.append(" ".join(tokens[i : i + self.shingle_size]))
        return shingles or tokens

    def compute_minhash(self, text: str) -> MinHash:
        """
        Tính toán dấu vân tay MinHash đại diện cho tập hợp shingles của văn bản.

        Tham số:
            text: Chuỗi nội dung văn bản.

        Trả về:
            Đối tượng MinHash chứa chữ ký băm 128 chiều.
        """
        minhash = MinHash(num_perm=self.num_perm)
        shingles = self._extract_shingles(text)
        for s in shingles:
            minhash.update(s.encode("utf-8"))
        return minhash

    def is_duplicate(self, doc_id: str, text: str) -> bool:
        """
        Kiểm tra văn bản có bị trùng lặp với các văn bản đã xuất hiện trước đó hay không.
        - Nếu trùng lặp: Trả về True và tăng bộ đếm trùng lặp.
        - Nếu duy nhất: Đưa vào chỉ mục băm LSH và trả về False.

        Tham số:
            doc_id: Mã định danh tài liệu.
            text: Chuỗi nội dung văn bản.

        Trả về:
            bool: True nếu phát hiện trùng lặp, False nếu là văn bản duy nhất.
        """
        self.total_seen += 1
        
        # Ngăn chặn tràn bộ nhớ (OOM) khi xử lý 10 triệu bản ghi
        # bằng cách làm mới chỉ mục băm LSH theo từng khối cửa sổ trượt 50.000 tài liệu
        if self.total_seen % 50000 == 0:
            self.lsh = MinHashLSH(threshold=self.threshold, num_perm=self.num_perm)
            
        minhash = self.compute_minhash(text)
        candidates = self.lsh.query(minhash)
        
        if candidates:
            self.total_duplicates += 1
            return True
            
        self.lsh.insert(doc_id, minhash)
        return False

    def filter_stream(
        self, stream: Iterable[Tuple[str, str]]
    ) -> Generator[Tuple[str, str], None, None]:
        """
        Bộ lọc luồng (Generator): Nhận luồng cặp (doc_id, text) và chỉ sinh ra các cặp văn bản không bị trùng.

        Tham số:
            stream: Luồng đầu vào chứa các cặp (doc_id, text).

        Sinh ra:
            Từng cặp (doc_id, text) duy nhất.
        """
        for doc_id, text in stream:
            if not self.is_duplicate(doc_id, text):
                yield doc_id, text

    @property
    def stats(self) -> Dict[str, int]:
        """Trả về từ điển thống kê số lượng văn bản đã xử lý, số trùng lặp và số duy nhất giữ lại."""
        return {
            "total_seen": self.total_seen,
            "total_duplicates": self.total_duplicates,
            "unique_kept": self.total_seen - self.total_duplicates,
        }

    def reset(self) -> None:
        """Xóa trắng chỉ mục LSH và đặt lại các biến thống kê đếm về 0."""
        self.lsh = MinHashLSH(threshold=self.threshold, num_perm=self.num_perm)
        self.total_seen = 0
        self.total_duplicates = 0

