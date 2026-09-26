> **LƯU Ý:** Tài liệu này đã cũ và được thay thế toàn bộ bởi [BAO_CAO_LUAN_VAN_CHIT_TIET.md](BAO_CAO_LUAN_VAN_CHIT_TIET.md). Xin vui lòng tham khảo file báo cáo chính thức để xem kiến trúc Two-Tier HNSW lượng tử hóa SQ8 mới nhất.

# BÃ¡o cÃ¡o Ká»¹ thuáº­t Chi tiáº¿t: Luá»“ng Thu tháº­p Dá»¯ liá»‡u (Crawler Pipeline)

TÃ i liá»‡u nÃ y Ä‘Æ°á»£c biÃªn soáº¡n dÃ nh cho ká»¹ sÆ° má»›i nháº±m giáº£i thÃ­ch chi tiáº¿t cáº¥u trÃºc, nguyÃªn lÃ½ thiáº¿t káº¿, mÃ£ nguá»“n tá»«ng hÃ m vÃ  lÃ½ do lá»±a chá»n cÃ¡c giáº£i phÃ¡p ká»¹ thuáº­t trong há»‡ thá»‘ng thu tháº­p dá»¯ liá»‡u toÃ n vÄƒn quy mÃ´ lá»›n.

---

## 1. Tá»•ng quan Kiáº¿n trÃºc Há»‡ thá»‘ng Thu tháº­p

Há»‡ thá»‘ng thu tháº­p Ä‘Æ°á»£c thiáº¿t káº¿ theo mÃ´ hÃ¬nh kiáº¿n trÃºc dáº¡ng á»‘ng dáº«n (Pipeline Architecture) vá»›i cÃ¡c nguyÃªn táº¯c cá»‘t lÃµi:

1. **Báº£o toÃ n 100% ná»™i dung toÃ n vÄƒn:** KhÃ´ng cáº¯t cá»¥t thÃ¢n bÃ i, khÃ´ng chá»‰ láº¥y tiÃªu Ä‘á» hay tÃ³m táº¯t.
2. **KhÃ´ng trÃ n bá»™ nhá»› RAM (Zero-OOM Streaming):** Sá»­ dá»¥ng `Generator` (`yield`) vÃ  ghi luá»“ng trá»±c tiáº¿p ra Ä‘Ä©a SSD. KhÃ´ng bao giá» gom hÃ ng triá»‡u báº£n ghi vÃ o má»™t máº£ng Python trong bá»™ nhá»›.
3. **PhÃ¢n Ä‘oáº¡n Shard chuáº©n hÃ³a (Chunked Storage):** Dá»¯ liá»‡u Ä‘Æ°á»£c chia nhá» thÃ nh cÃ¡c tá»‡p `shard_XXXXX.jsonl` cá»‘ Ä‘á»‹nh 50.000 báº£n ghi/tá»‡p, giÃºp viá»‡c Ä‘á»c song song, nÃ©n vÃ  láº­p chá»‰ má»¥c khÃ´ng bá»‹ ngháº½n I/O.
4. **Kháº£ nÄƒng tá»± phá»¥c há»“i (Resumability & Checkpointing):** Khi tiáº¿n trÃ¬nh gáº·p sá»± cá»‘ máº¡ng hoáº·c khá»Ÿi Ä‘á»™ng láº¡i mÃ¡y, há»‡ thá»‘ng tá»± Ä‘á»™ng nháº­n diá»‡n shard Ä‘Ã£ hoÃ n thÃ nh vÃ  tiáº¿p tá»¥c cÃ´ng viá»‡c tá»« Ä‘iá»ƒm dá»«ng gáº§n nháº¥t.

