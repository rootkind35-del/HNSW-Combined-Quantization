"""Cấu hình cho thư viện thu thập dữ liệu (Crawler)."""

import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class CrawlerConfig:
    """Cấu hình tham số kết nối, lưu trữ và các nguồn dữ liệu."""

    # Đường dẫn lưu trữ đầu ra
    output_dir: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "crawl"))
    
    # Kích thước mỗi tệp shard (số lượng văn bản toàn văn trên mỗi tệp)
    shard_size: int = 50000

    # Tham số HTTP mạng
    request_timeout: int = 15
    max_retries: int = 3
    backoff_factor: float = 1.5
    rate_limit_delay: float = 0.2  # Giây nghỉ giữa các request để tránh bị chặn IP

    # Danh sách User-Agent chuẩn duyệt web
    user_agents: List[str] = field(default_factory=lambda: [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    ])

    # Danh mục các nguồn tin tức và văn bản pháp luật chính thống Việt Nam
    rss_sources: List[tuple] = field(default_factory=lambda: [
        # Thư viện Pháp luật & Cổng Pháp luật Việt Nam
        ("Thư Viện Pháp Luật - Chính Sách Mới", "https://thuvienphapluat.vn/rss/chinh-sach-phap-luat-moi.rss"),
        ("Thư Viện Pháp Luật - Thời Sự Pháp Luật", "https://thuvienphapluat.vn/rss/thoi-su-phap-luat.rss"),
        ("Thư Viện Pháp Luật - Án Lệ", "https://thuvienphapluat.vn/rss/an-le.rss"),
        ("Luật Việt Nam - Văn Bản Mới", "https://luatvietnam.vn/rss/van-ban-moi.rss"),
        ("Luật Việt Nam - Chính Sách Mới", "https://luatvietnam.vn/rss/chinh-sach-moi.rss"),
        # Báo điện tử VNExpress
        ("VNExpress - Tin Mới", "https://vnexpress.net/rss/tin-moi-nhat.rss"),
        ("VNExpress - Thời Sự", "https://vnexpress.net/rss/thoi-su.rss"),
        ("VNExpress - Pháp Luật", "https://vnexpress.net/rss/phap-luat.rss"),
        ("VNExpress - Kinh Doanh", "https://vnexpress.net/rss/kinh-doanh.rss"),
        ("VNExpress - Khoa Học", "https://vnexpress.net/rss/khoa-hoc.rss"),
        ("VNExpress - Số Hóa", "https://vnexpress.net/rss/so-hoa.rss"),
        ("VNExpress - Giáo Dục", "https://vnexpress.net/rss/giao-duc.rss"),
        # Báo Dân Trí
        ("Dân Trí - Trang Chủ", "https://dantri.com.vn/rss/home.rss"),
        ("Dân Trí - Xã Hội", "https://dantri.com.vn/rss/xa-hoi.rss"),
        ("Dân Trí - Pháp Luật", "https://dantri.com.vn/rss/phap-luat.rss"),
        ("Dân Trí - Sức Mạnh Số", "https://dantri.com.vn/rss/suc-manh-so.rss"),
        ("Dân Trí - Kinh Doanh", "https://dantri.com.vn/rss/kinh-doanh.rss"),
        # Báo Tuổi Trẻ
        ("Tuổi Trẻ - Tin Mới", "https://tuoitre.vn/rss/tin-moi-nhat.rss"),
        ("Tuổi Trẻ - Thời Sự", "https://tuoitre.vn/rss/thoi-su.rss"),
        ("Tuổi Trẻ - Pháp Luật", "https://tuoitre.vn/rss/phap-luat.rss"),
        ("Tuổi Trẻ - Kinh Doanh", "https://tuoitre.vn/rss/kinh-doanh.rss"),
        # Báo VietnamNet
        ("VietnamNet - Thời Sự", "https://vietnamnet.vn/rss/thoi-su.rss"),
        ("VietnamNet - Pháp Luật", "https://vietnamnet.vn/rss/phap-luat.rss"),
        ("VietnamNet - Công Nghệ", "https://vietnamnet.vn/rss/cong-nghe.rss"),
        ("VietnamNet - Kinh Doanh", "https://vietnamnet.vn/rss/kinh-doanh.rss"),
        # Báo Thanh Niên
        ("Thanh Niên - Trang Chủ", "https://thanhnien.vn/rss/home.rss"),
        ("Thanh Niên - Thời Sự", "https://thanhnien.vn/rss/thoi-su.rss"),
        ("Thanh Niên - Pháp Luật", "https://thanhnien.vn/rss/phap-luat.rss"),
        # Báo Lao Động & Tiền Phong & Nhân Dân
        ("Lao Động - Trang Chủ", "https://laodong.vn/rss/home.rss"),
        ("Lao Động - Pháp Luật", "https://laodong.vn/rss/phap-luat.rss"),
        ("Tiền Phong - Trang Chủ", "https://tienphong.vn/rss/home.rss"),
        ("Báo Nhân Dân - Tin Mới", "https://nhandan.vn/rss/tin-moi-nhat.rss"),
    ])
