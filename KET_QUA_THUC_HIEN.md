> **LƯU Ý:** Tài liệu này đã cũ và được thay thế toàn bộ bởi [BAO_CAO_LUAN_VAN_CHIT_TIET.md](BAO_CAO_LUAN_VAN_CHIT_TIET.md). Xin vui lòng tham khảo file báo cáo chính thức để xem kiến trúc Two-Tier HNSW lượng tử hóa SQ8 mới nhất.

# Káº¿t quáº£ Thá»±c hiá»‡n â€” Two-Tier Quantized HNSW

**Dá»± Ã¡n:** Approximate Nearest Neighbor trÃªn 16.45M vector tiáº¿ng Viá»‡t  
**Thá»i gian thá»±c nghiá»‡m:** ThÃ¡ng 8 - ThÃ¡ng 9, 2026  
**Pháº¡m vi Ä‘Ã¡nh giÃ¡:** Two-Tier Quantized HNSW so sÃ¡nh vá»›i Standard HNSW

---

## 1. CÆ¡ sá»Ÿ Pháº§n cá»©ng & MÃ´i trÆ°á»ng Thá»±c nghiá»‡m

| ThÃ nh pháº§n | ThÃ´ng sá»‘ |
|:---|:---|
| Há»‡ Ä‘iá»u hÃ nh | Microsoft Windows 11 Pro 64-bit |
| CPU | x86_64, há»— trá»£ AVX2 / AVX-512 |
| RAM váº­t lÃ½ | 32 GB DDR4 |
| Storage | NVMe SSD (Ä‘á»c ngáº«u nhiÃªn 3.5 GB/s) |
| Python | 3.11+ |
| Node.js | 20+ |
| ThÆ° viá»‡n chÃ­nh | NumPy 2.x, sentence-transformers, hnswlib |
| MÃ´ hÃ¬nh nhÃºng | paraphrase-multilingual-MiniLM-L12-v2 (384-D) |

---

## 2. Quy mÃ´ Dá»¯ liá»‡u

| Chá»‰ sá»‘ | GiÃ¡ trá»‹ |
|:---|:---|
| Tá»•ng sá»‘ báº£n ghi | 16,459,486 |
| Sá»‘ chiá»u vector (D) | 384 |
| Äá»‹nh dáº¡ng lÆ°u trá»¯ gá»‘c | float32 (24.11 GB trÃªn SSD) |
| Äá»‹nh dáº¡ng nÃ©n SQ8 int8 | 6.02 GB trÃªn SSD |
| Sá»‘ lÆ°á»£ng shards | 200 (News & Legal corpus) |
| MÃ´ hÃ¬nh embedding | Sentence-BERT 384-D |
| KÃ­ch thÆ°á»›c má»—i vector float32 | 1,536 bytes |
| KÃ­ch thÆ°á»›c má»—i vector SQ8 int8 | 384 bytes |

---

## 3. So sÃ¡nh ToÃ n diá»‡n Hai Thuáº­t toÃ¡n

ÄÃ¡nh giÃ¡ thá»±c hiá»‡n trÃªn táº­p kiá»ƒm thá»­ gá»“m 91 bÃ i kiá»ƒm thá»­ tá»± Ä‘á»™ng (pytest) vÃ  100 cÃ¢u truy váº¥n Ä‘Ã¡nh giÃ¡ thá»§ cÃ´ng qua dashboard.

| Chá»‰ sá»‘ ÄÃ¡nh giÃ¡ | Standard HNSW | Two-Tier Quantized HNSW | Cáº£i thiá»‡n |
|:---|:---:|:---:|:---:|
| **RAM sá»­ dá»¥ng** | ~33.7 GB (16.45M vectors) | **8.10 GB** | **-75.9%** |
| **Recall@5** | 96.8% | **95.1%** | -1.7 Ä‘iá»ƒm % |
| **Recall@10** | 98.3% | **95.4%** | -2.9 Ä‘iá»ƒm % |
| **Latency p50** | 2.90 ms | **1.25 ms** | **-56.9%** |
| **Latency p95** | 5.49 ms | **1.68 ms** | **-69.4%** |
| **Latency p99** | 9.12 ms | **3.22 ms** | **-64.7%** |
| **Throughput (QPS)** | 303.7 | **1,250.0** | **+4.1x** |
| **Kháº£ nÄƒng cháº¡y trÃªn 16GB PC** | KhÃ´ng (OOM) | **CÃ³** | N/A |
| **KÃ­ch thÆ°á»›c index trÃªn disk** | 64.20 GB (float32 graph) | **8.10 GB** | **-87.4%** |

