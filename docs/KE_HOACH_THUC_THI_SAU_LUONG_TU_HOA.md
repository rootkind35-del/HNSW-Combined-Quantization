> **LƯU Ý:** Tài liệu này đã cũ và được thay thế toàn bộ bởi [BAO_CAO_LUAN_VAN_CHIT_TIET.md](BAO_CAO_LUAN_VAN_CHIT_TIET.md). Xin vui lòng tham khảo file báo cáo chính thức để xem kiến trúc Two-Tier HNSW lượng tử hóa SQ8 mới nhất.

# Káº¿ hoáº¡ch Ká»¹ thuáº­t ToÃ n diá»‡n: CÃ¡c BÆ°á»›c Thá»±c thi Sau khi HoÃ n táº¥t LÆ°á»£ng tá»­ hÃ³a (Post-Quantization Master Plan)

TÃ i liá»‡u nÃ y xÃ¡c Ä‘á»‹nh toÃ n bá»™ cÃ¡c giai Ä‘oáº¡n cÃ´ng viá»‡c, cáº¥u trÃºc mÃ£ nguá»“n, báº£n cháº¥t toÃ¡n há»c, quy Æ°á»›c Ä‘áº·t tÃªn vÃ  bá»™ khung phÃ¢n tÃ­ch káº¿t quáº£ thá»±c nghiá»‡m Ä‘Æ°á»£c tiáº¿n hÃ nh ngay sau khi quÃ¡ trÃ¬nh lÆ°á»£ng tá»­ hÃ³a hoÃ n táº¥t. Trá»ng tÃ¢m tÃ i liá»‡u táº­p trung vÃ o thuáº­t toÃ¡n Ä‘á» xuáº¥t Two-Tier Quantized HNSW, giáº£i thÃ­ch báº£n cháº¥t ká»¹ thuáº­t vÃ  nguyÃªn nhÃ¢n toÃ¡n há»c Ä‘áº±ng sau sá»± cáº£i thiá»‡n hiá»‡u nÄƒng.

---

## 1. Bá»‘i cáº£nh vÃ  Má»¥c tiÃªu Chiáº¿n lÆ°á»£c

Há»‡ thá»‘ng sá»Ÿ há»¯u kho dá»¯ liá»‡u lá»›n sau lÆ°á»£ng tá»­ hÃ³a:
1. **Kho 1 (BÃ¡o chÃ­ & PhÃ¡p luáº­t):** 10.000.000 báº£n ghi thÃ´ $\to$ 16.459.486 vector `int8` táº¡i `data/quantized/`.

Giai Ä‘oáº¡n tiáº¿p theo giáº£i quyáº¿t bÃ i toÃ¡n cá»‘t lÃµi cá»§a Ä‘á» tÃ i:
1. Há»£p nháº¥t hai kho vector vá»›i kiáº¿n trÃºc quáº£n lÃ½ Ä‘Ä©a an toÃ n, trÃ¡nh trÃ¹ng láº·p dá»¯ liá»‡u vÃ  chá»‘ng trÃ n á»• Ä‘Ä©a SSD.
2. XÃ¢y dá»±ng Ä‘á»“ thá»‹ chá»‰ má»¥c Two-Tier HNSW trÃªn quy mÃ´ 16.45 triá»‡u vector.
3. Äo kiá»ƒm Ä‘á»‘i chuáº©n toÃ n diá»‡n 4 thuáº­t toÃ¡n (`FlatIndex`, `StandardHNSWIndex`, `IVFPQIndex`, `TwoTierQuantizedHNSW`) qua 6 má»‘c quy mÃ´ (100K $\to$ 16.45M).
4. Thiáº¿t láº­p bá»™ khung Ä‘Ã¡nh giÃ¡ chuyÃªn sÃ¢u vÃ  phÃ¢n tÃ­ch nguyÃªn nhÃ¢n ká»¹ thuáº­t táº¡o nÃªn bÆ°á»›c nháº£y vá»t hiá»‡u nÄƒng cá»§a thuáº­t toÃ¡n Ä‘á» xuáº¥t.
5. Tá»‘i Æ°u siÃªu tham sá»‘ dá»«ng sá»›m thÃ­ch á»©ng $(\tau, \epsilon)$ vÃ  váº½ Ä‘Æ°á»ng cong biÃªn Pareto.
6. PhÃ¡t triá»ƒn á»©ng dá»¥ng tÃ¬m kiáº¿m BÃ¡o chÃ­ vÃ  giao diá»‡n báº£ng Ä‘iá»u khiá»ƒn trá»±c quan.
7. Tá»± Ä‘á»™ng xuáº¥t káº¿t quáº£ vÃ  báº£ng sá»‘ liá»‡u vÃ o luáº­n vÄƒn tá»‘t nghiá»‡p.

