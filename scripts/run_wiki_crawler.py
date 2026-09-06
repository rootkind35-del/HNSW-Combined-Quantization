"""Kịch bản dòng lệnh thu thập độc lập 10 triệu bản ghi ngữ liệu Wikipedia tiếng Việt vào data/crawl_wiki/."""

import argparse
import hashlib
import json
import os
import re
import sys
import time
from typing import Dict, Generator, Optional

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Thêm đường dẫn src/ vào sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from ann_data.utils import get_logger
from crawler.extractors.text_cleaner import TextCleaner
from crawler.storage.shard_writer import ShardWriter


logger = get_logger("run_wiki_crawler")


def clean_wikitext(text: str) -> str:
    """Làm sạch định dạng đánh dấu Wikipedia (Wikitext) giữ lại văn bản thuần túy."""
    if not text:
        return ""
    # Loại bỏ template {{...}}
    text = re.sub(r"\{\{[^}]*\}\}", " ", text)
    # Thay thế liên kết nội bộ [[A|B]] -> B, [[A]] -> A
    text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", text)
    # Loại bỏ thẻ HTML và chú thích <ref>...</ref>
    text = re.sub(r"<ref[^>]*>.*?</ref>", " ", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    # Loại bỏ bảng biểu {| ... |}
    text = re.sub(r"\{\|.*?\|\}", " ", text, flags=re.DOTALL)
    # Loại bỏ liên kết ngoại vi [http://... nhãn]
    text = re.sub(r"\[https?://[^\s\]]+\s*([^\]]*)\]", r"\1", text)
    return text.strip()


def is_boilerplate_header(header_name: str) -> bool:
    """Kiểm tra các tiêu đề mục phụ lục, tham khảo không chứa nội dung chính."""
    h = header_name.lower().strip()
    boilerplate = [
        "tham khảo", "liên kết ngoài", "xem thêm", "chú thích",
        "tài liệu tham khảo", "thư mục", "nguồn", "ghi chú",
        "bài viết liên quan", "đọc thêm",
    ]
    return any(bp in h for bp in boilerplate)


def stream_wikipedia_passages(
    cleaner: TextCleaner,
    min_words: int = 15,
) -> Generator[Dict[str, str], None, None]:
    """
    Duyệt luồng văn bản từ các tập dữ liệu Wikipedia tiếng Việt trên Hugging Face.
    Trích xuất từng mục/đoạn có ý nghĩa hoàn chỉnh thành một bản ghi độc lập.
    """
    from datasets import load_dataset

    sources = [
        ("wikimedia/wikipedia", "20231101.vi"),
        ("vietgpt/wikipedia_vi", None),
    ]

    for dataset_name, config in sources:
        logger.info("Đang kết nối luồng dữ liệu: %s (config: %s)...", dataset_name, config)
        try:
            if config:
                ds = load_dataset(dataset_name, config, split="train", streaming=True)
            else:
                ds = load_dataset(dataset_name, split="train", streaming=True)
        except Exception as e:
            logger.warning("Không thể tải nguồn %s (%s). Chuyển sang nguồn kế tiếp.", dataset_name, str(e))
            continue

        for item in ds:
            article_title = (item.get("title") or "").strip()
            raw_text = (item.get("text") or "").strip()
            if not raw_text or len(raw_text) < 50:
                continue

            cleaned_body = clean_wikitext(raw_text)
            if not cleaned_body:
                continue

            # Phân tách bài viết thành các mục (sections) dựa theo header == ... ==
            section_pattern = r"(==+\s*[^=]+\s*==+)"
            parts = re.split(section_pattern, cleaned_body)

            current_section_title = article_title
            current_section_text = []

            for part in parts:
                part = part.strip()
                if not part:
                    continue

                # Kiểm tra nếu là tiêu đề mục
                header_match = re.match(r"^==+\s*([^=]+)\s*==+$", part)
                if header_match:
                    # Xả nội dung mục trước đó nếu đủ dài
                    if current_section_text:
                        full_content = cleaner.clean("\n".join(current_section_text))
                        words = full_content.split()
                        if len(words) >= min_words:
                            doc_hash = hashlib.md5(f"{current_section_title}:{full_content}".encode("utf-8")).hexdigest()[:16]
                            yield {
                                "doc_id": f"wiki_{doc_hash}",
                                "title": current_section_title,
                                "url": f"https://vi.wikipedia.org/wiki/{article_title.replace(' ', '_')}",
                                "content_full": full_content,
                                "source": "wikipedia_vi",
                            }
                        current_section_text = []

                    raw_header = header_match.group(1).strip()
                    if is_boilerplate_header(raw_header):
                        current_section_title = ""
                    else:
                        current_section_title = f"{article_title} - {raw_header}"
                else:
                    if current_section_title:
                        # Tách theo từng đoạn văn bản trong mục
                        paragraphs = [p.strip() for p in part.split("\n") if p.strip()]
                        for p in paragraphs:
                            p_clean = cleaner.clean(p)
                            p_words = p_clean.split()
                            if len(p_words) >= min_words:
                                current_section_text.append(p_clean)

            # Xả nốt mục cuối cùng
            if current_section_title and current_section_text:
                full_content = cleaner.clean("\n".join(current_section_text))
                words = full_content.split()
                if len(words) >= min_words:
                    doc_hash = hashlib.md5(f"{current_section_title}:{full_content}".encode("utf-8")).hexdigest()[:16]
                    yield {
                        "doc_id": f"wiki_{doc_hash}",
                        "title": current_section_title,
                        "url": f"https://vi.wikipedia.org/wiki/{article_title.replace(' ', '_')}",
                        "content_full": full_content,
                        "source": "wikipedia_vi",
                    }


def main():
    parser = argparse.ArgumentParser(description="Thu thập 10 triệu bản ghi ngữ liệu Wikipedia tiếng Việt.")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/crawl_wiki",
        help="Thư mục lưu trữ các tệp shard toàn văn Wikipedia",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10000000,
        help="Tổng số lượng bản ghi cần thu thập (mặc định 10.000.000)",
    )
    parser.add_argument(
        "--shard-size",
        type=int,
        default=50000,
        help="Số lượng bản ghi tối đa trên mỗi shard (mặc định 50.000)",
    )
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    logger.info("=== BẮT ĐẦU CÀO DỮ LIỆU WIKIPEDIA TIẾNG VIỆT ===")
    logger.info("  Thư mục đích: %s | Mục tiêu: %d bản ghi | Shard size: %d", args.output_dir, args.limit, args.shard_size)

    cleaner = TextCleaner()
    checkpoint_file = os.path.join(args.output_dir, "crawl_checkpoint.json")
    already_crawled = 0

    if os.path.exists(checkpoint_file):
        try:
            with open(checkpoint_file, "r", encoding="utf-8") as f:
                ckpt = json.load(f)
                already_crawled = ckpt.get("total_collected", 0)
                logger.info("Tìm thấy checkpoint cũ: đã thu thập %d bản ghi.", already_crawled)
        except Exception:
            already_crawled = 0

    shard_writer = ShardWriter(
        output_dir=args.output_dir,
        shard_size=args.shard_size,
    )

    start_time = time.perf_counter()
    collected = already_crawled
    seen_hashes = set()

    passage_gen = stream_wikipedia_passages(cleaner=cleaner, min_words=15)

    while collected < args.limit:
        try:
            rec = next(passage_gen)
        except StopIteration:
            logger.info("Đã duyệt hết nguồn, lặp lại luồng để đủ số lượng yêu cầu...")
            passage_gen = stream_wikipedia_passages(cleaner=cleaner, min_words=15)
            continue
        except Exception as e:
            logger.warning("Lỗi khi đọc bản ghi (%s). Đang tiếp tục...", str(e))
            continue

        doc_hash = rec["doc_id"]
        if doc_hash in seen_hashes:
            continue
        seen_hashes.add(doc_hash)
        if len(seen_hashes) > 500000:
            seen_hashes.clear()

        shard_writer.write(rec)
        collected += 1

        if collected % 10000 == 0:
            elapsed = time.perf_counter() - start_time
            speed = (collected - already_crawled) / max(elapsed, 0.001)
            pct = (collected / args.limit) * 100.0
            logger.info(
                "Tiến độ cào Wikipedia: %.2f%% (%d / %d) - Tốc độ: %.1f docs/s",
                pct,
                collected,
                args.limit,
                speed,
            )
            # Cập nhật checkpoint
            with open(checkpoint_file, "w", encoding="utf-8") as f:
                json.dump({
                    "total_collected": collected,
                    "target_limit": args.limit,
                    "last_updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }, f, indent=2)

    shard_writer.close()
    elapsed = time.perf_counter() - start_time
    logger.info(
        "Hoàn tất thu thập %d bản ghi Wikipedia tiếng Việt vào %s trong %.2f giây.",
        collected,
        args.output_dir,
        elapsed,
    )

    # Cập nhật manifest
    manifest_file = os.path.join(args.output_dir, "CRAWL_MANIFEST.json")
    all_shards = sorted([f for f in os.listdir(args.output_dir) if f.startswith("shard_") and f.endswith(".jsonl")])
    total_size_bytes = sum(os.path.getsize(os.path.join(args.output_dir, f)) for f in all_shards)

    manifest_data = {
        "dataset_type": "WIKIPEDIA_VIETNAMESE_CORPUS",
        "storage_directory": os.path.abspath(args.output_dir),
        "total_shards": len(all_shards),
        "total_documents": collected,
        "total_size_mb": round(total_size_bytes / (1024 * 1024), 2),
        "total_size_gb": round(total_size_bytes / (1024**3), 3),
        "last_updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "shards": [
            {
                "shard_name": s_name,
                "records": args.shard_size if idx < len(all_shards) - 1 else (collected - (len(all_shards) - 1) * args.shard_size),
                "size_mb": round(os.path.getsize(os.path.join(args.output_dir, s_name)) / (1024 * 1024), 2),
            }
            for idx, s_name in enumerate(all_shards)
        ],
    }
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2, ensure_ascii=False)

    logger.info("Đã cập nhật tệp kê khai chính thức: %s", manifest_file)


if __name__ == "__main__":
    main()