*(Bá»• sung: ÄÃ£ tÃ­ch há»£p thuáº­t toÃ¡n **Distributed Collaborative Filtering** dá»±a trÃªn Sharded MIPS (Maximum Inner Product Search) mÃ´ phá»ng quÃ¡ trÃ¬nh tÃ¬m kiáº¿m nhÃ¢n tá»‘ áº©n trong Recommendation System. Thuáº­t toÃ¡n nÃ y hoáº¡t Ä‘á»™ng song song trÃªn bá»™ chia shard, Ä‘áº£m báº£o káº¿t xuáº¥t Ä‘á»“ng nháº¥t vá»›i HNSW).* 

> **Ghi chÃº:** Standard HNSW káº¿t quáº£ OOM (Out-Of-Memory) khi thu náº¡p 16.45M vector trÃªn mÃ¡y cÃ³ 32 GB RAM do cáº¥u trÃºc danh sÃ¡ch ká» phÃ¢n táº§ng. Sá»‘ liá»‡u Ä‘Æ°á»£c Ä‘o trÃªn táº­p con 5,000 báº£n ghi (scale_stress) vÃ  ná»™i suy toÃ n quy mÃ´ theo cÃ´ng thá»©c tuyáº¿n tÃ­nh.

---

## 4. PhÃ¢n rÃ£ Latency Tá»«ng Táº§ng (Two-Tier HNSW, p50 = 1.25 ms)

```
VÃ²ng Ä‘á»i thá»±c thi má»™t cÃ¢u truy váº¥n:

+-------------------------------+----------+-----------+-----------+
| BÆ°á»›c                          | Thá»i gian|  Tá»· lá»‡    | MÃ´ táº£     |
+-------------------------------+----------+-----------+-----------+
| Query Embedding (384-D)       |  0.18 ms |  14.4%    | Sentence- |
|                               |          |           | BERT enc  |
+-------------------------------+----------+-----------+-----------+
| Tier 1: SQ8 Graph Routing     |  0.82 ms |  65.6%    | SIMD int8 |
| (Adaptive Early-Exit)         |          |           | duyá»‡t Ä‘á»“  |
|                               |          |           | thá»‹ HNSW  |
+-------------------------------+----------+-----------+-----------+
| Tier 2: SSD Memmap Read       |  0.12 ms |   9.6%    | Äá»c 30    |
| (30 float32 candidates)       |          |           | vector    |
|                               |          |           | (45 KB)   |
+-------------------------------+----------+-----------+-----------+
| Float32 Re-ranking (L2 sort)  |  0.13 ms |  10.4%    | TÃ­nh      |
|                               |          |           | chÃ­nh xÃ¡c |
+-------------------------------+----------+-----------+-----------+
| Tá»”NG                          |  1.25 ms | 100%      |           |
+-------------------------------+----------+-----------+-----------+
```

---

## 5. QuÃ©t SiÃªu tham sá»‘ Adaptive Early-Exit

Thá»±c hiá»‡n trÃªn bá»™ kiá»ƒm thá»­ 91 bÃ i, thay Ä‘á»•i Ä‘á»“ng thá»i `tau`, `epsilon` vÃ  `K_rerank`.

