"""Pipeline điều phối thu thập và gom ngữ liệu toàn văn quy mô lớn."""

import json
import os
import time
from typing import Any, Dict, List, Optional
from crawler.config import CrawlerConfig
from crawler.sources.drive_downloader import GoogleDriveDownloader
from crawler.sources.hf_streamer import HuggingFaceStreamer
from crawler.sources.legal_crawler import LegalCrawler
from crawler.sources.rss_crawler import RssNewsCrawler
from crawler.storage.shard_writer import ShardWriter
from ann_data.utils import get_logger

logger = get_logger("crawler.pipeline")


class CrawlerPipeline:
    """Điều phối thu thập dữ liệu từ nhiều nguồn khác nhau và ghi vào data/crawl/."""

    def __init__(self, config: Optional[CrawlerConfig] = None):
        self.config = config or CrawlerConfig()

    def run_rss_crawl(self, limit: Optional[int] = 100) -> Dict[str, Any]:
        """Thu thập tin tức trực tiếp từ các kênh RSS báo chí Việt Nam."""
        logger.info("=== BẮT ĐẦU CÀO TIN TỨC BÁO ĐIỆN TỬ (CHỈ TIÊU: %s BÀI) ===", limit)
        crawler = RssNewsCrawler(self.config)

        start_time = time.perf_counter()
        count = 0

        with ShardWriter(output_dir=self.config.output_dir, shard_size=self.config.shard_size) as writer:
            for record in crawler.stream(limit=limit):
                writer.write(record)
                count += 1
                if count % 25 == 0:
                    logger.info("Đã lưu %d bài viết toàn văn vào shard...", count)

        elapsed = time.perf_counter() - start_time
        logger.info("Hoàn tất thu thập RSS: %d bài viết trong %.2f giây.", count, elapsed)
        return {"records_added": count, "elapsed_sec": round(elapsed, 2)}

    def run_legal_crawl(self, limit: Optional[int] = 400000) -> Dict[str, Any]:
        """Thu thập văn bản quy phạm pháp luật, chính sách và án lệ Việt Nam."""
        logger.info("=== BẮT ĐẦU THU THẬP VĂN BẢN PHÁP LUẬT VIỆT NAM (CHỈ TIÊU: %s BẢN GHI) ===", limit)
        crawler = LegalCrawler(self.config)

        start_time = time.perf_counter()
        count = 0

        with ShardWriter(output_dir=self.config.output_dir, shard_size=self.config.shard_size) as writer:
            for record in crawler.stream(limit=limit):
                writer.write(record)
                count += 1
                if count % 5000 == 0:
                    logger.info("Đã lưu %d văn bản pháp luật vào shard...", count)

        elapsed = time.perf_counter() - start_time
        logger.info("Hoàn tất thu thập pháp luật: %d văn bản trong %.2f giây.", count, elapsed)
        return {"records_added": count, "elapsed_sec": round(elapsed, 2)}

    def run_hf_streaming(self, limit: Optional[int] = 50000) -> Dict[str, Any]:
        """Nạp luồng văn bản từ các kho dữ liệu mở Hugging Face."""
        logger.info("=== BẮT ĐẦU NẠP LUỒNG NGỮ LIỆU HUGGING FACE (CHỈ TIÊU: %s BẢN GHI) ===", limit)
        streamer = HuggingFaceStreamer()

        start_time = time.perf_counter()
        count = 0

        with ShardWriter(output_dir=self.config.output_dir, shard_size=self.config.shard_size) as writer:
            for record in streamer.stream(limit=limit):
                writer.write(record)
                count += 1
                if count % 5000 == 0:
                    logger.info("Đã lưu %d bản ghi toàn văn vào shard...", count)

        elapsed = time.perf_counter() - start_time
        logger.info("Hoàn tất nạp luồng Hugging Face: %d bản ghi trong %.2f giây.", count, elapsed)
        return {"records_added": count, "elapsed_sec": round(elapsed, 2)}

    def run_full_crawl(self, limit: int = 10000000) -> Dict[str, Any]:
        """Gom dữ liệu toàn văn tổng hợp quy mô 10 triệu bản ghi từ báo chí, pháp luật và kho mở."""
        logger.info("=== BẮT ĐẦU CHIẾN DỊCH GOM DỮ LIỆU TOÀN DIỆN (MỤC TIÊU: %d BẢN GHI) ===", limit)
        start_time = time.perf_counter()

        # Kiểm tra số lượng tài liệu đã có sẵn trong data/crawl/
        existing_docs = 0
        manifest_path = os.path.join(self.config.output_dir, "CRAWL_MANIFEST.json")
        if os.path.exists(manifest_path):
            try:
                import json
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
                    existing_docs = manifest.get("total_documents", 0)
            except Exception:
                existing_docs = 0

        needed = max(0, limit - existing_docs)
        logger.info("Hiện đã có sẵn: %d tài liệu. Cần thu thập thêm: %d tài liệu để đạt mục tiêu %d.", existing_docs, needed, limit)

        if needed == 0:
            logger.info("Đã đạt chỉ tiêu %d tài liệu. Không cần thu thập thêm.", limit)
            return {"records_added": 0, "total_documents": existing_docs, "elapsed_sec": 0.0}

        newly_collected = 0

        with ShardWriter(output_dir=self.config.output_dir, shard_size=self.config.shard_size) as writer:
            # 1. Cào tin tức báo chí trực tiếp nếu chưa có
            if newly_collected < needed and existing_docs < 50000:
                logger.info("Giai đoạn 1: Cào tin tức báo điện tử thời sự trực tuyến...")
                rss_crawler = RssNewsCrawler(self.config)
                for rec in rss_crawler.stream(limit=min(needed, 20000)):
                    writer.write(rec)
                    newly_collected += 1
                    if newly_collected >= needed:
                        break

            # 2. Thu thập văn bản quy phạm pháp luật
            if newly_collected < needed and existing_docs < 500000:
                logger.info("Giai đoạn 2: Thu thập văn bản pháp luật và chính sách Việt Nam...")
                legal_crawler = LegalCrawler(self.config)
                for rec in legal_crawler.stream(limit=needed - newly_collected):
                    writer.write(rec)
                    newly_collected += 1
                    if newly_collected % 10000 == 0:
                        logger.info("Tiến độ gom dữ liệu mới: %d / %d bản ghi...", newly_collected, needed)
                    if newly_collected >= needed:
                        break

            # 3. Nạp ngữ liệu tiếng Việt quy mô lớn (Wikipedia, xP3x, C4 vi...)
            if newly_collected < needed:
                logger.info("Giai đoạn 3: Nạp kho ngữ liệu bách khoa toàn thư và văn bản tiếng Việt quy mô lớn (C4/Wikipedia)...")
                hf_streamer = HuggingFaceStreamer()
                for rec in hf_streamer.stream(limit=needed - newly_collected):
                    writer.write(rec)
                    newly_collected += 1
                    if newly_collected % 20000 == 0:
                        logger.info("Tiến độ gom dữ liệu mới: %d / %d bản ghi...", newly_collected, needed)
                    if newly_collected >= needed:
                        break

        elapsed = time.perf_counter() - start_time
        total_now = existing_docs + newly_collected
        logger.info("Hoàn tất gom dữ liệu: thêm %d bản ghi mới (Tổng: %d bản ghi) trong %.2f giây.", newly_collected, total_now, elapsed)
        return {"records_added": newly_collected, "total_documents": total_now, "elapsed_sec": round(elapsed, 2)}

    def run_drive_download(self, file_id_or_url: str, output_path: str) -> bool:
        """Tải tệp dữ liệu dung lượng lớn từ Google Drive."""
        logger.info("=== BẮT ĐẦU TẢI DỮ LIỆU TỪ GOOGLE DRIVE ===")
        return GoogleDriveDownloader.download_file(file_id_or_url, output_path)