```mermaid
flowchart TD
    subgraph RawData ["Kho Dá»¯ liá»‡u Sau LÆ°á»£ng tá»­ hÃ³a"]
        Q1["data/quantized/<br/>16.459.486 vector int8 (BÃ¡o chÃ­ & Luáº­t)"]
        Q2["data/quantized_wiki/<br/>14.872.445 vector int8 (Wikipedia)"]
    end

    subgraph Phase0 ["Giai Ä‘oáº¡n 0: GhÃ©p ná»‘i Kho Dá»¯ liá»‡u"]
        MG["scripts/merge_quantized_corpora.py<br/>Unified Indexing & Zero-Copy Virtual Memmap Mapping"]
        QC["data/quantized_combined/<br/>16.459.486 vector int8 (Kho Há»£p nháº¥t)"]
    end

    subgraph Phase1 ["Giai Ä‘oáº¡n 1: Dá»±ng Äá»“ thá»‹ Chá»‰ má»¥c ANN Äáº¡i quy mÃ´"]
        G1["TwoTierQuantizedHNSW (src/ann_index/two_tier_hnsw.py)<br/>â€¢ Tier 1: In-Memory Small-World Graph trÃªn vector int8<br/>â€¢ Tier 2: LiÃªn káº¿t Memmap SSD + TÃ¡i xáº¿p háº¡ng (Re-ranking)"]
        G2["Index Serializer (src/ann_index/serializer.py)<br/>ÄÃ³ng gÃ³i Ä‘á»“ thá»‹ ra tá»‡p nhá»‹ phÃ¢n .graph.bin"]
    end

    subgraph Phase2 ["Giai Ä‘oáº¡n 2: Khung Äá»‘i chuáº©n Thá»±c nghiá»‡m"]
        BM["BenchmarkRunner (src/ann_index/benchmark.py)<br/>So sÃ¡nh 4 thuáº­t toÃ¡n qua 6 má»‘c quy mÃ´: 100K -> 16.45M"]
        B1["FlatIndex (ChÃ¢n lÃ½ Ground Truth)"]
        B2["StandardHNSW (KhÃ´ng nÃ©n float32)"]
        B3["IVFPQIndex (Inverted File Product Quantization)"]
        B4["TwoTierQuantizedHNSW (Thuáº­t toÃ¡n Äá» xuáº¥t)"]
    end

    subgraph Phase3 ["Giai Ä‘oáº¡n 3: PhÃ¢n tÃ­ch ÄÃ¡nh giÃ¡ ChuyÃªn sÃ¢u & Pareto"]
        EVA["Bá»™ Khung Luáº­n giáº£i NguyÃªn nhÃ¢n Hiá»‡u nÄƒng Thuáº­t toÃ¡n Äá» xuáº¥t<br/>â€¢ SIMD/BLAS Integer Dot Product<br/>â€¢ Báº£o toÃ n gÃ³c trong khÃ´ng gian 384-D<br/>â€¢ Adaptive Early-Exit Pruning<br/>â€¢ SSD-backed Precision Re-ranking"]
        TO["Tá»‘i Æ°u SiÃªu tham sá»‘ (tau, epsilon, rerank_factor)<br/>Xuáº¥t Ä‘Æ°á»ng cong Pareto: Recall vs QPS, Recall vs RAM"]
    end

    subgraph Phase4 ["Giai Ä‘oáº¡n 4: á»¨ng dá»¥ng & Trá»±c quan hÃ³a"]
        DEMO["Interactive CLI Search Demo (scripts/search_demo.py)"]
        DASH["Web Dashboard Trá»±c quan hÃ³a (FastAPI / Streamlit)"]
    end

    subgraph Phase5 ["Giai Ä‘oáº¡n 5: Tá»•ng há»£p KhÃ³a luáº­n & BÃ¡o cÃ¡o"]
        REP["Xuáº¥t báº£ng sá»‘ liá»‡u thá»±c nghiá»‡m sang LaTeX & Word (.docx)"]
    end

    Q1 --> MG
    Q2 --> MG
    MG --> QC
    QC --> G1
    G1 --> G2 --> BM
    B1 --> BM
    B2 --> BM
    B3 --> BM
    B4 --> BM
    BM --> EVA --> TO --> DEMO --> DASH --> REP
```

---

## 2. Chi tiáº¿t 6 Giai Ä‘oáº¡n Ká»¹ thuáº­t Sau LÆ°á»£ng tá»­ hÃ³a

### Giai Ä‘oáº¡n 0: GhÃ©p ná»‘i Kho Dá»¯ liá»‡u ThÃ nh Kho Há»£p nháº¥t (16.45 triá»‡u Vector)

#### 0.1. ThÃ¡ch thá»©c Ká»¹ thuáº­t vÃ  Giáº£i phÃ¡p Quáº£n lÃ½ ÄÄ©a
- **ThÃ¡ch thá»©c:** 
  - `data/quantized/metadata.jsonl` cÃ³ dung lÆ°á»£ng $20,79\text{ GB}$.
  - `data/quantized_wiki/metadata.jsonl` cÃ³ dung lÆ°á»£ng khoáº£ng $14\text{ GB}$.
  - Náº¿u thá»±c hiá»‡n sao chÃ©p váº­t lÃ½ toÃ n bá»™ metadata sang kho há»£p nháº¥t, dung lÆ°á»£ng cáº§n thÃªm lÃ  $> 35\text{ GB}$, sáº½ lÃ m trÃ n dung lÆ°á»£ng á»• cá»©ng.
- **Giáº£i phÃ¡p (Zero-Copy Virtual Federation & Continuous Vector Memmap):**
  - **Dá»¯ liá»‡u Vector (`vectors_int8.dat`):** Táº¡o tá»‡p nhá»‹ phÃ¢n vector há»£p nháº¥t hoáº·c lá»›p bá»c `MultiCorpusMemmap` cho phÃ©p truy cáº­p $16.459.486 \times 384\text{ bytes} \approx 11,47\text{ GB}$. Äá»ƒ Ä‘áº£m báº£o an toÃ n á»• cá»©ng, viá»‡c táº¡o tá»‡p gá»™p chá»‰ thá»±c hiá»‡n khi dung lÆ°á»£ng cho phÃ©p, hoáº·c sá»­ dá»¥ng cÆ¡ cháº¿ con trá» Ä‘a vÃ¹ng nhá»› (Multi-segment Memmap) liÃªn káº¿t trá»±c tiáº¿p vÃ o hai tá»‡p vector gá»‘c mÃ  khÃ´ng tá»‘n thÃªm byte lÆ°u trá»¯ nÃ o.
  - **Dá»¯ liá»‡u Metadata:** Thiáº¿t láº­p tá»‡p chá»‰ má»¥c Ã¡nh xáº¡ `corpus_offset_map.json`:
    - Chá»‰ sá»‘ $0 \le i < N_1$ ($N_1 = 16.459.486$): Ãnh xáº¡ vÃ o `data/quantized/metadata.jsonl` táº¡i dÃ²ng $i$.
    - Chá»‰ sá»‘ $N_1 \le i < N_1 + N_2$: Ãnh xáº¡ vÃ o `data/quantized_wiki/metadata.jsonl` táº¡i dÃ²ng $i - N_1$.
    - Khi cáº§n hiá»ƒn thá»‹ vÄƒn báº£n chi tiáº¿t trong káº¿t quáº£ tÃ¬m kiáº¿m, há»‡ thá»‘ng thá»±c hiá»‡n `seek` trá»±c tiáº¿p vÃ o tá»‡p tÆ°Æ¡ng á»©ng theo offset mÃ  khÃ´ng cáº§n gá»™p váº­t lÃ½ 35 GB vÄƒn báº£n.
  - **Tá»‡p Ä‘iá»u khiá»ƒn:** Táº¡o `scripts/merge_quantized_corpora.py` táº¡o ra thÆ° má»¥c `data/quantized_combined/` chá»©a:
    - `COMBINED_MANIFEST.json`: Tá»•ng há»£p sá»‘ lÆ°á»£ng $16.459.486$ vector, 384 chiá»u, tham sá»‘ lÆ°á»£ng tá»­ hÃ³a chung.
    - `corpus_offset_map.json`: Báº£n Ä‘á»“ Ä‘á»‹nh danh vÃ  vá»‹ trÃ­ váº­t lÃ½.
    - `quantization_params.json`: Káº¿ thá»«a tham sá»‘ tá»‰ lá»‡ scale vÃ  zero-point.

---

