> **LƯU Ý:** Tài liệu này đã cũ và được thay thế toàn bộ bởi [BAO_CAO_LUAN_VAN_CHIT_TIET.md](BAO_CAO_LUAN_VAN_CHIT_TIET.md). Xin vui lòng tham khảo file báo cáo chính thức để xem kiến trúc Two-Tier HNSW lượng tử hóa SQ8 mới nhất.

# HÆ°á»›ng dáº«n Thá»±c hiá»‡n â€” HNSW Combined Quantization

**PhiÃªn báº£n:** v1.0.0  
**Cáº­p nháº­t:** ThÃ¡ng 9, 2026  
**Pháº¡m vi:** CÃ i Ä‘áº·t, cháº¡y thá»­, sá»­ dá»¥ng dashboard vÃ  Ä‘Ã¡nh giÃ¡ káº¿t quáº£

---

## Má»¥c lá»¥c

1. [YÃªu cáº§u Pháº§n cá»©ng & Pháº§n má»m](#1-yÃªu-cáº§u-pháº§n-cá»©ng--pháº§n-má»m)
2. [Táº£i Dá»¯ liá»‡u (Báº¯t buá»™c)](#2-táº£i-dá»¯-liá»‡u-báº¯t-buá»™c)
3. [CÃ i Ä‘áº·t Dá»± Ã¡n](#3-cÃ i-Ä‘áº·t-dá»±-Ã¡n)
4. [Cháº¡y Dashboard Trá»±c quan](#4-cháº¡y-dashboard-trá»±c-quan)
5. [HÆ°á»›ng dáº«n Sá»­ dá»¥ng Tá»«ng Tab](#5-hÆ°á»›ng-dáº«n-sá»­-dá»¥ng-tá»«ng-tab)
6. [Cháº¡y ÄÃ¡nh giÃ¡ Thuáº­t toÃ¡n](#6-cháº¡y-Ä‘Ã¡nh-giÃ¡-thuáº­t-toÃ¡n)
7. [Cháº¡y Pipeline Tá»« Äáº§u](#7-cháº¡y-pipeline-tá»«-Ä‘áº§u)
8. [Cáº¥u hÃ¬nh SiÃªu tham sá»‘](#8-cáº¥u-hÃ¬nh-siÃªu-tham-sá»‘)
9. [Cháº¡y Bá»™ Kiá»ƒm thá»­](#9-cháº¡y-bá»™-kiá»ƒm-thá»­)
10. [API Reference](#10-api-reference)
11. [Xá»­ lÃ½ Sá»± cá»‘ ThÆ°á»ng gáº·p](#11-xá»­-lÃ½-sá»±-cá»‘-thÆ°á»ng-gáº·p)

---

## 1. YÃªu cáº§u Pháº§n cá»©ng & Pháº§n má»m

### Tá»‘i thiá»ƒu

| ThÃ nh pháº§n | YÃªu cáº§u |
|:---|:---|
| RAM | 16 GB (Ä‘á»§ cháº¡y Two-Tier HNSW) |
| Storage | 15 GB NVMe SSD trá»‘ng (cho index SQ8) |
| CPU | x86_64 vá»›i AVX2 |
| Python | 3.11 hoáº·c cao hÆ¡n |
| Node.js | 20 hoáº·c cao hÆ¡n |

### Khuyáº¿n nghá»‹

| ThÃ nh pháº§n | Khuyáº¿n nghá»‹ |
|:---|:---|
| RAM | 32 GB+ |
| Storage | 50 GB+ SSD (cho dá»¯ liá»‡u float32 + SQ8 + cache) |
| CPU | Há»— trá»£ AVX-512 cho hiá»‡u suáº¥t SIMD tá»‘t hÆ¡n |

> **LÆ°u Ã½:** Standard HNSW trÃªn 16.45M vector cáº§n ~64 GB RAM. Chá»‰ Two-Tier Quantized HNSW má»›i cháº¡y Ä‘Æ°á»£c trÃªn mÃ¡y 16-32 GB.

---

## 2. Táº£i Dá»¯ liá»‡u (Báº¯t buá»™c)

Do giá»›i háº¡n vá» dung lÆ°á»£ng cá»§a GitHub, dá»¯ liá»‡u khÃ´ng Ä‘Æ°á»£c Ä‘Ã­nh kÃ¨m trong mÃ£ nguá»“n. Báº¡n cáº§n táº£i dá»¯ liá»‡u vÃ  Ä‘áº·t Ä‘Ãºng vÃ o thÆ° má»¥c `data/`.

ðŸ‘‰ **Link táº£i trá»n bá»™ dá»¯ liá»‡u (Google Drive):**  
[https://drive.google.com/drive/folders/1b2yiq6Ly5cl3VdNW2LuM1EqdaZNdpbPW?usp=sharing](https://drive.google.com/drive/folders/1b2yiq6Ly5cl3VdNW2LuM1EqdaZNdpbPW?usp=sharing)

**CÃ¡ch bá»‘ trÃ­ thÆ° má»¥c dá»¯ liá»‡u sau khi táº£i:**
```text
HNSW-Combined-Quantization/
â”œâ”€â”€ data/
â”‚   â”œâ”€â”€ processed/
â”‚   â”‚   â”œâ”€â”€ search_index_cache.npz          # 5,000 vector Ä‘Ã£ chuáº©n hÃ³a
â”‚   â”‚   â”œâ”€â”€ search_index_metadata.json      # Metadata 5,000 tÃ i liá»‡u
â”‚   â”‚   â”œâ”€â”€ pca_3d_projection.json          # Tá»a Ä‘á»™ PCA 3D
â”‚   â”‚   â””â”€â”€ vectors_3d_cache.json           # Cache Ä‘á»“ thá»‹ 3D cho Dashboard
â”‚   â”œâ”€â”€ raw/
â”‚   â”‚   â”œâ”€â”€ raw_crawled_news.jsonl          # Dá»¯ liá»‡u vÄƒn báº£n thÃ´
â”‚   â”‚   â””â”€â”€ RAW_DATASET_MANIFEST.json
```
*(Chi tiáº¿t thÃªm vui lÃ²ng xem file `data/README.md`)*

---

## 3. CÃ i Ä‘áº·t Dá»± Ã¡n

### BÆ°á»›c 1 â€” Clone vÃ  mÃ´i trÆ°á»ng

```bash
git clone git@github.com:rootkind35-del/HNSW-Combined-Quantization.git
cd HNSW-Combined-Quantization

# Táº¡o virtual environment
python -m venv .venv

# KÃ­ch hoáº¡t (Windows)
.venv\Scripts\activate
# KÃ­ch hoáº¡t (Linux/macOS)
source .venv/bin/activate
```

### BÆ°á»›c 2 â€” CÃ i Ä‘áº·t thÆ° viá»‡n Python

```bash
# CÃ i Ä‘áº·t cÆ¡ báº£n
pip install -e .

# CÃ i Ä‘áº·t thÃªm ML + dev tools
pip install -e ".[ml,dev]"
```

### BÆ°á»›c 3 â€” CÃ i Ä‘áº·t Node.js cho Dashboard

```bash
cd dashboard
npm install
cd ..
```

### BÆ°á»›c 4 â€” Kiá»ƒm tra cÃ i Ä‘áº·t

```bash
python -c "import numpy, sentence_transformers; print('Python OK')"
node -e "console.log('Node OK')"
```

---

## 4. Cháº¡y Dashboard Trá»±c quan

HÃ£y cháº¯c cháº¯n ráº±ng báº¡n Ä‘Ã£ lÃ m bÆ°á»›c **2. Táº£i Dá»¯ liá»‡u** vÃ  Ä‘áº·t chÃºng vÃ o thÆ° má»¥c `data/processed/`.

### Khá»Ÿi Ä‘á»™ng Server

```bash
# Má»Ÿ terminal 1 â€” Python search microservice
cd dashboard
python scripts/search_service.py
# Service cháº¡y trÃªn port 5005

# Má»Ÿ terminal 2 â€” Node.js dashboard server
cd dashboard
npm start
# Server cháº¡y trÃªn port 3000
```

Má»Ÿ trÃ¬nh duyá»‡t, truy cáº­p: **http://localhost:3000**

---

## 5. HÆ°á»›ng dáº«n Sá»­ dá»¥ng Tá»«ng Tab

### Tab 1 â€” TÃ¬m kiáº¿m & Execution Inspector

**Má»¥c Ä‘Ã­ch:** Nháº­p cÃ¢u truy váº¥n ngá»¯ nghÄ©a vÃ  xem káº¿t quáº£ tÃ¬m kiáº¿m cÃ¹ng vá»›i biá»ƒu Ä‘á»“ thá»±c thi 4 giai Ä‘oáº¡n.

**CÃ¡ch sá»­ dá»¥ng:**

1. Nháº­p vÄƒn báº£n vÃ o Ã´ tÃ¬m kiáº¿m (vÃ­ dá»¥: `há»£p Ä‘á»“ng lao Ä‘á»™ng tá»‘i thiá»ƒu`).
2. Chá»n thuáº­t toÃ¡n: `Two-Tier Quantized HNSW`, `Standard HNSW` hoáº·c `Distributed Collaborative Filtering`.
3. Chá»‰nh Top-K slider (5-20 káº¿t quáº£).
4. Chá»n chip danh má»¥c náº¿u muá»‘n lá»c.
5. Nháº¥n **TÃ¬m kiáº¿m** hoáº·c Enter.

**Giáº£i thÃ­ch káº¿t quáº£ hiá»ƒn thá»‹:**

| Pháº§n | MÃ´ táº£ |
|:---|:---|
| 4 KPI cards | Elapsed time, Slot time, Bytes shuffled, Bytes spilled |
| S00 â€” Input | Thá»i gian chuáº©n hÃ³a vÃ  nhÃºng vector |
| S01 â€” Aggregate | Thá»i gian duyá»‡t Ä‘á»“ thá»‹ SQ8 qua 200 shards |
| S02 â€” Re-rank | Thá»i gian Ä‘á»c SSD vÃ  tÃ­nh láº¡i khoáº£ng cÃ¡ch float32 |
| S03 â€” Output | Tá»•ng káº¿t quáº£ vÃ  thá»i gian phÃ¡t sinh response |
| Graph Output | Danh sÃ¡ch káº¿t quáº£ (List view / JSON view) |

**Chuyá»ƒn Ä‘á»•i dáº¡ng xem káº¿t quáº£:**

- Nháº¥n `[Dáº¡ng Danh SÃ¡ch]` Ä‘á»ƒ xem tháº» card.
- Nháº¥n `[Dáº¡ng JSON]` Ä‘á»ƒ xem raw JSON.
- Nháº¥n `Copy JSON` Ä‘á»ƒ sao chÃ©p vÃ o clipboard.

**Dynamic SQL:** Pháº§n SQL dÆ°á»›i thanh tÃ¬m kiáº¿m tá»± Ä‘á»™ng cáº­p nháº­t khi Ä‘á»•i tham sá»‘ â€” Ä‘Ã¢y lÃ  SQL mÃ´ phá»ng logic truy váº¥n Ä‘á»™ng.

---

### Tab 2 â€” KhÃ´ng gian Vector 3D (Three.js)

**Má»¥c Ä‘Ã­ch:** Trá»±c quan hÃ³a khÃ´ng gian vector nhÃºng 384-D Ä‘Æ°á»£c chiáº¿u xuá»‘ng 3 chiá»u qua PCA.

**CÃ¡ch sá»­ dá»¥ng:**

1. Thá»±c hiá»‡n tÃ¬m kiáº¿m á»Ÿ Tab 1 trÆ°á»›c.
2. Chuyá»ƒn sang Tab 2.
3. CÃ¡c Ä‘iá»ƒm káº¿t quáº£ tÃ¬m kiáº¿m Ä‘Æ°á»£c tÃ´ mÃ u vÃ ng/Ä‘á», cÃ¡c Ä‘iá»ƒm ná»n mÃ u xanh.
4. Di chuá»™t lÃªn Ä‘iá»ƒm báº¥t ká»³ Ä‘á»ƒ xem tooltip (tiÃªu Ä‘á», danh má»¥c, score, lÃ½ do).
5. Nháº¥n **Xem trÃªn 3D** trÃªn má»™t káº¿t quáº£ Ä‘á»ƒ focus vÃ o Ä‘iá»ƒm Ä‘Ã³.
6. Panel **HUD Detail** hiá»ƒn thá»‹ Ä‘áº§y Ä‘á»§ thÃ´ng tin tÃ i liá»‡u Ä‘Æ°á»£c chá»n.

**Äiá»u hÆ°á»›ng:**
- KÃ©o chuá»™t Ä‘á»ƒ xoay
- Scroll Ä‘á»ƒ phÃ³ng to/thu nhá»
- Click pháº£i + kÃ©o Ä‘á»ƒ dá»‹ch chuyá»ƒn

---

### Tab 3 â€” Danh sÃ¡ch Top-K

**Má»¥c Ä‘Ã­ch:** Xem báº£ng káº¿t quáº£ tÃ¬m kiáº¿m Ä‘áº§y Ä‘á»§ vá»›i xáº¿p háº¡ng rÃµ rÃ ng.

**Ná»™i dung hiá»ƒn thá»‹:**
- Thá»© tá»± xáº¿p háº¡ng (Rank #1 = Ä‘á»™ tÆ°Æ¡ng Ä‘á»“ng cao nháº¥t)
- Äá»™ tÆ°Æ¡ng Ä‘á»“ng (Similarity Score, thang 0-1)
- TiÃªu Ä‘á» tÃ i liá»‡u
- Äoáº¡n trÃ­ch dáº«n vÄƒn báº£n
- Danh má»¥c (News / Legal)
- LÃ½ do xáº¿p háº¡ng (Reasoning badge)

**LÆ°u Ã½:** Káº¿t quáº£ Ä‘Æ°á»£c sáº¯p xáº¿p giáº£m dáº§n theo `similarity_score`.

---

### Tab 4 â€” ÄÃ¡nh giÃ¡ Thuáº­t toÃ¡n

**Má»¥c Ä‘Ã­ch:** So sÃ¡nh Two-Tier Quantized HNSW vs Standard HNSW trÃªn cÃ¡c chá»‰ sá»‘ QPS, Recall, Latency.

**CÃ¡ch sá»­ dá»¥ng:**

1. Nháº¥n **Cháº¡y ÄÃ¡nh giÃ¡**.
2. Há»‡ thá»‘ng cháº¡y 100 cÃ¢u truy váº¥n máº«u trÃªn cáº£ 2 thuáº­t toÃ¡n.
3. Biá»ƒu Ä‘á»“ QPS, Latency, Recall hiá»ƒn thá»‹ so sÃ¡nh trá»±c tiáº¿p.
4. Biá»ƒu Ä‘á»“ HNSW SiÃªu tham sá»‘ cho phÃ©p thay Ä‘á»•i `M`, `ef_construction`, `ef_search` Ä‘á»ƒ xem áº£nh hÆ°á»Ÿng.

---

## 6. Cháº¡y ÄÃ¡nh giÃ¡ Thuáº­t toÃ¡n báº±ng CLI

NgoÃ i viá»‡c dÃ¹ng Dashboard, báº¡n cÃ³ thá»ƒ cháº¡y báº±ng dÃ²ng lá»‡nh:

```bash
# Cháº¡y Ä‘Ã¡nh giÃ¡ truy xuáº¥t trÃªn 2 thuáº­t toÃ¡n
python scripts/run_retrieval_evaluation.py --top-k 10

# Káº¿t quáº£ lÆ°u táº¡i:
#   data/processed/evaluation_results/benchmark_report_YYYYMMDD_HHMMSS.json
#   data/processed/evaluation_results/benchmark_summary_YYYYMMDD_HHMMSS.md
```

### Scale Stress Test (Chá»‹u táº£i)

```bash
# Kiá»ƒm tra hiá»‡u suáº¥t theo quy mÃ´ N = 1000, 2500, 5000
python scripts/run_scale_stress_test.py
```

---

## 7. Cháº¡y Pipeline Tá»« Äáº§u

Chá»‰ thá»±c hiá»‡n khi báº¡n muá»‘n lÃ m láº¡i toÃ n bá»™ quÃ¡ trÃ¬nh thu tháº­p vÃ  lÆ°á»£ng tá»­ hÃ³a:

```bash
# 1. Thu tháº­p dá»¯ liá»‡u bÃ¡o chÃ­ & phÃ¡p luáº­t
python scripts/run_crawler.py --target-records 100000 --batch-size 1000

# 2. LÆ°á»£ng tá»­ hÃ³a SQ8
python scripts/run_quantization.py

# 3. XÃ¢y dá»±ng bá»™ Ä‘á»‡m tÃ¬m kiáº¿m cho Dashboard
python scripts/build_clean_search_cache.py
```

---

## 8. Cáº¥u hÃ¬nh SiÃªu tham sá»‘

File cáº¥u hÃ¬nh: `configs/default_pipeline.json`

| Tham sá»‘ | Kiá»ƒu | Máº·c Ä‘á»‹nh | MÃ´ táº£ |
|:---|:---|:---:|:---|
| `dim` | int | 384 | Sá»‘ chiá»u vector (chuáº©n Sentence-BERT) |
| `max_elements` | int | 10,000,000 | Dung lÆ°á»£ng tá»‘i Ä‘a má»—i phÃ¢n vÃ¹ng index |
| `M` | int | 16 | Sá»‘ liÃªn káº¿t tá»‘i Ä‘a má»—i node trong HNSW |
| `ef_construction` | int | 100 | KÃ­ch thÆ°á»›c hÃ ng Ä‘á»£i á»©ng viÃªn khi xÃ¢y graph |
| `ef_search` | int | 32 | KÃ­ch thÆ°á»›c hÃ ng Ä‘á»£i á»©ng viÃªn khi truy váº¥n |
| `tau` | int | 3 | Sá»‘ bÆ°á»›c bÃ£o hÃ²a dá»«ng sá»›m (Adaptive Early-Exit) |
| `eps` | float | 0.0001 | NgÆ°á»¡ng cáº£i thiá»‡n tÆ°Æ¡ng Ä‘á»‘i Ä‘á»ƒ dá»«ng sá»›m |
| `rerank_factor` | int | 3 | Há»‡ sá»‘ nhÃ¢n sá»‘ lÆ°á»£ng á»©ng viÃªn Tier 2 |

---

## 9. Cháº¡y Bá»™ Kiá»ƒm thá»­

### Kiá»ƒm thá»­ Backend Python

```bash
# Cháº¡y toÃ n bá»™ 91 bÃ i kiá»ƒm thá»­ pytest
pytest tests/ -v
```

### Kiá»ƒm thá»­ Frontend UI

```bash
# Kiá»ƒm thá»­ render vÃ  logic UI (Node.js)
node tests/test_ui_render_harness.js
# Káº¿t quáº£: 19 passed, 0 failed

# Kiá»ƒm thá»­ adversarial stress
node tests/test_adversarial_frontend_stress.js
# Káº¿t quáº£: 3 adversarial cases, 0 findings
```

---

## 10. API Reference

Server Express cá»§a Dashboard cháº¡y trÃªn port 3000.

| Endpoint | Method | Body / Params | Chá»©c nÄƒng |
|:---|:---|:---|:---|
| `GET /api/status` | GET | â€” | Tráº¡ng thÃ¡i index, RAM usage, sá»‘ báº£n ghi |
| `POST /api/search` | POST | `{ query, algorithm, top_k, category }` | Thá»±c thi tÃ¬m kiáº¿m ngá»¯ nghÄ©a |
| `POST /api/eval/run` | POST | `{ top_k }` | Cháº¡y benchmark 2 thuáº­t toÃ¡n |
| `GET /api/eval/history` | GET | â€” | Danh sÃ¡ch cÃ¡c bÃ¡o cÃ¡o benchmark Ä‘Ã£ cháº¡y |
| `GET /api/eval/download/:type/:file` | GET | type=report/query, file=filename | Táº£i JSON/Markdown report |

### VÃ­ dá»¥ gá»i API tÃ¬m kiáº¿m

```bash
curl -X POST http://localhost:3000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "há»£p Ä‘á»“ng lao Ä‘á»™ng tá»‘i thiá»ƒu", "algorithm": "two_tier", "top_k": 5}'
```

---

## 11. Xá»­ lÃ½ Sá»± cá»‘ ThÆ°á»ng gáº·p

### Lá»—i káº¿t ná»‘i `Python service not responding`

**NguyÃªn nhÃ¢n:** Python microservice (port 5005) chÆ°a cháº¡y.

**CÃ¡ch xá»­ lÃ½:**
```bash
cd dashboard
python scripts/search_service.py
```

---

### Lá»—i `Cannot find module` khi cháº¡y Node

**NguyÃªn nhÃ¢n:** Báº¡n chÆ°a cÃ i Ä‘áº·t package cho thÆ° má»¥c dashboard.

**CÃ¡ch xá»­ lÃ½:**
```bash
cd dashboard
npm install
```

---

### Lá»—i `ModuleNotFoundError` trong Python

**CÃ¡ch xá»­ lÃ½:** Äáº£m báº£o báº¡n Ä‘Ã£ cÃ i toÃ n bá»™ mÃ´i trÆ°á»ng áº£o.
```bash
pip install -e ".[ml,dev]"
```

---

### Biá»ƒu Ä‘á»“ 3D khÃ´ng hiá»ƒn thá»‹

**NguyÃªn nhÃ¢n:** TrÃ¬nh duyá»‡t khÃ´ng há»— trá»£ WebGL hoáº·c GPU bá»‹ vÃ´ hiá»‡u hÃ³a.

**CÃ¡ch xá»­ lÃ½:**
- Thá»­ trÃ¬nh duyá»‡t khÃ¡c (Chrome/Edge phiÃªn báº£n má»›i nháº¥t).
- Báº­t `Override software rendering list` trong `chrome://flags`.

---

### Out-Of-Memory khi cháº¡y Standard HNSW

**ÄÃ¢y lÃ  Ä‘iá»u bÃ¬nh thÆ°á»ng** vá»›i táº­p 16.45M vector. Standard HNSW cáº§n tá»›i ~64 GB RAM. HÃ£y chuyá»ƒn sang sá»­ dá»¥ng `Two-Tier Quantized HNSW` Ä‘á»ƒ tiáº¿t kiá»‡m 75% RAM.

