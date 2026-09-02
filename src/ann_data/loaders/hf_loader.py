"""Module nạp dữ liệu ngữ liệu lớn theo luồng trực tiếp từ Hugging Face Hub."""

from typing import Generator, Optional, Tuple
from ann_data.loaders.base import BaseDataLoader
from ann_data.utils import get_logger


class HuggingFaceLoader(BaseDataLoader):
    """
    Trình nạp dữ liệu văn bản theo luồng (streaming) từ các tập ngữ liệu tiếng Việt lớn trên Hugging Face.
    Cho phép đọc từng bản ghi qua mạng mà không cần tải toàn bộ hàng chục GB về ổ cứng trước.
    """

    def __init__(
        self,
        dataset_name: str = "fsnaix/vietnamese-corpus-large",
        config_name: Optional[str] = None,
        split: str = "train",
        text_column: str = "text",
        id_column: Optional[str] = None,
        streaming: bool = True,
    ):
        """
        Khởi tạo trình nạp dữ liệu Hugging Face.

        Tham số:
            dataset_name: Tên ngữ liệu trên Hugging Face Hub (mặc định fsnaix/vietnamese-corpus-large).
            config_name: Tên cấu hình tập con (subset) nếu có.
            split: Tập phân chia ('train', 'validation', 'test').
            text_column: Tên trường chứa nội dung văn bản.
            id_column: Tên trường chứa mã ID (nếu None sẽ tự sinh mã).
            streaming: Kích hoạt chế độ luồng (True) để tiết kiệm ổ đĩa và bộ nhớ.
        """
        self.dataset_name = dataset_name
        self.config_name = config_name
        self.split = split
        self.text_column = text_column
        self.id_column = id_column
        self.streaming = streaming
        self.logger = get_logger("HuggingFaceLoader")

    def _load_dataset_stream(self):
        """Khởi tạo đối tượng luồng dữ liệu từ thư viện datasets."""
        try:
            from datasets import load_dataset
            kwargs = {
                "path": self.dataset_name,
                "split": self.split,
                "streaming": self.streaming,
                "trust_remote_code": False,
            }
            if self.config_name:
                kwargs["name"] = self.config_name
                
            dataset = load_dataset(**kwargs)
            return dataset
        except Exception as e:
            self.logger.warning(
                "Không thể khởi tạo luồng Hugging Face cho '%s' (cấu hình: %s): %s",
                self.dataset_name,
                self.config_name,
                str(e),
            )
            return None

    def stream(self, limit: Optional[int] = None) -> Generator[Tuple[str, str], None, None]:
        """
        Sinh ra từng cặp (doc_id, text) từ luồng ngữ liệu tiếng Việt.

        Tham số:
            limit: Số lượng bản ghi tối đa cần nạp.

        Sinh ra:
            Tuple[str, str]: (doc_id, text)
        """
        dataset = self._load_dataset_stream()
        if dataset is None:
            self.logger.info("Luồng dữ liệu ngữ liệu không khả dụng hoặc mạng không phản hồi.")
            return

        yielded = 0
        for idx, item in enumerate(dataset):
            if not isinstance(item, dict):
                continue

            text = item.get(self.text_column, "")
            if not text or not isinstance(text, str):
                continue

            doc_id = (
                str(item.get(self.id_column))
                if self.id_column and self.id_column in item
                else f"hf_{self.split}_{idx:08d}"
            )

            yield doc_id, text
            yielded += 1

            if limit is not None and yielded >= limit:
                break

