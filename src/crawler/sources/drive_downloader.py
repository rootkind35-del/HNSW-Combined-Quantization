"""Trình tải tệp dung lượng lớn từ Google Drive hỗ trợ vượt qua xác nhận virus và tải dạng luồng (chunked stream)."""

import os
import re
import sys
import time
import urllib.parse
import urllib.request
from typing import Optional
from ann_data.utils import get_logger

logger = get_logger("crawler.drive_downloader")


class GoogleDriveDownloader:
    """Tải tệp lớn từ Google Drive an toàn và ghi trực tiếp xuống ổ cứng."""

    @staticmethod
    def extract_file_id(url_or_id: str) -> str:
        """Trích xuất Google Drive File ID từ URL hoặc trả về ID nếu đã ở dạng ID."""
        if "/" in url_or_id:
            match = re.search(r"/(?:file/d/|id=)([a-zA-Z0-9_-]+)", url_or_id)
            if match:
                return match.group(1)
        return url_or_id

    @classmethod
    def download_file(
        cls,
        file_id_or_url: str,
        output_path: str,
        chunk_size: int = 10 * 1024 * 1024,  # 10 MB chunks
    ) -> bool:
        """
        Tải tệp từ Google Drive và ghi trực tiếp xuống đĩa.

        Tham số:
            file_id_or_url: File ID hoặc liên kết chia sẻ Google Drive.
            output_path: Đường dẫn tệp đích cần lưu trên đĩa.
            chunk_size: Kích thước từng khối đệm khi ghi đĩa.

        Trả về:
            True nếu tải thành công, False nếu thất bại.
        """
        file_id = cls.extract_file_id(file_id_or_url)
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36"
        base_url = f"https://drive.usercontent.google.com/download?id={file_id}&export=download"

        logger.info("Đang kiểm tra tệp Google Drive (ID: %s)...", file_id)

        req = urllib.request.Request(base_url, headers={"User-Agent": user_agent})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                content_type = resp.headers.get("Content-Type", "")
                
                # Nếu Google trả về trang cảnh báo virus (HTML) đối với tệp lớn
                if "text/html" in content_type:
                    html = resp.read().decode("utf-8", errors="replace")
                    
                    # Tìm form xác nhận tải tệp
                    confirm_match = re.search(r'name="confirm"\s+value="([^"]+)"', html)
                    uuid_match = re.search(r'name="uuid"\s+value="([^"]+)"', html)
                    
                    confirm_token = confirm_match.group(1) if confirm_match else "t"
                    uuid_token = uuid_match.group(1) if uuid_match else ""
                    
                    params = {
                        "id": file_id,
                        "export": "download",
                        "confirm": confirm_token,
                    }
                    if uuid_token:
                        params["uuid"] = uuid_token
                        
                    download_url = f"https://drive.usercontent.google.com/download?{urllib.parse.urlencode(params)}"
                    logger.info("Phát hiện tệp lớn. Vượt qua cảnh báo kiểm tra virus...")
                else:
                    download_url = base_url

            # Tiến hành tải luồng tệp nhị phân
            logger.info("Bắt đầu tải dữ liệu vào: %s", output_path)
            req_dl = urllib.request.Request(download_url, headers={"User-Agent": user_agent})
            
            with urllib.request.urlopen(req_dl, timeout=30) as dl_resp, open(output_path, "wb") as out_f:
                total_bytes_str = dl_resp.headers.get("Content-Length")
                total_bytes = int(total_bytes_str) if total_bytes_str else 0
                downloaded = 0
                start_time = time.perf_counter()
                last_log = start_time

                while True:
                    chunk = dl_resp.read(chunk_size)
                    if not chunk:
                        break
                    out_f.write(chunk)
                    downloaded += len(chunk)
                    
                    now = time.perf_counter()
                    if now - last_log >= 5.0:  # Ghi log mỗi 5 giây
                        speed_mb = (downloaded / (1024 * 1024)) / max(now - start_time, 0.001)
                        if total_bytes > 0:
                            pct = (downloaded / total_bytes) * 100.0
                            logger.info("Tiến độ: %.1f%% (%.2f / %.2f GB) - Tốc độ: %.1f MB/s", pct, downloaded / (1024**3), total_bytes / (1024**3), speed_mb)
                        else:
                            logger.info("Đã tải: %.2f GB - Tốc độ: %.1f MB/s", downloaded / (1024**3), speed_mb)
                        last_log = now

            elapsed = time.perf_counter() - start_time
            file_size_gb = os.path.getsize(output_path) / (1024**3)
            logger.info("Hoàn tất tải tệp sau %.1f giây. Kích thước trên đĩa: %.2f GB (%s)", elapsed, file_size_gb, output_path)
            return True

        except Exception as e:
            logger.error("Lỗi tải tệp từ Google Drive: %s", str(e))
            return False
