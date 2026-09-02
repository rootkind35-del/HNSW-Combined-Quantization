"""Bộ điều phối Pipeline xử lý dữ liệu lớn theo luồng (Streaming Data Pipeline) cho 10 triệu văn bản."""

import time
from typing import Any, Dict, Iterable, Optional, Tuple
from ann_data.cleaner import TextCleaner
from ann_data.config import PipelineConfig
from ann_data.deduplicator import StreamDeduplicator
from ann_data.embedder import BatchEmbedder, BaseEmbedder, SentenceTransformerEmbedder
from ann_data.storage import MemmapStorage
from ann_data.tokenizer import BaseTokenizer, PyViTokenizer
from ann_data.utils import get_logger


class DataPipeline:
    """
    Điều phối toàn diện chu trình xử lý dữ liệu từ đầu đến cuối (End-to-End Streaming Pipeline):
    1. Làm sạch ký tự rác, chuẩn hóa Unicode NFC và bóc tách HTML.
    2. Tách từ ghép tiếng Việt bằng PyVi.
    3. Lọc trùng lặp thời gian thực bằng MinHash LSH.
    4. Sinh vector đặc trưng 384 chiều bằng mô hình ngôn ngữ Transformer.
    5. Gom lô và ghi trực tiếp vào tệp nhị phân np.memmap 15.36 GB trên SSD.
    """

    def __init__(
        self,
        config: PipelineConfig,
        embedder: Optional[BaseEmbedder] = None,
        tokenizer: Optional[BaseTokenizer] = None,
    ):
        """
        Khởi tạo Pipeline xử lý dữ liệu.

        Tham số:
            config: Đối tượng cấu hình PipelineConfig.
            embedder: Mô hình sinh vector nhúng (tùy chọn, mặc định nạp SentenceTransformer).
            tokenizer: Bộ tách từ tiếng Việt (tùy chọn, mặc định PyViTokenizer).
        """
        self.config = config
        self.logger = get_logger("DataPipeline")
        
        # Các module thành phần con
        self.cleaner = TextCleaner(
            normalize_nfc=config.normalize_unicode_nfc,
            strip_html=config.strip_html_tags,
            remove_urls=config.remove_urls,
        )
        self.tokenizer = tokenizer or PyViTokenizer()
        self.deduplicator = StreamDeduplicator(
            threshold=config.minhash_threshold,
            num_perm=config.minhash_num_perm,
            lowercase=config.lowercase_tokens_for_dedup,
        )
        self.storage = MemmapStorage(
            file_path=config.output_memmap_path,
            max_records=config.max_records,
            dim=config.embedding_dim,
            dtype=config.dtype,
            mode="w+",
        )
        selected_embedder = embedder or SentenceTransformerEmbedder(
            model_name=config.model_name,
            dim=config.embedding_dim,
        )
        self.batch_embedder = BatchEmbedder(
            embedder=selected_embedder,
            storage=self.storage,
            batch_size=config.batch_size,
        )

    def process_item(self, doc_id: str, raw_text: str) -> Optional[str]:
        """
        Xử lý tiền xử lý, tách từ và kiểm tra khử trùng lặp cho một mẫu văn bản đơn lẻ.

        Tham số:
            doc_id: Mã định danh tài liệu.
            raw_text: Nội dung văn bản thô.

        Trả về:
            Chuỗi văn bản đã qua xử lý nếu hợp lệ và không trùng lặp, ngược lại trả về None.
        """
        cleaned = self.cleaner.clean(raw_text)
        if not cleaned:
            return None

        tokenized = self.tokenizer.tokenize(cleaned)
        if not tokenized:
            return None

        if self.deduplicator.is_duplicate(doc_id, tokenized):
            return None

        return tokenized

    def process_stream(
        self, stream: Iterable[Tuple[str, str]], log_interval: int = 10000
    ) -> Dict[str, Any]:
        """
        Xử lý một luồng liên tục các cặp (doc_id, text), nạp qua pipeline và ghi vector nhúng xuống đĩa SSD.

        Tham số:
            stream: Iterable sinh ra các tuple (doc_id, text).
            log_interval: Tần suất ghi nhật ký tiến độ (mặc định mỗi 10.000 tài liệu).

        Trả về:
            Dict chứa các chỉ số thống kê tổng kết tiến trình chạy.
        """
        start_time = time.perf_counter()
        total_input = 0
        total_valid = 0

        self.logger.info("Bắt đầu xử lý luồng dữ liệu...")

        for doc_id, text in stream:
            total_input += 1
            processed_text = self.process_item(doc_id, text)
            
            if processed_text is not None:
                total_valid += 1
                self.batch_embedder.add(processed_text)

            if total_input % log_interval == 0:
                self.logger.info(
                    "Đã xử lý %d tài liệu | Hợp lệ: %d | Trùng lặp: %d",
                    total_input,
                    total_valid,
                    self.deduplicator.total_duplicates,
                )

        # Xả toàn bộ các vector còn dư trong bộ đệm vào file lưu trữ
        self.batch_embedder.flush()
        elapsed = time.perf_counter() - start_time

        stats = {
            "total_input": total_input,
            "total_valid_embedded": total_valid,
            "total_duplicates": self.deduplicator.total_duplicates,
            "storage_written_records": self.storage.current_count,
            "output_path": self.config.output_memmap_path,
            "elapsed_seconds": round(elapsed, 4),
            "throughput_docs_per_sec": round(total_input / max(elapsed, 1e-6), 2),
        }
        self.logger.info("Pipeline hoàn tất: %s", stats)
        return stats

    def close(self) -> None:
        """Đóng toàn bộ các tài nguyên tệp tin đang mở."""
        self.batch_embedder.close()

    def __enter__(self) -> "DataPipeline":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