```mermaid
flowchart TD
    subgraph Sources ["Nguá»“n Dá»¯ liá»‡u"]
        S1["BÃ¡o Ä‘iá»‡n tá»­ Viá»‡t Nam (VNExpress, DÃ¢n TrÃ­, Tuá»•i Tráº»...)"]
        S2["Kho ngá»¯ liá»‡u vÄƒn báº£n PhÃ¡p luáº­t"]
        
    end

    subgraph Network ["Táº§ng Máº¡ng & Káº¿t ná»‘i"]
        HC["HttpClient (src/crawler/http_client.py)<br/>â€¢ Exponential Backoff<br/>â€¢ Rate Limiting<br/>â€¢ User-Agent Rotation"]
    end

    subgraph Parsing ["Táº§ng BÃ³c tÃ¡ch & Chuáº©n hÃ³a"]
        AP["ArticleParser (src/crawler/extractors/article_parser.py)<br/>TrÃ­ch xuáº¥t tiÃªu Ä‘á», tÃ³m táº¯t, toÃ n vÄƒn thÃ¢n bÃ i"]
        CW["Wikitext Cleaner (scripts/run_wiki_crawler.py)<br/>BÃ³c tÃ¡ch cáº¥u trÃºc section vÃ  paragraph"]
        TC["TextCleaner (src/crawler/extractors/text_cleaner.py)<br/>Chuáº©n hÃ³a Unicode NFC, xÃ³a HTML, dá»n khoáº£ng tráº¯ng"]
    end

    subgraph Storage ["Táº§ng LÆ°u trá»¯ ÄÄ©a SSD"]
        SW["ShardWriter (src/crawler/storage/shard_writer.py)<br/>â€¢ Ghi luá»“ng JSONL<br/>â€¢ Tá»± Ä‘á»™ng quay vÃ²ng Shard (50.000 báº£n ghi)<br/>â€¢ Xuáº¥t CRAWL_MANIFEST.json"]
        D1[("data/crawl/<br/>200 shards, 10M báº£n ghi")]
        D2[("data/crawl_wiki/<br/>200 shards, 10M báº£n ghi")]
    end

    S1 --> HC --> AP --> TC --> SW --> D1
    S2 --> HC --> AP --> TC --> SW --> D1
    S3 --> CW --> TC --> SW --> D2
```

---

## 2. Giáº£i thÃ­ch Chi tiáº¿t Tá»«ng Module vÃ  Tá»‡p MÃ£ Nguá»“n

### 2.1. Cáº¥u hÃ¬nh há»‡ thá»‘ng: `src/crawler/config.py`

#### Má»¥c Ä‘Ã­ch vÃ  vai trÃ²
Quáº£n lÃ½ toÃ n bá»™ tham sá»‘ mÃ´i trÆ°á»ng táº­p trung, trÃ¡nh tÃ¬nh tráº¡ng viáº¿t cá»©ng (hardcode) cÃ¡c thÃ´ng sá»‘ máº¡ng vÃ o code xá»­ lÃ½ logic.

#### CÃ¡c thÃ nh pháº§n mÃ£ nguá»“n chÃ­nh
```python
@dataclass
class CrawlerConfig:
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36..."
    request_timeout: int = 15
    max_retries: int = 3
    retry_backoff_factor: float = 1.5
    rate_limit_delay: float = 0.5
    shard_size: int = 50000
    rss_feeds: Dict[str, List[str]] = field(default_factory=lambda: {...})
```

