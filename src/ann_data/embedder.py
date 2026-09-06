"""Module sinh vector đặc trưng ngữ nghĩa (Dense Embeddings) và quản lý ghi lô vào bộ nhớ SSD."""

from abc import ABC, abstractmethod
from typing import List, Optional
import numpy as np
from ann_data.storage import MemmapStorage
from ann_data.utils import get_logger


class BaseEmbedder(ABC):
    """Giao diện trừu tượng cho các mô hình sinh vector đặc trưng văn bản."""

    @abstractmethod
    def encode(self, texts: List[str], **kwargs) -> np.ndarray:
        """
        Mã hóa danh sách các chuỗi văn bản thành mảng vector numpy kích thước (len(texts), dim).

        Tham số:
            texts: Danh sách chuỗi văn bản đầu vào.
            **kwargs: Tham số bổ sung như batch_size.

        Trả về:
            Mảng numpy 2 chiều kiểu float32 chứa các vector nhúng.
        """
        pass

    @property
    @abstractmethod
    def dim(self) -> int:
        """Trả về số chiều không gian vector nhúng đặc trưng."""
        pass


class MockEmbedder(BaseEmbedder):
    """Bộ sinh vector ngẫu nhiên giả lập phục vụ kiểm thử đơn vị nhanh và kiểm định luồng I/O mà không cần GPU/mạng."""

    def __init__(self, dim: int = 384, seed: Optional[int] = 42):
        """
        Khởi tạo MockEmbedder với seed cố định để đảm bảo tính tái lập.

        Tham số:
            dim: Số chiều không gian vector (mặc định 384 chiều theo chuẩn MiniLM).
            seed: Giá trị hạt giống ngẫu nhiên.
        """
        self._dim = dim
        self._rng = np.random.RandomState(seed)

    @property
    def dim(self) -> int:
        return self._dim

    def encode(self, texts: List[str], **kwargs) -> np.ndarray:
        """Sinh các vector chuẩn hóa độ dài đơn vị L2 một cách nhanh chóng."""
        count = len(texts)
        if count == 0:
            return np.empty((0, self._dim), dtype=np.float32)
        # Sinh mảng float32 chuẩn hóa theo phân phối chuẩn
        vectors = self._rng.randn(count, self._dim).astype(np.float32)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        return vectors / np.maximum(norms, 1e-12)


class SentenceTransformerEmbedder(BaseEmbedder):
    """Mô hình nhúng ngữ nghĩa mạng nơ-ron sâu sử dụng thư viện sentence-transformers."""

    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2", dim: int = 384):
        """
        Khởi tạo mô hình Transformer đa ngôn ngữ hỗ trợ tiếng Việt.

        Tham số:
            model_name: Tên mô hình trên Hugging Face.
            dim: Số chiều vector đầu ra của mô hình (MiniLM là 384).
        """
        self.model_name = model_name
        self._dim = dim
        self._logger = get_logger("SentenceTransformerEmbedder")
        self._model = None
        self._fallback_mock: Optional[MockEmbedder] = None
        self._init_model()

    def _init_model(self) -> None:
        """Nạp mô hình Transformer với cơ chế tự động chuyển sang MockEmbedder nếu môi trường thiếu thư viện/mạng."""
        try:
            from sentence_transformers import SentenceTransformer
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self._model = SentenceTransformer(self.model_name, device=device)
        except Exception as e:
            self._logger.warning(
                "Không thể nạp sentence_transformers (%s). Tự động kích hoạt cơ chế dự phòng MockEmbedder.",
                str(e)
            )
            self._fallback_mock = MockEmbedder(dim=self._dim)

    @property
    def dim(self) -> int:
        return self._dim

    def encode(self, texts: List[str], batch_size: int = 512) -> np.ndarray:
        """
        Mã hóa ngữ nghĩa danh sách văn bản thành các dense vector 384 chiều.

        Tham số:
            texts: Danh sách chuỗi văn bản cần nhúng.
            batch_size: Kích thước lô xử lý trên GPU (mặc định 512).

        Trả về:
            Mảng numpy float32 chứa các vector nhúng ngữ nghĩa.
        """
        if not texts:
            return np.empty((0, self._dim), dtype=np.float32)

        if self._model is not None:
            embeddings = self._model.encode(
                texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=False,
            )
            return embeddings.astype(np.float32)
        elif self._fallback_mock is not None:
            return self._fallback_mock.encode(texts)
        else:
            raise RuntimeError("Không có backend sinh vector nào khả dụng.")


class BatchEmbedder:
    """Bộ điều phối nạp lô và ghi trực tiếp vector nhúng vào tệp nhị phân MemmapStorage trên đĩa SSD."""

    def __init__(self, embedder: BaseEmbedder, storage: MemmapStorage, batch_size: int = 64):
        """
        Khởi tạo bộ gom lô vector.

        Tham số:
            embedder: Đối tượng mô hình sinh vector.
            storage: Đối tượng bộ lưu trữ đĩa MemmapStorage.
            batch_size: Kích thước lô trước khi xả ghi vào tệp (mặc định 64).
        """
        self.embedder = embedder
        self.storage = storage
        self.batch_size = batch_size
        self.buffer: List[str] = []

    def add(self, text: str) -> Optional[int]:
        """
        Thêm một mẫu văn bản vào bộ nhớ đệm. Nếu bộ đệm đầy kích thước batch_size, tự động xả ghi vào đĩa.

        Tham số:
            text: Nội dung văn bản cần nhúng.

        Trả về:
            Số lượng bản ghi vừa được ghi nếu có xả bộ đệm, ngược lại trả về None.
        """
        self.buffer.append(text)
        if len(self.buffer) >= self.batch_size:
            return self.flush()
        return None

    def flush(self) -> int:
        """Mã hóa toàn bộ văn bản trong bộ đệm và ghi nối tiếp vào tệp memmap trên đĩa."""
        if not self.buffer:
            return 0

        vectors = self.embedder.encode(self.buffer)
        num_records = len(vectors)
        self.storage.append_batch(vectors)
        self.buffer.clear()
        return num_records

    def close(self) -> None:
        """Xả toàn bộ các mục còn lại trong bộ đệm và đóng file lưu trữ."""
        self.flush()
        self.storage.close()

    def __enter__(self) -> "BatchEmbedder":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