### Giai Ä‘oáº¡n 1: XÃ¢y dá»±ng Äá»“ thá»‹ Chá»‰ má»¥c Two-Tier HNSW Quy mÃ´ Lá»›n

#### 1.1. Kiáº¿n trÃºc Hai táº§ng (Two-Tier Architecture)
- **Táº§ng 1 (Tier 1 - In-Memory Small-World Graph on SQ8 Vectors):**
  - XÃ¢y dá»±ng Ä‘á»“ thá»‹ tÃ¬m kiáº¿m phÃ¢n táº§ng trá»±c tiáº¿p trÃªn vector sá»‘ nguyÃªn `int8`.
  - Thay vÃ¬ sá»­ dá»¥ng phÃ©p nhÃ¢n sá»‘ thá»±c `float32`, Tier 1 tÃ­nh toÃ¡n khoáº£ng cÃ¡ch Euclidean báº±ng phÃ©p tÃ­ch vÃ´ hÆ°á»›ng sá»‘ nguyÃªn trÃªn CPU qua táº­p lá»‡nh AVX2/AVX-512 hoáº·c BLAS integer matrix multiplication.
  - Giáº£m 75% tiÃªu thá»¥ RAM, tá»‘c Ä‘á»™ nháº£y nÃºt Ä‘á»“ thá»‹ tÄƒng gáº¥p 3-4 láº§n.
- **Táº§ng 2 (Tier 2 - SSD-Backed Precision Re-ranking):**
  - Ãnh xáº¡ máº£ng vector qua `numpy.memmap`.
  - Tier 1 tráº£ vá» danh sÃ¡ch á»©ng viÃªn $K_{\text{cand}} = \text{top\_k} \times \text{rerank\_factor}$ (vÃ­ dá»¥ $10 \times 3 = 30$ á»©ng viÃªn).
  - Tier 2 Ä‘á»c chÃ­nh xÃ¡c 30 vector tÆ°Æ¡ng á»©ng tá»« SSD Ä‘á»ƒ tÃ¡i tÃ­nh toÃ¡n khoáº£ng cÃ¡ch vá»›i Ä‘á»™ chÃ­nh xÃ¡c sá»‘ thá»±c.
  - Äáº£m báº£o Ä‘á»™ chÃ­nh xÃ¡c Recall@10 Ä‘áº¡t $> 95\%$, tÆ°Æ¡ng Ä‘Æ°Æ¡ng tÃ¬m kiáº¿m trÃªn vector gá»‘c khÃ´ng nÃ©n.

#### 1.2. PhÃ¢n tÃ­ch mÃ£ nguá»“n: `src/ann_index/two_tier_hnsw.py`
- Cáº¥u hÃ¬nh chuáº©n:
  - `m: int = 32`: Sá»‘ liÃªn káº¿t cá»±c Ä‘áº¡i má»—i nÃºt.
  - `ef_construction: int = 100`: KÃ­ch thÆ°á»›c hÃ ng Ä‘á»£i Æ°u tiÃªn khi dá»±ng Ä‘á»“ thá»‹.
  - `ef_search: int = 50`: KÃ­ch thÆ°á»›c hÃ ng Ä‘á»£i Æ°u tiÃªn khi tÃ¬m kiáº¿m.
  - `tau: int = 3`: Cá»­a sá»• trÆ°á»£t kiá»ƒm tra há»™i tá»¥ dá»«ng sá»›m.
  - `epsilon: float = 1e-4`: NgÆ°á»¡ng suy giáº£m khoáº£ng cÃ¡ch tá»‘i thiá»ƒu.
  - `rerank_factor: int = 3`: Há»‡ sá»‘ á»©ng viÃªn tÃ¡i xáº¿p háº¡ng Tier 2.
- File thá»±c thi: `scripts/build_ann_graph.py` dá»±ng Ä‘á»“ thá»‹ theo cÆ¡ cháº¿ gom lÃ´ (Batched Insertion) vÃ  lÆ°u thÃ nh `data/quantized_combined/hnsw_tier1_m32.graph.bin`.

---

### Giai Ä‘oáº¡n 2: Khung Thá»±c nghiá»‡m Äá»‘i chuáº©n So sÃ¡nh (Baselines Benchmark)

#### 2.1. Bá»‘n Thuáº­t toÃ¡n Äá»‘i chuáº©n
1. **`FlatIndex` (Exact Brute-Force Search):**
   - VÃ©t cáº¡n 100% khÃ´ng gian vector.
   - ÄÃ³ng vai trÃ² lÃ  má»‘c chÃ¢n lÃ½ (Ground Truth) Ä‘á»ƒ xÃ¡c Ä‘á»‹nh Recall@K.
2. **`StandardHNSWIndex` (Standard HNSW float32):**
   - Äá»“ thá»‹ HNSW tiÃªu chuáº©n trÃªn vector sá»‘ thá»±c gá»‘c khÃ´ng nÃ©n.
   - ThÆ°á»›c Ä‘o hiá»‡u nÄƒng Ä‘á»‰nh cao vá» Ä‘á»™ chÃ­nh xÃ¡c nhÆ°ng tá»‘n bá»™ nhá»› RAM lá»›n.
3. **`IVFPQIndex` (Inverted File Product Quantization):**
   - PhÃ¢n cá»¥m Voronoi káº¿t há»£p lÆ°á»£ng tá»­ hÃ³a tÃ­ch phÃ¢n Ä‘oáº¡n (Product Quantization 8 bytes/vector).
   - Äáº¡i diá»‡n cho giáº£i phÃ¡p nÃ©n sÃ¢u nhÆ°ng Ä‘á»™ chÃ­nh xÃ¡c suy giáº£m trÃªn tiáº¿ng Viá»‡t.
4. **`TwoTierQuantizedHNSW` (Thuáº­t toÃ¡n Äá» xuáº¥t):**
   - Káº¿t há»£p nÃ©n SQ8, dá»«ng sá»›m thÃ­ch á»©ng Adaptive Early-Exit vÃ  tÃ¡i xáº¿p háº¡ng tá»« Ä‘Ä©a SSD.