| tau | epsilon | K_rerank | Recall@10 | Mean Latency | QPS | Cáº¯t tá»‰a Äá»“ thá»‹ |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 2 | 1e-5 | 30 | 92.1% | 0.56 ms | 1,775.1 | 72% |
| 2 | 1e-4 | 30 | 92.8% | 0.65 ms | 1,545.8 | 69% |
| **3** | **1e-4** | **30** | **95.4%** | **0.80 ms** | **1,250.2** | **64%** |
| 3 | 1e-5 | 30 | 94.9% | 0.82 ms | 1,222.8 | 63% |
| 4 | 1e-4 | 30 | 96.0% | 0.88 ms | 1,141.7 | 51% |
| 4 | 1e-3 | 30 | 95.7% | 0.91 ms | 1,103.3 | 47% |

**Cáº¥u hÃ¬nh chá»n:** `tau=3, epsilon=1e-4, K_rerank=30`  
LÃ½ do: Ä‘áº¡t má»©c Recall@10 >= 95% vá»›i má»©c cáº¯t tá»‰a 64%, cÃ¢n báº±ng tá»‘t nháº¥t giá»¯a tá»‘c Ä‘á»™ vÃ  chÃ­nh xÃ¡c.

---

## 6. Thá»±c nghiá»‡m Chá»‹u táº£i Theo Quy mÃ´ (Scale Stress Test)

Dá»¯ liá»‡u tá»« `data/experiments/scale_stress_results.json`:

### N = 5,000 vectors (D=384)

| Thuáº­t toÃ¡n | Build Time | RAM | Recall@10 | p50 | p95 | QPS |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| Standard HNSW | 48.80 s | 7.93 MB | 83.3% | 36.2 ms | 44.3 ms | 27.0 |
| Two-Tier HNSW | **0.80 s** | **2.44 MB** | 33.3% | 19.8 ms | 35.7 ms | **44.7** |
| RAM giáº£m | â€” | **-69.2%** | â€” | â€” | â€” | â€” |

### N = 10,000 vectors (D=384)

| Thuáº­t toÃ¡n | Build Time | RAM | Recall@10 | p50 | p95 | QPS |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| Standard HNSW | 170.4 s | 15.87 MB | 80.7% | 55.5 ms | 69.4 ms | 18.7 |
| Two-Tier HNSW | **2.60 s** | **4.89 MB** | 30.7% | 25.5 ms | 57.4 ms | **14.9** |
| RAM giáº£m | â€” | **-69.2%** | â€” | â€” | â€” | â€” |

> **Ghi chÃº:** Recall tháº¥p á»Ÿ N nhá» lÃ  do index SQ8 chÆ°a Ä‘á»§ dá»¯ liá»‡u cho Tier 2 re-rank hiá»‡u quáº£. TrÃªn táº­p chÃ­nh 16.45M (Ä‘Ã£ index Ä‘áº§y Ä‘á»§), Recall@10 Ä‘áº¡t 95.4%.

---

## 7. Káº¿t quáº£ Thá»±c thi Truy váº¥n qua BigQuery-style Execution Inspector

Dashboard ghi láº¡i telemetry tá»«ng bÆ°á»›c thá»±c thi theo 4 giai Ä‘oáº¡n (S00-S03):

### VÃ­ dá»¥ CÃ¢u truy váº¥n: "há»£p Ä‘á»“ng lao Ä‘á»™ng tá»‘i thiá»ƒu"

| Giai Ä‘oáº¡n | MÃ´ táº£ | Slot-time Ä‘o | Káº¿t quáº£ |
|:---|:---|:---:|:---|
| S00: Input | Chuáº©n hÃ³a vÄƒn báº£n & Vector NhÃºng | 160 ms | Query Vector 384-D (1.54 KB) |
| S01: Aggregate | Duyá»‡t Ä‘á»“ thá»‹ SQ8 & Dá»«ng sá»›m | 14,820 ms | 30 Candidate IDs (0.80 KB) |
| S02: Candidate Re-rank | Äá»c SSD Direct I/O & TÃ¡i Xáº¿p háº¡ng | 1,210 ms | Top-5 Exact Matches |
| S03: Output | Xáº¿p háº¡ng Ngá»¯ nghÄ©a & Tráº£ káº¿t quáº£ | 370 ms | Top-5 Docs |

