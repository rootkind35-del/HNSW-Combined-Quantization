"""Thư viện thu thập dữ liệu (Crawler) toàn văn tiếng Việt và quản lý shard quy mô lớn."""

from crawler.config import CrawlerConfig
from crawler.extractors.article_parser import ArticleParser
from crawler.extractors.text_cleaner import TextCleaner
from crawler.http_client import HttpClient
from crawler.pipeline import CrawlerPipeline
from crawler.sources.drive_downloader import GoogleDriveDownloader
from crawler.sources.hf_streamer import HuggingFaceStreamer
from crawler.sources.legal_crawler import LegalCrawler
from crawler.sources.rss_crawler import RssNewsCrawler
from crawler.storage.shard_writer import ShardWriter

__all__ = [
    "ArticleParser",
    "CrawlerConfig",
    "CrawlerPipeline",
    "GoogleDriveDownloader",
    "HttpClient",
    "HuggingFaceStreamer",
    "LegalCrawler",
    "RssNewsCrawler",
    "ShardWriter",
    "TextCleaner",
]