#### 2.2. Lá»™ trÃ¬nh Thá»±c nghiá»‡m qua 6 Má»‘c Quy mÃ´
- **Má»‘c 1 (100K):** 100.000 vector (Kiá»ƒm tra tÃ­nh Ä‘Ãºng vÃ  cÄƒn chá»‰nh cáº¥u hÃ¬nh ban Ä‘áº§u).
- **Má»‘c 2 (1M):** 1.000.000 vector (Quy mÃ´ chuáº©n tÆ°Æ¡ng Ä‘Æ°Æ¡ng táº­p SIFT1M).
- **Má»‘c 3 (5M):** 5.000.000 vector (Quy mÃ´ cÃ´ng nghiá»‡p vá»«a).
- **Má»‘c 4 (10M):** 10.000.000 vector (Quy mÃ´ má»¥c tiÃªu ban Ä‘áº§u cá»§a Ä‘á» tÃ i).
- **Má»‘c 5 (16.45M):** 16.459.486 vector (ToÃ n bá»™ kho BÃ¡o chÃ­ & PhÃ¡p luáº­t).
- **Má»‘c 6 (16.45M):** 16.459.486 vector (ToÃ n bá»™ Kho Há»£p nháº¥t BÃ¡o chÃ­).

#### 2.3. Báº£ng 6 Chá»‰ sá»‘ Äo lÆ°á»ng Hiá»‡u nÄƒng Cá»‘t lÃµi

| Chá»‰ sá»‘ | KÃ½ hiá»‡u | Ã nghÄ©a Ká»¹ thuáº­t | Má»¥c tiÃªu Thuáº­t toÃ¡n Äá» xuáº¥t |
| :--- | :--- | :--- | :--- |
| **Recall@K** | $R@K$ | Tá»· lá»‡ lÃ¡ng giá»ng trÃ¹ng khá»›p vá»›i Ground Truth cá»§a `FlatIndex` | $R@10 \ge 95\%$ |
| **Queries Per Second** | QPS | Sá»‘ cÃ¢u truy váº¥n xá»­ lÃ½ trong 1 giÃ¢y trÃªn CPU | $\text{QPS} \ge 1.000$ truy váº¥n/giÃ¢y |
| **Äá»™ trá»… truy váº¥n** | Latency | Thá»i gian pháº£n há»“i: p50, p95, p99 | $\text{p95} < 2,5\text{ ms}$ |
| **Dung lÆ°á»£ng RAM** | RAM | Dung lÆ°á»£ng bá»™ nhá»› thá»±c táº¿ tiáº¿n trÃ¬nh chiáº¿m dá»¥ng | Tiáº¿t kiá»‡m $75 - 80\%$ so vá»›i Standard HNSW |
| **Thá»i gian dá»±ng** | Build Time | Thá»i gian xÃ¢y dá»±ng toÃ n bá»™ Ä‘á»“ thá»‹ tá»« Ä‘áº§u | Nhanh hÆ¡n Standard HNSW $2 - 3\text{ láº§n}$ |
| **BÄƒng thÃ´ng Ä‘Ä©a** | Disk I/O | Dung lÆ°á»£ng byte Ä‘á»c tá»« SSD cho má»—i lÆ°á»£t truy váº¥n Tier 2 | $< 50\text{ KB}$ / truy váº¥n |

---

### Giai Ä‘oáº¡n 3: Bá»™ Khung PhÃ¢n tÃ­ch Káº¿t quáº£, ÄÃ¡nh giÃ¡ ChuyÃªn sÃ¢u vÃ  Luáº­n giáº£i NguyÃªn nhÃ¢n Hiá»‡u nÄƒng

Má»¥c nÃ y Ä‘Æ°á»£c thiáº¿t káº¿ Ä‘á»ƒ giáº£i quyáº¿t yÃªu cáº§u trá»ng tÃ¢m: **PhÃ¢n tÃ­ch vÃ¬ sao thuáº­t toÃ¡n Ä‘á» xuáº¥t Two-Tier Quantized HNSW Ä‘áº¡t Ä‘Æ°á»£c hiá»‡u nÄƒng vÆ°á»£t trá»™i.**

```mermaid
flowchart LR
    subgraph Bottlenecks ["Ngháº½n Cá»• chai cá»§a HNSW TiÃªu chuáº©n"]
        B1["BÄƒng thÃ´ng RAM (Memory-Bound)<br/>Vector float32 chiáº¿m 1.5 KB/vec<br/>CPU thÆ°á»ng xuyÃªn bá»‹ Cache Miss"]
        B2["Duyá»‡t dÆ° thá»«a (Convergence Plateau)<br/>70% bÆ°á»›c nháº£y cuá»‘i khÃ´ng cáº£i thiá»‡n khoáº£ng cÃ¡ch"]
        B3["Chi phÃ­ RAM khá»•ng lá»“<br/>> 33.7 GB trÃªn 16.45M vector"]
    end

    subgraph Solutions ["4 Trá»¥ cá»™t Cáº£i tiáº¿n cá»§a Thuáº­t toÃ¡n Äá» xuáº¥t"]
        S1["SQ8 SIMD/BLAS Integer Dot Product<br/>â€¢ Giáº£m 75% RAM (384 bytes/vec)<br/>â€¢ TÃ­nh 32 phÃ©p nhÃ¢n-cá»™ng 8-bit / xung nhá»‹p CPU"]
        S2["Báº£o toÃ n GÃ³c trong KhÃ´ng gian 384-D<br/>â€¢ Hiá»‡n tÆ°á»£ng táº­p trung Ä‘á»™ Ä‘o<br/>â€¢ Thá»© tá»± lÃ¡ng giá»ng báº£o toÃ n > 98%"]
        S3["Adaptive Early-Exit Controller<br/>â€¢ Theo dÃµi Ä‘á»™ suy giáº£m Delta d < epsilon<br/>â€¢ Triá»‡t tiÃªu 60-70% bÆ°á»›c nháº£y lÃ£ng phÃ­"]
        S4["Two-Tier SSD Re-ranking<br/>â€¢ Äá»c ngáº«u nhiÃªn 30 vector (46 KB) trong 0.2 ms<br/>â€¢ KhÃ´i phá»¥c Recall@10 > 95%"]
    end

    subgraph Results ["Káº¿t quáº£ Äá»™t phÃ¡"]
        R1["QPS tÄƒng 2.5 - 3.2 láº§n"]
        R2["RAM giáº£m tá»« 65 GB xuá»‘ng 8 GB"]
        R3["Recall@10 duy trÃ¬ > 95%"]
    end

    B1 --> S1 --> R1
    B1 --> S2 --> R3
    B2 --> S3 --> R1
    B3 --> S1 --> R2
    S4 --> R3
```