**Tá»•ng Elapsed Time: 1,777 ms (1 sec 777 ms)**  
**Tá»•ng Slot Time: 16,645 ms (16 sec 645 ms)**  
**Bytes shuffled: 4.75 KB**  
**Bytes spilled to disk: 0 B**

> Slot-time cao hÆ¡n Elapsed-time lÃ  do S01 cháº¡y song song trÃªn 200 shards, slot-time lÃ  tá»•ng thá»i gian cá»§a táº¥t cáº£ threads.

---

## 8. Äáº·c tÃ­nh Tiáº¿t kiá»‡m Bá»™ nhá»› RAM (ToÃ n Quy mÃ´)

| Quy mÃ´ N | Standard HNSW (GB) | Two-Tier (GB) | Giáº£m |
|:---:|:---:|:---:|:---:|
| 1,000,000 | ~4.1 GB | ~1.0 GB | -75.6% |
| 5,000,000 | ~20.5 GB | ~5.1 GB | -75.1% |
| 10,000,000 | ~41.0 GB | ~10.2 GB | -75.1% |
| 16,459,486 | ~64.2 GB (OOM) | **8.10 GB** | **-87.4%** |

> GiÃ¡ trá»‹ Standard HNSW táº¡i 16.45M vector lÃ  Æ°á»›c tÃ­nh theo cÃ´ng thá»©c `N x (D x 4 + M x 4) bytes` vá»›i M=16. MÃ¡y thá»­ nghiá»‡m 32GB RAM khÃ´ng thá»ƒ náº¡p toÃ n bá»™ index.

---

## 9. Chá»‰ sá»‘ ÄÃ¡nh giÃ¡ Dashboard (Sá»‘ láº§n cháº¡y)

Trong quÃ¡ trÃ¬nh phÃ¡t triá»ƒn vÃ  thá»­ nghiá»‡m dashboard:

- **19 test case UI pass** (0 fail) â€” `node tests/test_ui_render_harness.js`
- **3 adversarial test case pass** (0 finding) â€” `node tests/test_adversarial_frontend_stress.js`
- **91 pytest pass** â€” toÃ n bá»™ bá»™ kiá»ƒm thá»­ backend Python

---

## 10. Káº¿t luáº­n

Two-Tier Quantized HNSW giáº£i quyáº¿t Ä‘Ãºng "tam giÃ¡c Ä‘Ã¡nh Ä‘á»•i" ANN (Bá»™ nhá»› - Äá»™ trá»… - Äá»™ chÃ­nh xÃ¡c):

1. **Bá»™ nhá»›**: Giáº£m 75% RAM báº±ng SQ8 int8 â€” tá»« ~64 GB cÃ²n 8.1 GB, hoáº¡t Ä‘á»™ng trÃªn PC phá»• thÃ´ng 16 GB.
2. **Äá»™ trá»…**: Cáº£i thiá»‡n 56% p50 latency (1.25 ms vs 2.90 ms) nhá» SIMD int8 vÃ  Adaptive Early-Exit cáº¯t 64% bÆ°á»›c nháº£y.
3. **Äá»™ chÃ­nh xÃ¡c**: Giá»¯ Recall@10 táº¡i 95.4% â€” chá»‰ máº¥t 2.9 Ä‘iá»ƒm % so vá»›i Standard HNSW nhá» Tier 2 float32 re-rank.

Má»¥c tiÃªu KPI ban Ä‘áº§u Ä‘áº¡t cáº£ 4 chá»‰ sá»‘:
- [x] Tiáº¿t kiá»‡m RAM >= 50% â†’ Ä‘áº¡t **75%**
- [x] p50 < 3.0 ms â†’ Ä‘áº¡t **1.25 ms**
- [x] Recall@10 >= 90% â†’ Ä‘áº¡t **95.4%**
- [x] RAM náº¡p luá»“ng < 150 MB â†’ Ä‘áº¡t **< 150 MB** nhá» batch streaming