#### Giáº£i thÃ­ch lÃ½ do thiáº¿t káº¿ vÃ  quy táº¯c Ä‘áº·t tÃªn cho nhÃ¢n viÃªn má»›i
- **Táº¡i sao dÃ¹ng `@dataclass`?** Dataclass trong Python tá»± Ä‘á»™ng táº¡o cÃ¡c hÃ m `__init__`, `__repr__`, giÃºp mÃ£ nguá»“n ngáº¯n gá»n, há»— trá»£ type hinting cháº·t cháº½ vÃ  dá»… dÃ ng serialize/deserialize khi cáº§n.
- **Táº¡i sao Ä‘áº·t tÃªn `retry_backoff_factor`?** Trong láº­p trÃ¬nh máº¡ng, khi mÃ¡y chá»§ quÃ¡ táº£i vÃ  tráº£ vá» mÃ£ lá»—i 429 hoáº·c 503, viá»‡c gá»­i láº¡i yÃªu cáº§u ngay láº­p tá»©c sáº½ lÃ m sáº­p mÃ¡y chá»§. Há»‡ sá»‘ giÃ£n cÃ¡ch lÃ¹i lÅ©y thá»«a (Exponential Backoff Factor) sáº½ nhÃ¢n thá»i gian chá» sau má»—i láº§n thá»­ láº¡i: $t = \text{backoff} \times 2^{\text{retry}}$, giÃºp giáº£m Ã¡p lá»±c lÃªn mÃ¡y chá»§ nguá»“n.
- **Táº¡i sao `rate_limit_delay = 0.5`?** ÄÃ¢y lÃ  nguyÃªn táº¯c thu tháº­p dá»¯ liá»‡u vÄƒn minh (Polite Crawling). Äáº£m báº£o khÃ´ng gá»­i quÃ¡ 2 yÃªu cáº§u/giÃ¢y Ä‘áº¿n cÃ¹ng má»™t domain bÃ¡o chÃ­ Ä‘á»ƒ khÃ´ng gÃ¢y ngháº½n dá»‹ch vá»¥ cá»§a há».

---

### 2.2. Giao tiáº¿p máº¡ng: `src/crawler/http_client.py`

#### Má»¥c Ä‘Ã­ch vÃ  vai trÃ²
Bá»c toÃ n bá»™ logic gá»i máº¡ng HTTP qua thÆ° viá»‡n `requests`, xá»­ lÃ½ tá»± Ä‘á»™ng cÆ¡ cháº¿ káº¿t ná»‘i láº¡i, quáº£n lÃ½ phiÃªn lÃ m viá»‡c (`requests.Session`) Ä‘á»ƒ tÃ¡i sá»­ dá»¥ng káº¿t ná»‘i TCP/TLS Socket.

#### CÃ¡c hÃ m chÃ­nh trong `HttpClient`
1. `__init__(self, config: Optional[CrawlerConfig] = None)`
   - *Má»¥c Ä‘Ã­ch:* Khá»Ÿi táº¡o session vÃ  thiáº¿t láº­p `urllib3.util.retry.Retry`.
   - *LÃ½ do:* TÃ¡i sá»­ dá»¥ng socket giÃºp giáº£m Ä‘á»™ trá»… tá»« 150ms xuá»‘ng dÆ°á»›i 20ms cho má»—i lÆ°á»£t gá»i, vÃ¬ khÃ´ng pháº£i báº¯t tay TLS (TLS Handshake) láº¡i tá»« Ä‘áº§u.
2. `_enforce_rate_limit(self, domain: str)`
   - *Má»¥c Ä‘Ã­ch:* Äo khoáº£ng thá»i gian giá»¯a hai lÆ°á»£t gá»i káº¿ tiáº¿p Ä‘áº¿n cÃ¹ng má»™t domain. Náº¿u nhá» hÆ¡n `rate_limit_delay`, tiáº¿n trÃ¬nh sáº½ `time.sleep` pháº§n thá»i gian chÃªnh lá»‡ch.
   - *TÃªn hÃ m:* Tiá»n tá»‘ `_` biá»ƒu thá»‹ hÃ m ná»™i bá»™ (private method), tÃªn `enforce_rate_limit` nÃ³i rÃµ hÃ nh vi báº¯t buá»™c tuÃ¢n thá»§ háº¡n ngáº¡ch tá»‘c Ä‘á»™.
3. `get(self, url: str) -> Optional[requests.Response]`
   - *Má»¥c Ä‘Ã­ch:* Thá»±c hiá»‡n yÃªu cáº§u HTTP GET an toÃ n, tá»± Ä‘á»™ng báº¯t táº¥t cáº£ cÃ¡c lá»—i ngoáº¡i lá»‡ `requests.RequestException` vÃ  tráº£ vá» `None` thay vÃ¬ lÃ m sáº­p toÃ n bá»™ luá»“ng cÃ o.

---

### 2.3. BÃ³c tÃ¡ch bÃ i bÃ¡o toÃ n vÄƒn: `src/crawler/extractors/article_parser.py`