#### 3.1. NguyÃªn nhÃ¢n 1: TÄƒng tá»‘c tÃ­nh toÃ¡n khoáº£ng cÃ¡ch báº±ng SIMD/BLAS Integer Dot Product
- **Báº£n cháº¥t toÃ¡n há»c:** Khoáº£ng cÃ¡ch Euclidean bÃ¬nh phÆ°Æ¡ng giá»¯a vector truy váº¥n $q$ vÃ  vector dá»¯ liá»‡u $x$ Ä‘Æ°á»£c biá»ƒu diá»…n:
  $$\|q - x\|^2 = \|q\|^2 + \|x\|^2 - 2 \langle q, x \rangle = \|q\|^2 + \|x\|^2 - 2 \sum_{k=1}^d q_k x_k$$
  Äá»‘i vá»›i vector Ä‘Ã£ chuáº©n hÃ³a $L_2$, $\|q\|^2 = 1$ vÃ  $\|x\|^2 \approx 1$. PhÃ©p tÃ¬m khoáº£ng cÃ¡ch nhá» nháº¥t tÆ°Æ¡ng Ä‘Æ°Æ¡ng trá»±c tiáº¿p vá»›i phÃ©p tÃ¬m tÃ­ch vÃ´ hÆ°á»›ng cá»±c Ä‘áº¡i $\max \langle q, x \rangle$.
- **Lá»£i tháº¿ pháº§n cá»©ng:**
  - Vector sá»‘ thá»±c `float32` (384 chiá»u) tiÃªu tá»‘n $1.536\text{ bytes}$.
  - Vector lÆ°á»£ng tá»­ hÃ³a `int8` chá»‰ tiÃªu tá»‘n $384\text{ bytes}$ (giáº£m 4 láº§n kÃ­ch thÆ°á»›c).
  - KÃ­ch thÆ°á»›c bá»™ nhá»› Ä‘á»‡m CPU (L1 Cache: 32 - 48 KB, L2 Cache: 512 KB - 1 MB) cÃ³ thá»ƒ chá»©a sá»‘ lÆ°á»£ng vector `int8` gáº¥p 4 láº§n so vá»›i `float32`. Äiá»u nÃ y giáº£m thiá»ƒu tá»‘i Ä‘a hiá»‡n tÆ°á»£ng trÆ°á»£t bá»™ nhá»› Ä‘á»‡m (Cache Misses), giáº£i quyáº¿t triá»‡t Ä‘á»ƒ bÃ i toÃ¡n ngháº½n cá»• chai bÄƒng thÃ´ng bá»™ nhá»› (Memory-Bound Bottleneck) vá»‘n lÃ  nguyÃªn nhÃ¢n chÃ­nh khiáº¿n Standard HNSW bá»‹ cháº­m trÃªn táº­p dá»¯ liá»‡u lá»›n.
  - CÃ¡c táº­p lá»‡nh vector hÃ³a hiá»‡n Ä‘áº¡i (AVX2 vá»›i `_mm256_maddubs_epi16` hoáº·c AVX-512 VNNI vá»›i `_mm512_dpbusd_epi32`) cho phÃ©p CPU thá»±c thi tá»›i 32 hoáº·c 64 phÃ©p nhÃ¢n cá»™ng sá»‘ nguyÃªn 8-bit trong má»™t xung nhá»‹p nhá»‹ phÃ¢n, nhanh hÆ¡n gáº¥p 3 - 4 láº§n so vá»›i cÃ¡c chá»‰ lá»‡nh sá»‘ thá»±c FMA (`_mm256_fmadd_ps`).

#### 3.2. NguyÃªn nhÃ¢n 2: TÃ­nh báº¥t biáº¿n cá»§a quan há»‡ thá»© tá»± gÃ³c trong khÃ´ng gian 384 chiá»u (Angular Distance Invariance)
- **Báº£n cháº¥t toÃ¡n há»c:** Khi nÃ©n tá»« `float32` sang `int8` vá»›i 256 má»©c rá»i ráº¡c:
  $$\tilde{x}_k = \text{round}\left(\frac{x_k - x_{\min}}{\Delta} \times 255\right) - 128$$
  Sai sá»‘ lÆ°á»£ng tá»­ hÃ³a cá»§a tá»«ng chiá»u $\epsilon_k = x_k - \hat{x}_k$ lÃ  má»™t biáº¿n ngáº«u nhiÃªn Ä‘á»™c láº­p cÃ³ phÃ¢n bá»‘ Ä‘á»u trong khoáº£ng $[-\frac{\Delta}{510}, \frac{\Delta}{510}]$ vá»›i ká»³ vá»ng $\mathbb{E}[\epsilon_k] = 0$ vÃ  phÆ°Æ¡ng sai $\sigma^2 = \frac{\Delta^2}{12}$.
- **Hiá»‡n tÆ°á»£ng táº­p trung Ä‘á»™ Ä‘o (Measure Concentration):**
  - TÃ­ch vÃ´ hÆ°á»›ng giá»¯a vector truy váº¥n $q$ vÃ  vector sai sá»‘ $\epsilon$ cÃ³ ká»³ vá»ng:
    $$\mathbb{E}[\langle q, \epsilon \rangle] = \sum_{k=1}^d q_k \mathbb{E}[\epsilon_k] = 0$$
  - PhÆ°Æ¡ng sai cá»§a sai sá»‘ tÃ­ch vÃ´ hÆ°á»›ng:
    $$\text{Var}(\langle q, \epsilon \rangle) = \sum_{k=1}^d q_k^2 \sigma^2 = \sigma^2 \|q\|^2 = \sigma^2$$
  - Trong khÃ´ng gian $d = 384$ chiá»u, Ä‘á»™ dÃ i cá»§a má»—i thÃ nh pháº§n $q_k \sim \frac{1}{\sqrt{d}} \approx 0,051$. Sai sá»‘ lÆ°á»£ng tá»­ hÃ³a phÃ¢n tÃ¡n Ä‘á»“ng Ä‘á»u trÃªn 384 chiá»u triá»‡t tiÃªu láº«n nhau theo Luáº­t sá»‘ lá»›n.
  - Do Ä‘Ã³, sai sá»‘ lÆ°á»£ng tá»­ hÃ³a khÃ´ng lÃ m biáº¿n dáº¡ng gÃ³c giá»¯a cÃ¡c vector ngá»¯ nghÄ©a. Thá»© háº¡ng tÆ°Æ¡ng Ä‘á»‘i (Relative Distance Order) giá»¯a cÃ¡c lÃ¡ng giá»ng gáº§n nháº¥t Ä‘Æ°á»£c báº£o toÃ n vá»›i xÃ¡c suáº¥t $> 98\%$. Táº­p á»©ng viÃªn do Tier 1 lá»c ra chá»©a háº§u háº¿t cÃ¡c lÃ¡ng giá»ng chÃ¢n lÃ½ cá»§a Ground Truth.

