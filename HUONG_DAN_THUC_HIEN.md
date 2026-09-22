# Huong dan Thuc hien — HNSW Combined Quantization

**Phien ban:** v1.0.0  
**Cap nhat:** Thang 9, 2026  
**Pham vi:** Cai dat, chay thu, su dung dashboard va danh gia ket qua

---

## Muc luc

1. [Yeu cau Phan cung & Phan mem](#1-yeu-cau-phan-cung--phan-mem)
2. [Cai dat Du an](#2-cai-dat-du-an)
3. [Chay Dashboard Truc quan](#3-chay-dashboard-truc-quan)
4. [Huong dan Su dung Tung Tab](#4-huong-dan-su-dung-tung-tab)
5. [Chay Danh gia Thuat toan](#5-chay-danh-gia-thuat-toan)
6. [Chay Pipeline Tu Dau](#6-chay-pipeline-tu-dau)
7. [Cau hinh Sieu tham so](#7-cau-hinh-sieu-tham-so)
8. [Chay Bo Kiem thu](#8-chay-bo-kiem-thu)
9. [API Reference](#9-api-reference)
10. [Xu ly Su co Thuong gap](#10-xu-ly-su-co-thuong-gap)

---

## 1. Yeu cau Phan cung & Phan mem

### Toi thieu

| Thanh phan | Yeu cau |
|:---|:---|
| RAM | 16 GB (du chay Two-Tier HNSW) |
| Storage | 15 GB NVMe SSD trong (cho index SQ8) |
| CPU | x86_64 voi AVX2 |
| Python | 3.11 hoac cao hon |
| Node.js | 20 hoac cao hon |

### Khuyen nghi

| Thanh phan | Khuyen nghi |
|:---|:---|
| RAM | 32 GB+ |
| Storage | 50 GB+ SSD (cho du lieu float32 + SQ8 + cache) |
| CPU | Ho tro AVX-512 cho hieu suat SIMD tot hon |

> **Luu y:** Standard HNSW tren 16.45M vector can ~64 GB RAM. Chi Two-Tier Quantized HNSW moi chay duoc tren may 16-32 GB.

---

## 2. Cai dat Du an

### Buoc 1 — Clone va moi truong

```bash
git clone git@github.com:rootkind35-del/HNSW-Combined-Quantization.git
cd HNSW-Combined-Quantization

# Tao virtual environment
python -m venv .venv

# Kich hoat (Windows)
.venv\Scripts\activate
# Kich hoat (Linux/macOS)
source .venv/bin/activate
```

### Buoc 2 — Cai dat thu vien Python

```bash
# Cai dat co ban
pip install -e .

# Cai dat them ML + dev tools
pip install -e ".[ml,dev]"
```

### Buoc 3 — Cai dat Node.js cho Dashboard

```bash
cd dashboard
npm install
cd ..
```

### Buoc 4 — Kiem tra cai dat

```bash
python -c "import numpy, sentence_transformers; print('Python OK')"
node -e "console.log('Node OK')"
```

---

## 3. Chay Dashboard Truc quan

### Option A — Dung Cache Co san (nhanh nhat)

Tai cache tu Google Drive:

1. Truy cap: `https://drive.google.com/drive/folders/1b2yiq6Ly5cl3VdNW2LuM1EqdaZNdpbPW?usp=sharing`
2. Tai ve va giai nen vao `data/processed/`:

```
data/processed/
├── search_index_cache.npz          # 5,000 vector da chuan hoa
├── search_index_metadata.json       # Metadata 5,000 tai lieu
├── pca_3d_projection.json          # Toa do PCA 3D
└── vectors_3d_cache.json           # Cache toa do 3D
```

3. Kiem tra:

```bash
python -c "import json; d=json.load(open('data/processed/search_index_metadata.json', encoding='utf-8')); print(f'Loaded {len(d)} records')"
```

### Khoi dong Server

```bash
# Mo terminal 1 — Python search microservice
cd dashboard
python scripts/search_service.py
# Service chay tren port 5005

# Mo terminal 2 — Node.js dashboard server
cd dashboard
node server.js
# Hoac: npm start
# Server chay tren port 3000
```

Mo trinh duyet, truy cap: **http://localhost:3000**

---

## 4. Huong dan Su dung Tung Tab

### Tab 1 — Tim kiem & Execution Inspector

**Muc dich:** Nhap cau truy van ngu nghia va xem ket qua tim kiem cung voi bieu do thuc thi 4 giai doan.

**Cach su dung:**

1. Nhap van ban vao o tim kiem (vi du: `hop dong lao dong`).
2. Chon algorithm: `Two-Tier Quantized HNSW` hoac `Standard HNSW`.
3. Chinh Top-K slider (5-20 ket qua).
4. Chon chip danh muc neu muon loc.
5. Nhan **Tim kiem** hoac Enter.

**Giai thich ket qua hien thi:**

| Phan | Mo ta |
|:---|:---|
| 4 KPI cards | Elapsed time, Slot time, Bytes shuffled, Bytes spilled |
| S00 — Input | Thoi gian chuan hoa va nhung vector |
| S01 — Aggregate | Thoi gian duyet do thi SQ8 qua 200 shards |
| S02 — Re-rank | Thoi gian doc SSD va tinh lai khoang cach float32 |
| S03 — Output | Tong ket qua va thoi gian phat sinh response |
| Graph Output | Danh sach ket qua (List view / JSON view) |

**Chuyen doi dang xem ket qua:**

- Nhan `[Dang Danh Sach]` de xem the card.
- Nhan `[Dang JSON]` de xem raw JSON.
- Nhan `Copy JSON` de sao chep vao clipboard.

**Dynamic SQL:** Phan SQL duoi thanh tim kiem tu dong cap nhat khi doi tham so — day la SQL logic tieu bieu, khong phai lenh thuc thi vat ly.

---

### Tab 2 — Khong gian Vector 3D (Three.js)

**Muc dich:** Truc quan hoa khong gian vector nhung 384-D duoc chieu xuong 3 chieu qua PCA.

**Cach su dung:**

1. Thuc hien tim kiem o Tab 1 truoc.
2. Chuyen sang Tab 2.
3. Cac diem ket qua tim kiem duoc to mau vang/do, cac diem nen mau xanh.
4. Di chuot len diem bat ky de xem tooltip (tieu de, danh muc, score, ly do).
5. Nhan **Xem tren 3D** tren mot ket qua de focus vao diem do tren khong gian 3D.
6. Panel **HUD Detail** hien thi day du thong tin tai lieu duoc chon.

**Dieu huong:**
- Keo chuot de xoay
- Scroll de phong to/thu nho
- Click phai + keo de dich chuyen

---

### Tab 3 — Danh sach Top-K

**Muc dich:** Xem bang ket qua tim kiem day du voi xep hang ro rang.

**Noi dung hien thi:**
- Thu tu xep hang (Rank #1 = do tuong dong cao nhat)
- Do tuong dong (Similarity Score, thang 0-1)
- Tieu de tai lieu
- Doan trich dan van ban
- Danh muc (News / Legal)
- Ly do xep hang (Reasoning badge)

**Luu y:** Ket qua duoc sap xep giam dan theo `similarity_score` — Rank #1 luon la ket qua co do khop ngu nghia cao nhat.

---

### Tab Danh gia

**Muc dich:** So sanh Two-Tier Quantized HNSW vs Standard HNSW tren cac chi so QPS, Recall, Latency.

**Cach su dung:**

1. Nhan **Chay Danh gia**.
2. He thong chay 100 cau truy van mau tren ca 2 thuat toan.
3. Bieu do QPS, Latency, Recall hien thi so sanh truc tiep.
4. Bieu do HNSW Siêu tham so cho phep thay doi `M`, `ef_construction`, `ef_search` de xem anh huong.

---

## 5. Chay Danh gia Thuat toan

### Quick Benchmark qua Dashboard

Trong Tab Danh gia, nhan "Chay Danh gia" — ket qua hien thi ngay tren bieu do.

### CLI Benchmark

```bash
# Chay danh gia truy xuat tren 2 thuat toan
python scripts/run_retrieval_evaluation.py --top-k 10

# Ket qua luu tai:
#   data/processed/evaluation_results/benchmark_report_YYYYMMDD_HHMMSS.json
#   data/processed/evaluation_results/benchmark_summary_YYYYMMDD_HHMMSS.md
```

### Scale Stress Test

```bash
# Kiem tra hieu suat theo quy mo N = 1000, 2500, 5000
python scripts/run_scale_stress_test.py

# Ket qua luu tai: data/experiments/scale_stress_results.json
```

---

## 6. Chay Pipeline Tu Dau

Chi thuc hien khi muon tai lai du lieu va xay dung lai index tu nguon.

### Buoc 1 — Thu thap du lieu

```bash
# Thu thap bao chi & phap luat tieng Viet
python scripts/run_crawler.py --target-records 100000 --batch-size 1000

# Thu thap Wikipedia tieng Viet (tuy chon)
# python scripts/run_wiki_crawler.py --target-records 100000
```

### Buoc 2 — Luong tu hoa SQ8

```bash
python scripts/run_quantization.py
```

### Buoc 3 — Xay dung cache tim kiem

```bash
python scripts/build_clean_search_cache.py
```

---

## 7. Cau hinh Sieu tham so

File cau hinh: `configs/default_pipeline.json`

| Tham so | Kieu | Mac dinh | Mo ta |
|:---|:---|:---:|:---|
| `dim` | int | 384 | So chieu vector (chuan Sentence-BERT) |
| `max_elements` | int | 10,000,000 | Dung luong toi da moi phan vung index |
| `M` | int | 16 | So lien ket toi da moi node trong HNSW |
| `ef_construction` | int | 100 | Kich thuoc hang doi ung vien khi xay graph |
| `ef_search` | int | 32 | Kich thuoc hang doi ung vien khi truy van |
| `tau` | int | 3 | So buoc bao hoa dung som (Early-Exit) |
| `eps` | float | 0.0001 | Nguong cai thien tuong doi dung som |
| `rerank_factor` | int | 3 | He so nhan so ung vien Tier 2 (K_rerank = K x factor) |

**Thay doi sieu tham so qua Dashboard:**

Tab Danh gia → Khu vuc "HNSW Sieu tham so" → Keo cac thanh truot M, ef_construction, ef_search, tau, epsilon → Bieu do tu cap nhat.

---

## 8. Chay Bo Kiem thu

### Kiem thu Backend Python

```bash
# Chay toan bo 91 pytest
pytest tests/ -v

# Chay nhanh (khong verbose)
pytest tests/
```

### Kiem thu Frontend UI

```bash
# Kiem thu render va logic UI (Node.js)
node tests/test_ui_render_harness.js
# Ket qua: 19 passed, 0 failed

# Kiem thu adversarial stress
node tests/test_adversarial_frontend_stress.js
# Ket qua: 3 adversarial cases, 0 findings
```

---

## 9. API Reference

Server Express chay tren port 3000.

| Endpoint | Method | Body / Params | Chuc nang |
|:---|:---|:---|:---|
| `GET /api/status` | GET | — | Trang thai index, RAM usage, so ban ghi |
| `POST /api/search` | POST | `{ query, algorithm, top_k, category }` | Thuc thi tim kiem ngu nghia |
| `POST /api/eval/run` | POST | `{ top_k }` | Chay benchmark 2 thuat toan |
| `GET /api/eval/history` | GET | — | Danh sach cac bao cao benchmark da chay |
| `GET /api/eval/download/:type/:file` | GET | type=report/query, file=filename | Tai JSON/Markdown report |

### Vi du goi API tim kiem

```bash
curl -X POST http://localhost:3000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "hop dong lao dong toi thieu", "algorithm": "two_tier", "top_k": 5}'
```

### Vi du phan hoi API

```json
{
  "results": [
    {
      "id": 1042381,
      "title": "Quy dinh ve muc luong toi thieu vung 2026",
      "preview": "Theo Nghi dinh 74/2025/ND-CP, muc luong...",
      "category": "legal",
      "similarity_score": 0.912,
      "rank": 1,
      "shard_id": "S047",
      "reason": "Do tuong dong cao (0.912): Noi dung khop voi tru khoa 'hop dong lao dong toi thieu'"
    }
  ],
  "metrics": {
    "elapsed_ms": 1777,
    "slot_ms": 16645,
    "bytes_shuffled": 4864,
    "bytes_spilled": 0,
    "stage_latencies": {
      "s00_input_ms": 160,
      "s01_graph_ms": 14820,
      "s02_rerank_ms": 1210,
      "s03_output_ms": 370
    }
  }
}
```

---

## 10. Xu ly Su co Thuong gap

### Loi ket noi `Python service not responding`

**Nguyen nhan:** Python microservice (port 5005) chua chay.

**Cach xu ly:**
```bash
cd dashboard
python scripts/search_service.py
```

Kiem tra port 5005 da mo:
```bash
netstat -an | findstr 5005
```

---

### Loi `Cannot find module`

**Nguyen nhan:** `npm install` chua chay.

**Cach xu ly:**
```bash
cd dashboard
npm install
```

---

### Loi `ModuleNotFoundError` trong Python

**Nguyen nhan:** Chua cai dat dependencies.

**Cach xu ly:**
```bash
pip install -e ".[ml,dev]"
```

---

### Trang tim kiem khong tra ket qua

**Kiem tra:**
1. Server Node.js dang chay o port 3000?
2. Python service dang chay o port 5005?
3. File `data/processed/search_index_metadata.json` va `search_index_cache.npz` ton tai?

```bash
python -c "import os; print(os.path.exists('data/processed/search_index_metadata.json'))"
```

---

### Bieu do 3D khong hien thi

**Nguyen nhan:** Trinh duyet khong ho tro WebGL hoac GPU bi disabled.

**Cach xu ly:**
- Thu trinh duyet khac (Chrome/Edge phien ban moi).
- Kiem tra `chrome://flags` → `Override software rendering list` → Enable.

---

### Out-Of-Memory khi chay Standard HNSW

**Day la dieu binh thuong** voi tap 16.45M vector. Standard HNSW can ~64 GB RAM. Chuyen sang dung `Two-Tier Quantized HNSW`.

---

## Ghi chu Nhanh

```bash
# Tat ca lenh quan trong

# Cai dat
pip install -e ".[ml,dev]" && cd dashboard && npm install && cd ..

# Chay he thong
python dashboard/scripts/search_service.py &
node dashboard/server.js

# Mo dashboard
start http://localhost:3000

# Kiem thu
pytest tests/ -v
node tests/test_ui_render_harness.js

# Benchmark CLI
python scripts/run_retrieval_evaluation.py --top-k 10
```