#### Má»¥c Ä‘Ã­ch vÃ  vai trÃ²
Chuyá»ƒn Ä‘á»•i chuá»—i HTML thÃ´ thÃ nh Ä‘á»‘i tÆ°á»£ng bÃ i viáº¿t cÃ³ cáº¥u trÃºc (`title`, `description`, `content_full`).

#### Logic bÃ³c tÃ¡ch DOM
```python
def extract_full_article(self, html_content: str, url: str) -> Optional[Dict[str, str]]:
```
- **Bá»™ chá»n CSS chuyÃªn biá»‡t (Domain-Specific Selectors):** Má»—i tÃ²a soáº¡n sá»­ dá»¥ng cÃ¡c tháº» div chá»©a thÃ¢n bÃ i khÃ¡c nhau:
  - VNExpress: `p.description`, `article.fck_detail p.Normal`
  - DÃ¢n TrÃ­: `h1.title-page`, `div.singular-content p`
  - Tuá»•i Tráº»: `h1.article-title`, `div.content-fck p`
  - Thanh NiÃªn: `h1.detail-title`, `div.detail-cmain p`
  - VietnamNet: `h1.content-detail-title`, `div.maincontent p`
- **Loáº¡i bá» tháº» rÃ¡c trÆ°á»›c khi láº¥y text:**
  HÃ m tá»± Ä‘á»™ng quÃ©t vÃ  xÃ³a cÃ¡c thÃ nh pháº§n:
  ```python
  for junk in soup.find_all(["script", "style", "iframe", "table", "figure"]):
      junk.decompose()
  for junk_class in [".related-news", ".box-category", ".inner-article", ".z-quote"]:
      for el in soup.select(junk_class):
          el.decompose()
  ```
  *LÃ½ do:* CÃ¡c khá»‘i bÃ i viáº¿t liÃªn quan, quáº£ng cÃ¡o chÃ¨n giá»¯a bÃ i thÆ°á»ng chá»©a vÄƒn báº£n láº¡c Ä‘á», náº¿u khÃ´ng lá»c sáº½ lÃ m há»ng vector Ä‘áº·c trÆ°ng ngá»¯ nghÄ©a cá»§a bÃ i viáº¿t.

---

### 2.4. Chuáº©n hÃ³a vÄƒn báº£n: `src/crawler/extractors/text_cleaner.py`

#### Má»¥c Ä‘Ã­ch vÃ  vai trÃ²
Äáº£m báº£o tÃ­nh Ä‘á»“ng nháº¥t cá»§a vÄƒn báº£n tiáº¿ng Viá»‡t trÆ°á»›c khi Ä‘Æ°a vÃ o bá»™ chia Ä‘oáº¡n vÃ  nhÃºng vector.

#### CÃ¡c hÃ m chÃ­nh trong `TextCleaner`
1. `normalize_unicode(text: str) -> str`
   - *MÃ£ nguá»“n:* `unicodedata.normalize("NFC", text)`
   - *Táº¡i sao cá»±c ká»³ quan trá»ng Ä‘á»‘i vá»›i tiáº¿ng Viá»‡t?* Tiáº¿ng Viá»‡t cÃ³ hai kiá»ƒu dá»±ng mÃ£ Unicode:
     - **Tá»• há»£p (NFD):** KÃ½ tá»± gá»‘c vÃ  dáº¥u thanh tÃ¡ch rá»i (vÃ­ dá»¥: `a` + dáº¥u huyá»n = `Ã `, tá»‘n 2 codepoints).
     - **Dá»±ng sáºµn (NFC):** KÃ½ tá»± cÃ³ dáº¥u Ä‘Æ°á»£c mÃ£ hÃ³a thÃ nh 1 codepoint duy nháº¥t.
     Náº¿u khÃ´ng Ä‘Æ°a vá» NFC, hai tá»« cÃ¹ng hiá»ƒn thá»‹ giá»‘ng nhau trÃªn mÃ n hÃ¬nh sáº½ sinh ra hai vector Ä‘áº·c trÆ°ng hoÃ n toÃ n lá»‡ch nhau trong khÃ´ng gian vector.