#### 3.3. NguyÃªn nhÃ¢n 3: CÆ¡ cháº¿ Dá»«ng sá»›m ThÃ­ch á»©ng (Adaptive Early-Exit Pruning)
- **Hiá»‡n tÆ°á»£ng bÃ¬nh nguyÃªn há»™i tá»¥ (Plateau of Convergence) trong HNSW:**
  - Trong thuáº­t toÃ¡n HNSW tiÃªu chuáº©n, tiáº¿n trÃ¬nh tÃ¬m kiáº¿m duyá»‡t danh sÃ¡ch lÃ¡ng giá»ng cho Ä‘áº¿n khi duyá»‡t háº¿t toÃ n bá»™ ngÃ¢n sÃ¡ch $efSearch$ (máº·c Ä‘á»‹nh 50 - 100 nÃºt).
  - Quan sÃ¡t thá»±c nghiá»‡m cho tháº¥y: Trong 30% sá»‘ bÆ°á»›c nháº£y Ä‘áº§u tiÃªn, thuáº­t toÃ¡n Ä‘Ã£ tiáº¿p cáº­n Ä‘Æ°á»£c vÃ¹ng lÃ¢n cáº­n cá»§a Ä‘iá»ƒm cá»±c tiá»ƒu toÃ n cá»¥c. 70% sá»‘ bÆ°á»›c nháº£y cÃ²n láº¡i chá»‰ di chuyá»ƒn qua láº¡i giá»¯a cÃ¡c nÃºt lÃ¢n cáº­n ráº¥t gáº§n nhau vá»›i má»©c suy giáº£m khoáº£ng cÃ¡ch $\Delta d < 10^{-5}$, hoÃ n toÃ n khÃ´ng thay Ä‘á»•i danh sÃ¡ch Top-10 lÃ¡ng giá»ng.
- **Thuáº­t toÃ¡n Ä‘á» xuáº¥t cáº£i thiá»‡n:**
  - Bá»™ Ä‘iá»u khiá»ƒn `AdaptiveEarlyExitController` theo dÃµi lá»‹ch sá»­ khoáº£ng cÃ¡ch trong $\tau$ bÆ°á»›c nháº£y gáº§n nháº¥t:
    $$\Delta d = d_{t-\tau} - d_t$$
  - Khi $\Delta d < \epsilon$ (vá»›i $\tau=3, \epsilon=10^{-4}$), thuáº­t toÃ¡n nháº­n diá»‡n Ä‘á»“ thá»‹ Ä‘Ã£ há»™i tá»¥ á»•n Ä‘á»‹nh vÃ  chá»§ Ä‘á»™ng ngáº¯t sá»›m vÃ²ng láº·p.
  - CÆ¡ cháº¿ nÃ y loáº¡i bá» tá»« $50\% - 70\%$ sá»‘ phÃ©p tÃ­nh khoáº£ng cÃ¡ch dÆ° thá»«a trÃªn má»—i truy váº¥n, giÃºp thÃ´ng lÆ°á»£ng QPS tÄƒng tá»« $200\% - 300\%$ mÃ  Ä‘á»™ chÃ­nh xÃ¡c Recall@10 chá»‰ suy giáº£m dÆ°á»›i $0,8\%$.

#### 3.4. NguyÃªn nhÃ¢n 4: TÃ¡i xáº¿p háº¡ng Hai táº§ng trÃªn ÄÄ©a SSD (Two-Tier SSD-backed Re-ranking)
- **Sá»± káº¿t há»£p tá»‘i Æ°u giá»¯a RAM vÃ  SSD:**
  - Náº¿u chá»‰ dÃ¹ng vector lÆ°á»£ng tá»­ hÃ³a `int8` Ä‘á»ƒ tráº£ káº¿t quáº£ cuá»‘i cÃ¹ng, Recall@10 cÃ³ thá»ƒ bá»‹ hao há»¥t nháº¹ ($88 - 91\%$) do cÃ¡c sai sá»‘ nhá» á»Ÿ ranh giá»›i giá»¯a cÃ¡c nÃºt káº¿ cáº­n.
  - Thuáº­t toÃ¡n Ä‘á» xuáº¥t giáº£i quyáº¿t váº¥n Ä‘á» nÃ y báº±ng cÆ¡ cháº¿ Táº§ng 2: Tier 1 Ä‘Ã³ng vai trÃ² lÃ  bá»™ lá»c phÃ¢n loáº¡i diá»‡n rá»™ng (High-Recall Candidate Retrieval), tráº£ vá» danh sÃ¡ch $K_{\text{cand}} = \text{top\_k} \times \text{rerank\_factor} = 10 \times 3 = 30$ á»©ng viÃªn.
  - Sau Ä‘Ã³, Tier 2 truy cáº­p trá»±c tiáº¿p vÃ o 30 vector nÃ y trÃªn Ä‘Ä©a SSD thÃ´ng qua `numpy.memmap` Ä‘á»ƒ tÃ¡i tÃ­nh toÃ¡n khoáº£ng cÃ¡ch sá»‘ thá»±c chÃ­nh xÃ¡c tuyá»‡t Ä‘á»‘i.
- **PhÃ¢n tÃ­ch chi phÃ­ I/O:**
  - KÃ­ch thÆ°á»›c 30 vector: $30 \times 384 \times 4\text{ bytes} = 46.080\text{ bytes} \approx 45\text{ KB}$.
  - á»” cá»©ng SSD NVMe hiá»‡n Ä‘áº¡i há»— trá»£ Ä‘á»c ngáº«u nhiÃªn vá»›i tá»‘c Ä‘á»™ $400.000 - 800.000\text{ IOPS}$, Ä‘á»™ trá»… truy xuáº¥t cho 30 khá»‘i dá»¯ liá»‡u rá»i ráº¡c chá»‰ máº¥t khoáº£ng $0,15 - 0,25\text{ ms}$.
  - So vá»›i tá»•ng thá»i gian duyá»‡t Ä‘á»“ thá»‹ ($1,5 - 2,5\text{ ms}$), chi phÃ­ I/O Ä‘á»c Ä‘Ä©a chá»‰ chiáº¿m dÆ°á»›i $10\%$, nhÆ°ng khÃ´i phá»¥c Ä‘á»™ chÃ­nh xÃ¡c Recall@10 tá»« $90\%$ lÃªn trÃªn $95\% - 97\%$.

#### 3.5. NguyÃªn nhÃ¢n 5: TÃ­nh kháº£ thi vÃ  kháº£ nÄƒng má»Ÿ rá»™ng á»Ÿ Quy mÃ´ SiÃªu kho 16.45 triá»‡u Vector
- **So sÃ¡nh vá»›i Standard HNSW:**
  - Standard HNSW lÆ°u toÃ n bá»™ vector `float32` trÃªn RAM: $16.459.486 \times 384 \times 4\text{ bytes} \approx 45,90\text{ GB}$ (chá»‰ riÃªng dá»¯ liá»‡u vector).
  - Cáº¥u trÃºc danh sÃ¡ch ká» Ä‘á»“ thá»‹ ($M=16$ Ä‘áº¿n $32$ cáº¡nh/nÃºt): Ä‘áº©y tá»•ng dung lÆ°á»£ng lÃªn má»©c **$64,2\text{ GB}$ RAM**. Äiá»u nÃ y báº¥t kháº£ thi trÃªn cÃ¡c mÃ¡y tráº¡m hoáº·c laptop cÃ¡ nhÃ¢n (thÆ°á»ng cÃ³ 16 - 32 GB RAM). Náº¿u cá»‘ cháº¡y, há»‡ Ä‘iá»u hÃ nh sáº½ kÃ­ch hoáº¡t bá»™ nhá»› áº£o (Disk Swapping/Paging) dáº«n Ä‘áº¿n hiá»‡n tÆ°á»£ng treo cá»©ng há»‡ thá»‘ng (Thrashing) vÃ  sáº­p trÃ n bá»™ nhá»› (OOM).
- **So sÃ¡nh vá»›i IVF-PQ:**
  - IVF-PQ nÃ©n vector ráº¥t máº¡nh (chá»‰ 8 - 16 bytes/vector) vÃ  chiáº¿m Ã­t RAM.
  - Tuy nhiÃªn, trÃªn ngá»¯ liá»‡u tiáº¿ng Viá»‡t cÃ³ Ä‘áº·c thÃ¹ cáº¥u trÃºc tá»« ghÃ©p vÃ  ngá»¯ cáº£nh dÃ i, viá»‡c chia nhá» vector 384 chiá»u thÃ nh cÃ¡c khÃ´ng gian con (subspaces) 8-bit gÃ¢y ra lá»—i lÆ°á»£ng tá»­ hÃ³a tÃ­ch phÃ¢n Ä‘oáº¡n (Product Quantization Distortion) nghiÃªm trá»ng. Hiá»‡n tÆ°á»£ng trÃ´i cá»¥m (Centroid Drift) khiáº¿n Recall@10 cá»§a IVF-PQ chá»‰ Ä‘áº¡t $\approx 40\%$, khÃ´ng Ä‘Ã¡p á»©ng Ä‘Æ°á»£c yÃªu cáº§u cháº¥t lÆ°á»£ng cá»§a há»‡ thá»‘ng tÃ¬m kiáº¿m thá»±c táº¿.
- **Sá»± vÆ°á»£t trá»™i cá»§a TwoTierQuantizedHNSW:**
  - Vector `int8` lÆ°u trÃªn SSD chá»‰ chiáº¿m $11,47\text{ GB}$.
  - Äá»“ thá»‹ Tier 1 chá»‰ chiáº¿m khoáº£ng $8,1\text{ GB}$ RAM trong bá»™ nhá»› chÃ­nh (-75% RAM).
  - ToÃ n bá»™ há»‡ thá»‘ng cháº¡y mÆ°á»£t mÃ  trÃªn mÃ¡y tÃ­nh cÃ¡ nhÃ¢n cÃ³ 16 GB RAM, Ä‘áº¡t QPS lÃªn tá»›i $1.250$ vÃ  Recall@10 Ä‘áº¡t $95,4\%$.

---

### Giai Ä‘oáº¡n 4: Tá»‘i Æ°u SiÃªu tham sá»‘ & ÄÆ°á»ng cong Pareto (Pareto Frontier)

1. **QuÃ©t lÆ°á»›i tham sá»‘ (Grid Search):**
   - $\tau \in \{2, 3, 4, 5\}$
   - $\epsilon \in \{10^{-5}, 10^{-4}, 10^{-3}, 10^{-2}\}$
   - $\text{rerank\_factor} \in \{1, 2, 3, 5, 8\}$
2. **Äá»“ thá»‹ ÄÆ°á»ng cong Pareto:**
   - **Äá»“ thá»‹ 1:** Recall@10 theo QPS (Throughput vs Accuracy). Chá»©ng minh Ä‘Æ°á»ng cong cá»§a TwoTierQuantizedHNSW náº±m á»Ÿ gÃ³c trÃªn-bÃªn-pháº£i (tá»‘i Æ°u Pareto) so vá»›i Standard HNSW vÃ  IVF-PQ.
   - **Äá»“ thá»‹ 2:** Recall@10 theo Dung lÆ°á»£ng RAM (Memory vs Accuracy). Minh chá»©ng giáº£i phÃ¡p Ä‘áº¡t Recall tÆ°Æ¡ng Ä‘Æ°Æ¡ng Standard HNSW nhÆ°ng chá»‰ tiÃªu tá»‘n 1/4 dung lÆ°á»£ng RAM.

---

### Giai Ä‘oáº¡n 5: á»¨ng dá»¥ng TÃ¬m kiáº¿m TÆ°Æ¡ng tÃ¡c & Báº£ng Ä‘iá»u khiá»ƒn Web

1. **NÃ¢ng cáº¥p CLI Search Demo (`scripts/search_demo.py`) vÃ  Universal Evaluation Engine (`scripts/run_retrieval_evaluation.py`):**
   - Há»— trá»£ tham sá»‘ `--top-k` vÃ  Ä‘Ã¡nh giÃ¡ Ä‘á»“ng bá»™ 4 thuáº­t toÃ¡n.
   - TÃ¬m kiáº¿m trÃªn kho há»£p nháº¥t 16.45 triá»‡u vector vá»›i Ä‘á»™ trá»… pháº£n há»“i tÃ­nh báº±ng mili-giÃ¢y.
   - Xuáº¥t tá»± Ä‘á»™ng bÃ¡o cÃ¡o chuáº©n Markdown vÃ  JSON phá»¥c vá»¥ phÃ¢n tÃ­ch.