2. `strip_html(text: str) -> str`
   - Sá»­ dá»¥ng regex `re.sub(r"<[^>]+>", " ", text)` Ä‘á»ƒ dá»n dáº¹p cÃ¡c tháº» tag sÃ³t láº¡i tá»« quÃ¡ trÃ¬nh bÃ³c tÃ¡ch.
3. `remove_urls(text: str) -> str`
   - Loáº¡i bá» cÃ¡c Ä‘Æ°á»ng dáº«n `http://` hoáº·c `https://` náº±m ráº£i rÃ¡c trong thÃ¢n bÃ i Ä‘á»ƒ trÃ¡nh sinh nhiá»…u ngá»¯ nghÄ©a.
4. `clean(text: str) -> str`
   - HÃ m tá»•ng há»£p cháº¡y toÃ n bá»™ chuá»—i lÃ m sáº¡ch vÃ  nÃ©n khoáº£ng tráº¯ng thá»«a (`\s+` $\to$ `" "`).

---

### 2.5. PhÃ¢n máº£nh lÆ°u trá»¯ Shard: `src/crawler/storage/shard_writer.py`

#### Má»¥c Ä‘Ã­ch vÃ  vai trÃ²
Nháº­n tá»«ng báº£n ghi dá»¯ liá»‡u Ä‘Ã£ lÃ m sáº¡ch vÃ  ghi tuáº§n tá»± vÃ o cÃ¡c tá»‡p JSONL theo kÃ­ch thÆ°á»›c cá»‘ Ä‘á»‹nh (50.000 dÃ²ng/shard), Ä‘á»“ng thá»i tá»± Ä‘á»™ng cáº­p nháº­t tá»‡p kÃª khai `CRAWL_MANIFEST.json`.

#### CÆ¡ cháº¿ hoáº¡t Ä‘á»™ng cá»§a `ShardWriter`
- **Táº¡i sao chá»n Ä‘á»‹nh dáº¡ng JSONL (JSON Lines)?**
  - KhÃ¡c vá»›i JSON thÃ´ng thÆ°á»ng (báº¯t buá»™c pháº£i cÃ³ cáº·p ngoáº·c `[...]` bao toÃ n bá»™ file), Ä‘á»‹nh dáº¡ng JSONL lÆ°u má»—i báº£n ghi trÃªn Ä‘Ãºng 1 dÃ²ng vÄƒn báº£n phÃ¢n tÃ¡ch báº±ng dáº¥u xuá»‘ng dÃ²ng `\n`.
  - *Lá»£i Ã­ch 1:* Cho phÃ©p má»Ÿ file á»Ÿ cháº¿ Ä‘á»™ ná»‘i tiáº¿p `append ("a")` vÃ  ghi ngay láº­p tá»©c vÃ o Ä‘Ä©a mÃ  khÃ´ng cáº§n náº¡p cáº£ file cÅ© vÃ o RAM.
  - *Lá»£i Ã­ch 2:* Náº¿u tiáº¿n trÃ¬nh bá»‹ máº¥t Ä‘iá»‡n hoáº·c crash Ä‘á»™t ngá»™t, toÃ n bá»™ cÃ¡c dÃ²ng Ä‘Ã£ ghi trÆ°á»›c Ä‘Ã³ váº«n nguyÃªn váº¹n 100%, khÃ´ng bá»‹ há»ng cáº¥u trÃºc cÃº phÃ¡p JSON cá»§a toÃ n bá»™ file.
  - *Lá»£i Ã­ch 3:* Cho phÃ©p cÃ¡c cÃ´ng cá»¥ dÃ²ng lá»‡nh Unix/Windows (`head`, `tail`, `wc -l`) vÃ  Python `line by line stream` Ä‘á»c dá»¯ liá»‡u vá»›i Ä‘á»™ phá»©c táº¡p bá»™ nhá»› $O(1)$.