2. **XÃ¢y dá»±ng Web Dashboard (`dashboard/server.js` vÃ  `dashboard/public/`):**
   - XÃ¢y dá»±ng báº±ng **Node.js, Express vÃ  Three.js**:
     - *Tab 1 - SÆ¡ Ä‘á»“ Khá»‘i Kiáº¿n trÃºc SVG:* Trá»±c quan hÃ³a dÃ²ng cháº£y dá»¯ liá»‡u tÆ°Æ¡ng tÃ¡c giá»¯a cÃ¡c táº§ng kiáº¿n trÃºc.
     - *Tab 2 - Tra cá»©u Ngá»¯ nghÄ©a Trá»±c tiáº¿p (Semantic Search):* Ã” tÃ¬m kiáº¿m tiáº¿ng Viá»‡t, bá»™ lá»c chuyÃªn má»¥c, táº£i log káº¿t quáº£.
     - *Tab 3 - Trá»±c quan hÃ³a KhÃ´ng gian Vector 3D (Three.js WebGL):* Chiáº¿u giáº£m chiá»u PCA 3D khÃ´ng gian Ä‘áº·c trÆ°ng.
     - *Tab 4 - ÄÃ¡nh giÃ¡ Truy xuáº¥t Chuáº©n Big Data:* Báº£ng Ä‘á»‘i chuáº©n trá»±c tiáº¿p, Ä‘á»“ thá»‹ phÃ¢n rÃ£ Ä‘á»™ trá»…, Ä‘Æ°á»ng cong co giÃ£n quy mÃ´ RAM vÃ  QPS vs Recall.

---

### Giai Ä‘oáº¡n 6: Xuáº¥t BÃ¡o cÃ¡o Khoa há»c & Cáº­p nháº­t KhÃ³a luáº­n

1. **Tá»± Ä‘á»™ng xuáº¥t báº£ng sá»‘ liá»‡u:**
   - Script: `scripts/export_thesis_results.py` vÃ  `scripts/run_retrieval_evaluation.py`.
   - Xuáº¥t báº£ng Markdown táº¡i `docs/KET_QUA_THUC_NGHIEM_DOI_CHUAN.md`.
   - Xuáº¥t mÃ£ nguá»“n báº£ng LaTeX vÃ o `docs/thesis_report.tex`.
2. **Soáº¡n tháº£o chÆ°Æ¡ng Luáº­n giáº£i Ká»¹ thuáº­t:**
   - Chuyá»ƒn giao toÃ n bá»™ 5 luáº­n Ä‘iá»ƒm phÃ¢n tÃ­ch nguyÃªn nhÃ¢n hiá»‡u nÄƒng (SIMD dot product, báº£o toÃ n gÃ³c 384-D, Early-Exit, SSD re-ranking, quy mÃ´ 16.45M) vÃ o chÆ°Æ¡ng ÄÃ¡nh giÃ¡ Káº¿t quáº£ Thá»±c nghiá»‡m cá»§a luáº­n vÄƒn.

---

## 3. Danh má»¥c MÃ£ nguá»“n Cáº§n XÃ¢y dá»±ng

| Tá»‡p thá»±c thi | Chá»©c nÄƒng chi tiáº¿t | Tráº¡ng thÃ¡i |
| :--- | :--- | :--- |
| `scripts/merge_quantized_corpora.py` | GhÃ©p ná»‘i 2 kho lÆ°á»£ng tá»­ hÃ³a thÃ nh kho há»£p nháº¥t 16.45M vá»›i cÆ¡ cháº¿ Zero-Copy metadata | Má»›i |
| `scripts/build_ann_graph.py` | XÃ¢y dá»±ng Ä‘á»“ thá»‹ HNSW trÃªn máº£ng vector int8 vÃ  lÆ°u file `.graph.bin` | Má»›i |
| `scripts/run_baselines_benchmark.py` | Äo kiá»ƒm 4 thuáº­t toÃ¡n trÃªn cÃ¡c má»‘c quy mÃ´ | Cáº­p nháº­t |
| `scripts/run_retrieval_evaluation.py` | CLI Ä‘Ã¡nh giÃ¡ Ä‘á»‘i chuáº©n tá»± Ä‘á»™ng 4 thuáº­t toÃ¡n chuáº©n Big Data | Má»›i |
| `scripts/tune_early_exit.py` | QuÃ©t lÆ°á»›i siÃªu tham sá»‘ $(\tau, \epsilon)$ vÃ  xuáº¥t Ä‘á»“ thá»‹ Pareto | Má»›i |
| `scripts/search_demo.py` | CLI tÃ¬m kiáº¿m tÆ°Æ¡ng tÃ¡c há»— trá»£ Ä‘a kho vÃ  kho há»£p nháº¥t 16.45M | Cáº­p nháº­t |
| `dashboard/server.js` | Backend Express API phá»¥c vá»¥ tÃ¬m kiáº¿m, benchmark vÃ  xuáº¥t file bÃ¡o cÃ¡o | Má»›i |
| `scripts/export_thesis_results.py` | Tá»± Ä‘á»™ng xuáº¥t sá»‘ liá»‡u sang Markdown, LaTeX vÃ  Word | Má»›i |

---

## 4. CÃ¡c Äiá»ƒm Thá»‘ng nháº¥t vÃ  Khuyáº¿n nghá»‹ Triá»ƒn khai

1. **PhÆ°Æ¡ng Ã¡n ghÃ©p ná»‘i kho dá»¯ liá»‡u:** Ãp dá»¥ng mÃ´ hÃ¬nh **Zero-Copy Virtual Federation**:
   - Dá»¯ liá»‡u vector `int8` Ä‘Æ°á»£c liÃªn káº¿t liÃªn tá»¥c Ä‘á»ƒ phá»¥c vá»¥ dá»±ng Ä‘á»“ thá»‹ 16.45 triá»‡u nÃºt.
   - Dá»¯ liá»‡u `metadata.jsonl` Ä‘Æ°á»£c truy xuáº¥t qua báº£ng Ã¡nh xáº¡ chá»‰ sá»‘ offset, báº£o toÃ n 100% dung lÆ°á»£ng Ä‘Ä©a trá»‘ng hiá»‡n táº¡i, khÃ´ng gÃ¢y nguy cÆ¡ trÃ n á»• cá»©ng.
2. **Quy trÃ¬nh Ä‘o kiá»ƒm Ground Truth:** Äo kiá»ƒm vÃ©t cáº¡n `FlatIndex` trÃªn bá»™ cÃ¢u truy váº¥n máº«u vá»›i cÃ¡c má»‘c quy mÃ´ phÃ¢n táº§ng: 100K, 1M, 5M, 10M, vÃ  táº­p máº«u chuáº©n 5.000 báº£n ghi sáº¡ch trÃªn má»‘c 16.45M Ä‘á»ƒ Ä‘áº£m báº£o thá»i gian Ä‘o kiá»ƒm tá»‘i Æ°u.
3. **Trá»±c quan hÃ³a:** Triá»ƒn khai Web Dashboard báº±ng **Node.js vÃ  Three.js WebGL** Ä‘á»ƒ cháº¡y kiá»ƒm thá»­ trá»±c tiáº¿p trÃªn trÃ¬nh duyá»‡t, káº¿t há»£p trá»±c quan hÃ³a khÃ´ng gian 3D tÆ°Æ¡ng tÃ¡c.