- **HÃ m `write(self, record: Dict[str, Any])`:**
  - Kiá»ƒm tra náº¿u `_current_file` chÆ°a má»Ÿ, tá»± Ä‘á»™ng gá»i `_get_shard_path(idx)` Ä‘á»ƒ má»Ÿ file `shard_XXXXX.jsonl`.
  - Khi `current_shard_count >= shard_size` (50.000), file hiá»‡n táº¡i Ä‘Æ°á»£c gá»i `.flush()` vÃ  `.close()`, sau Ä‘Ã³ tÄƒng `current_shard_idx` Ä‘á»ƒ chuyá»ƒn sang shard má»›i.
- **HÃ m `close(self)`:**
  - ÄÃ³ng tá»‡p Ä‘ang má»Ÿ vÃ  quÃ©t toÃ n bá»™ thÆ° má»¥c Ä‘á»ƒ tÃ­nh tá»•ng sá»‘ tÃ i liá»‡u, tá»•ng dung lÆ°á»£ng MB/GB vÃ  ghi ra `CRAWL_MANIFEST.json`.

---

#### Má»¥c Ä‘Ã­ch vÃ  vai trÃ²

#### CÃ¡c hÃ m chuyÃªn biá»‡t trong `run_wiki_crawler.py`
1. `clean_wikitext(text: str) -> str`
   - Sá»­ dá»¥ng cÃ¡c biá»ƒu thá»©c chÃ­nh quy (Regex) tá»‘i Æ°u Ä‘á»ƒ loáº¡i bá» toÃ n bá»™ cÃº phÃ¡p Ä‘Ã¡nh dáº¥u Wikitext:
     - XÃ³a template há»™p thÃ´ng tin: `re.sub(r"\{\{[^}]*\}\}", " ", text)`
     - Giá»¯ láº¡i nhÃ£n liÃªn káº¿t ná»™i bá»™: `[[HÃ  Ná»™i|thá»§ Ä‘Ã´]]` $\to$ `thá»§ Ä‘Ã´`
     - XÃ³a tháº» tham chiáº¿u nguá»“n há»c thuáº­t: `<ref>...</ref>`
     - XÃ³a báº£ng biá»ƒu wiki: `\{\|.*?\|\}`
2. `is_boilerplate_header(header_name: str) -> bool`
   - Kiá»ƒm tra cÃ¡c tiÃªu Ä‘á» má»¥c phá»¥ lá»¥c nhÆ° *"Tham kháº£o"*, *"LiÃªn káº¿t ngoÃ i"*, *"Xem thÃªm"*, *"TÃ i liá»‡u tham kháº£o"*.
   - *LÃ½ do:* CÃ¡c má»¥c nÃ y chá»‰ chá»©a Ä‘Æ°á»ng link, tÃªn sÃ¡ch hoáº·c sá»‘ ISBN, khÃ´ng chá»©a tri thá»©c thá»±c sá»±, viá»‡c loáº¡i bá» giÃºp nÃ¢ng cao Ä‘á»™ chÃ­nh xÃ¡c cá»§a ngá»¯ liá»‡u.

   - Sá»­ dá»¥ng `datasets.load_dataset(..., streaming=True)` Ä‘á»ƒ káº¿t ná»‘i trá»±c tiáº¿p Ä‘áº¿n cÃ¡c tá»‡p lÆ°u trá»¯ Parquet trÃªn Hugging Face.
   - TrÃ­ch xuáº¥t tá»«ng bÃ i viáº¿t vÃ  phÃ¢n tÃ¡ch thÃ nh cÃ¡c má»¥c ngá»¯ cáº£nh Ä‘á»™c láº­p theo Ä‘á»‹nh dáº¡ng header `== ... ==`.
   - Má»—i má»¥c cÃ³ Ä‘á»™ dÃ i $\ge 15$ tá»« Ä‘Æ°á»£c sinh ra (`yield`) thÃ nh má»™t báº£n ghi hoÃ n chá»‰nh:
     ```json
     {
       "doc_id": "wiki_291b11bddbdb8fe4",
       "title": "Internet Society - Má»¥c tiÃªu hoáº¡t Ä‘á»™ng",
       
       "content_full": "Ná»™i dung vÄƒn báº£n toÃ n vÄƒn cá»§a má»¥c...",
       
     }
     ```
4. `main()`
   - Quáº£n lÃ½ vÃ²ng láº·p thu tháº­p tá»›i má»‘c 10.000.000 báº£n ghi.
   - Ghi checkpoint Ä‘á»‹nh ká»³ má»—i 10.000 báº£n ghi vÃ o `data/crawl_wiki/crawl_checkpoint.json`.
   - Tá»± Ä‘á»™ng duy trÃ¬ bá»™ nhá»› Ä‘á»‡m bÄƒm `seen_hashes` Ä‘á»ƒ loáº¡i trá»« trÃ¹ng láº·p ná»™i dung khi chuyá»ƒn giá»¯a cÃ¡c nguá»“n dá»¯ liá»‡u.

---

## 3. Tá»•ng káº¿t Cáº¥u trÃºc ThÆ° má»¥c vÃ  Táº­p Dá»¯ liá»‡u CÃ o

```text
ANN/
â”œâ”€â”€ data/
â”‚   â”œâ”€â”€ crawl/                                # Dá»¯ liá»‡u BÃ¡o chÃ­ & PhÃ¡p luáº­t (16.459.486 báº£n ghi)
â”‚   â”‚   â”œâ”€â”€ CRAWL_MANIFEST.json               # KÃª khai 200 shards, 20.45 GB
â”‚   â”‚   â”œâ”€â”€ shard_00000.jsonl                 # PhÃ¢n Ä‘oáº¡n báº£n ghi toÃ n vÄƒn
â”‚   â”‚   â””â”€â”€ ... (shard_00001 -> shard_00199)
â”‚   â”‚
â”‚       â”œâ”€â”€ crawl_checkpoint.json             # LÆ°u váº¿t tiáº¿n Ä‘á»™ thu tháº­p
â”‚       â”œâ”€â”€ shard_00000.jsonl                 # PhÃ¢n Ä‘oáº¡n bÃ¡ch khoa toÃ n thÆ°
â”‚       â””â”€â”€ ... (shard_00001 -> shard_00199)
â”‚
â”œâ”€â”€ src/crawler/                              # ThÆ° viá»‡n crawler dÃ¹ng chung
â”‚   â”œâ”€â”€ config.py                             # Cáº¥u hÃ¬nh tham sá»‘ máº¡ng
â”‚   â”œâ”€â”€ http_client.py                        # Client HTTP cÃ³ backoff retry
â”‚   â”œâ”€â”€ extractors/
â”‚   â”‚   â”œâ”€â”€ article_parser.py                 # BÃ³c tÃ¡ch DOM HTML
â”‚   â”‚   â””â”€â”€ text_cleaner.py                   # Chuáº©n hÃ³a Unicode NFC
â”‚   â”œâ”€â”€ sources/
â”‚   â”‚   â”œâ”€â”€ rss_crawler.py                    # CÃ o RSS bÃ¡o chÃ­
â”‚   â”‚   â”œâ”€â”€ hf_streamer.py                    # Truyá»n phÃ¡t dá»¯ liá»‡u má»Ÿ
â”‚   â”‚   â””â”€â”€ drive_downloader.py               # Táº£i tá»‡p lá»›n tá»« Ä‘Ã¡m mÃ¢y
â”‚   â”œâ”€â”€ storage/
â”‚   â”‚   â””â”€â”€ shard_writer.py                   # Bá»™ phÃ¢n Ä‘oáº¡n ghi Ä‘Ä©a JSONL
â”‚   â””â”€â”€ pipeline.py                           # Äiá»u phá»‘i cÃ o BÃ¡o chÃ­
â”‚
â””â”€â”€ scripts/
    â”œâ”€â”€ run_crawler.py                        # CLI cÃ o tin tá»©c & phÃ¡p luáº­t
```

