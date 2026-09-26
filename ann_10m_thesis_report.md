> **LƯU Ý:** Tài liệu này đã cũ và được thay thế toàn bộ bởi [BAO_CAO_LUAN_VAN_CHIT_TIET.md](BAO_CAO_LUAN_VAN_CHIT_TIET.md). Xin vui lòng tham khảo file báo cáo chính thức để xem kiến trúc Two-Tier HNSW lượng tử hóa SQ8 mới nhất.

# BÃO CÃO Äá»€ TÃ€I MÃ”N Há»ŒC

## Äá» tÃ i: TÃ¬m hiá»ƒu vÃ  triá»ƒn khai thuáº­t toÃ¡n Approximate Nearest Neighbor (HNSW káº¿t há»£p LÆ°á»£ng tá»­ hÃ³a thÃ­ch á»©ng) trÃªn dá»¯ liá»‡u vÄƒn báº£n tiáº¿ng Viá»‡t quy mÃ´ 10 triá»‡u Ä‘áº¿n 16.45 triá»‡u báº£n ghi

---

### THÃ”NG TIN CHUNG
* **LÄ©nh vá»±c:** Dá»¯ liá»‡u lá»›n (Big Data), Xá»­ lÃ½ ngÃ´n ngá»¯ tá»± nhiÃªn (NLP), TÃ¬m kiáº¿m thÃ´ng tin (Information Retrieval).
* **Má»¥c tiÃªu á»©ng dá»¥ng:** XÃ¢y dá»±ng há»‡ sinh thÃ¡i tÃ¬m kiáº¿m ngá»¯ nghÄ©a (Semantic Search) vÃ  truy xuáº¥t tÃ i liá»‡u quy mÃ´ lá»›n (RAG) Ä‘Ã¡p á»©ng Ä‘á»™ trá»… mili-giÃ¢y trÃªn táº­p dá»¯ liá»‡u lá»›n tá»« 10 triá»‡u Ä‘áº¿n 16.45 triá»‡u vÄƒn báº£n.
* **Má»¥c tiÃªu nghiÃªn cá»©u:** Giáº£i quyáº¿t bÃ i toÃ¡n tháº¯t cá»• chai bá»™ nhá»› (Memory Bottleneck) cá»§a thuáº­t toÃ¡n HNSW gá»‘c thÃ´ng qua ká»¹ thuáº­t nÃ©n lÆ°á»£ng tá»­ hÃ³a káº¿t há»£p duyá»‡t Ä‘á»“ thá»‹ dá»«ng sá»›m, lÃ m tiá»n Ä‘á» má»Ÿ rá»™ng thÃ nh bÃ i bÃ¡o khoa há»c.
* **Quy mÃ´ thá»±c táº¿ Ä‘áº¡t Ä‘Æ°á»£c:** 16.459.486 vector 384 chiá»u (16.459.486 BÃ¡o chÃ­ & PhÃ¡p luáº­t + 0), phÃ¢n chia 400 shards, kiá»ƒm chá»©ng qua 91 bÃ i kiá»ƒm thá»­ tá»± Ä‘á»™ng.
* **PhÃ¢n cÃ´ng nhÃ³m:**
  * ThÃ nh viÃªn 1: Ká»¹ thuáº­t dá»¯ liá»‡u (Data Pipeline, Thu tháº­p BÃ¡o chÃ­, LÃ m sáº¡ch NFC, MinHash LSH, Vector Embedding).
  * ThÃ nh viÃªn 2: Ká»¹ thuáº­t thuáº­t toÃ¡n (CÃ i Ä‘áº·t Two-Tier HNSW, LÆ°á»£ng tá»­ hÃ³a SQ8, Dá»«ng sá»›m thÃ­ch á»©ng, Benchmark vÃ  ÄÃ¡nh giÃ¡ hiá»‡u nÄƒng).

---

## CHÆ¯Æ NG 1: Tá»”NG QUAN VÃ€ Äáº¶T Váº¤N Äá»€

### 1.1. Bá»‘i cáº£nh
Trong cÃ¡c há»‡ thá»‘ng tÃ¬m kiáº¿m hiá»‡n Ä‘áº¡i vÃ  cÃ¡c á»©ng dá»¥ng trÃ­ tuá»‡ nhÃ¢n táº¡o táº¡o sinh (GenAI / RAG), dá»¯ liá»‡u vÄƒn báº£n Ä‘Æ°á»£c chuyá»ƒn Ä‘á»•i thÃ nh cÃ¡c vector Ä‘áº·c trÆ°ng (vector embeddings) trong khÃ´ng gian nhiá»u chiá»u (vÃ­ dá»¥ 384 hoáº·c 768 chiá»u). 

Khi quy mÃ´ dá»¯ liá»‡u vÆ°á»£t qua ngÆ°á»¡ng 10 triá»‡u báº£n ghi vÃ  tiáº¿n tá»›i hÆ¡n 31 triá»‡u báº£n ghi, phÆ°Æ¡ng phÃ¡p tÃ¬m kiáº¿m chÃ­nh xÃ¡c (Exact k-NN / Flat Search) thÃ´ng qua quÃ©t toÃ n bá»™ táº­p dá»¯ liá»‡u (Brute-force) cÃ³ Ä‘á»™ phá»©c táº¡p thá»i gian lÃ  $\mathcal{O}(N \cdot D)$. PhÃ©p tÃ­nh nÃ y Ä‘Ã²i há»i hÃ ng tá»· phÃ©p nhÃ¢n cá»™ng ma tráº­n cho má»—i cÃ¢u truy váº¥n, khiáº¿n thá»i gian pháº£n há»“i kÃ©o dÃ i tá»« vÃ i chá»¥c giÃ¢y Ä‘áº¿n vÃ i phÃºt, khÃ´ng thá»ƒ á»©ng dá»¥ng trong mÃ´i trÆ°á»ng thá»i gian thá»±c.

### 1.2. Váº¥n Ä‘á» cá»§a cÃ¡c thuáº­t toÃ¡n xáº¥p xá»‰ hiá»‡n nay
Thuáº­t toÃ¡n tÃ¬m kiáº¿m lÃ¡ng giá»ng gáº§n Ä‘Ãºng (Approximate Nearest Neighbor - ANN) dá»±a trÃªn Ä‘á»“ thá»‹ phÃ¢n táº§ng (Hierarchical Navigable Small World - HNSW) hiá»‡n lÃ  tiÃªu chuáº©n cÃ´ng nghiá»‡p vá»›i tá»‘c Ä‘á»™ truy váº¥n mili-giÃ¢y vÃ  Ä‘á»™ chÃ­nh xÃ¡c (Recall) cao. Tuy nhiÃªn, khi Ã¡p dá»¥ng trÃªn quy mÃ´ lá»›n, HNSW bá»™c lá»™ Ä‘iá»ƒm yáº¿u chÃ­ máº¡ng vá» tiÃªu thá»¥ tÃ i nguyÃªn pháº§n cá»©ng:
* Vá»›i 10 triá»‡u vector 384 chiá»u kiá»ƒu float32, dá»¯ liá»‡u thÃ´ chiáº¿m 15.36 GB; má»Ÿ rá»™ng lÃªn 16.45 triá»‡u vector, dung lÆ°á»£ng Ä‘áº¡t 24.11 GB.
* Cáº¥u trÃºc Ä‘á»“ thá»‹ Ä‘a táº§ng cá»§a HNSW cáº§n lÆ°u danh sÃ¡ch liÃªn káº¿t giá»¯a cÃ¡c Ä‘á»‰nh ($M = 16$ Ä‘áº¿n $32$ lÃ¡ng giá»ng/Ä‘á»‰nh), kÃ­ch thÆ°á»›c báº£ng liÃªn káº¿t tiÃªu tá»‘n thÃªm khoáº£ng 25-30 GB (vÃ  trÃªn 32 GB vá»›i 16.45M).
* Tá»•ng dung lÆ°á»£ng RAM cáº§n thiáº¿t vÆ°á»£t quÃ¡ 46 GB Ä‘áº¿n 32 GB, khiáº¿n cÃ¡c mÃ¡y chá»§ phá»• thÃ´ng hoáº·c mÃ¡y tÃ­nh cÃ¡ nhÃ¢n (16GB - 32GB RAM) láº­p tá»©c gáº·p lá»—i trÃ n bá»™ nhá»› (Out-Of-Memory - OOM).

### 1.3. Má»¥c tiÃªu Ä‘á» tÃ i
1. XÃ¢y dá»±ng táº­p dá»¯ liá»‡u vÄƒn báº£n tiáº¿ng Viá»‡t quy mÃ´ lá»›n Ä‘áº¡t má»‘c cÆ¡ sá»Ÿ 10 triá»‡u báº£n ghi vÃ  má»Ÿ rá»™ng lÃªn 16.45 triá»‡u báº£n ghi tá»« hai nguá»“n: BÃ¡o chÃ­ & PhÃ¡p luáº­t .
2. Triá»ƒn khai vÃ  phÃ¢n tÃ­ch Ä‘iá»ƒm ngháº½n hiá»‡u nÄƒng cá»§a thuáº­t toÃ¡n HNSW chuáº©n vÃ  cÃ¡c biáº¿n thá»ƒ cÆ¡ báº£n (Flat, IVF-PQ).
3. Äá» xuáº¥t kiáº¿n trÃºc: **Two-Tier Quantized HNSW with Adaptive Early-Exit (Äá»“ thá»‹ lÆ°á»£ng tá»­ hÃ³a hai táº§ng vá»›i cÆ¡ cháº¿ dá»«ng sá»›m thÃ­ch á»©ng)** nháº±m giáº£m 75% dung lÆ°á»£ng vector trÃªn RAM mÃ  váº«n duy trÃ¬ Ä‘á»™ chÃ­nh xÃ¡c (Recall@10) trÃªn 94% - 95.4%.

---

## CHÆ¯Æ NG 2: CÆ  Sá»ž LÃ THUYáº¾T VÃ€ PHÃ‚N TÃCH NGUYÃŠN NHÃ‚N HIá»†U NÄ‚NG

### 2.1. Cáº¥u trÃºc vÃ  nguyÃªn lÃ½ cá»§a thuáº­t toÃ¡n HNSW
HNSW mÃ´ phá»ng nguyÃªn lÃ½ máº¡ng tháº¿ giá»›i nhá» (Small World Phenomenon). Äá»“ thá»‹ Ä‘Æ°á»£c chia thÃ nh nhiá»u táº§ng (Layer $0, 1, \dots, L$):
* **Táº§ng trÃªn cÃ¹ng ($L$):** ThÆ°a thá»›t, khoáº£ng cÃ¡ch giá»¯a cÃ¡c node lá»›n, Ä‘Ã³ng vai trÃ² "nháº£y cÃ³c" Ä‘á»ƒ Ä‘á»‹nh vá»‹ vÃ¹ng khÃ´ng gian rá»™ng (tÆ°Æ¡ng tá»± xa lá»™).
* **Táº§ng Ä‘Ã¡y ($0$):** Chá»©a toÃ n bá»™ $N$ vector, cÃ¡c liÃªn káº¿t dÃ y Ä‘áº·c vÃ  ngáº¯n, dÃ¹ng Ä‘á»ƒ Ä‘á»‹nh vá»‹ chÃ­nh xÃ¡c Ä‘iá»ƒm lÃ¡ng giá»ng cá»¥c bá»™.

QuÃ¡ trÃ¬nh truy váº¥n sá»­ dá»¥ng chiáº¿n lÆ°á»£c tÃ¬m kiáº¿m tham lam (Greedy Search):
$$\text{Node tiáº¿p theo} = \arg\min_{v \in \mathcal{N}(u)} \text{dist}(v, q)$$
Trong Ä‘Ã³ $\mathcal{N}(u)$ lÃ  táº­p lÃ¡ng giá»ng cá»§a node hiá»‡n táº¡i $u$, $q$ lÃ  vector truy váº¥n.

### 2.2. PhÃ¢n tÃ­ch nguyÃªn nhÃ¢n suy giáº£m hiá»‡u nÄƒng trÃªn dá»¯ liá»‡u lá»›n (>10 triá»‡u báº£n ghi)

1. **Tháº¯t cá»• chai bÄƒng thÃ´ng bá»™ nhá»› (Memory Bandwidth Bottleneck):**
   Má»—i bÆ°á»›c nháº£y trÃªn Ä‘á»“ thá»‹ yÃªu cáº§u CPU Ä‘á»c vector cá»§a cÃ¡c node lÃ¡ng giá»ng tá»« RAM. Vá»›i 10 triá»‡u vector, kÃ­ch thÆ°á»›c dá»¯ liá»‡u vÆ°á»£t xa dung lÆ°á»£ng bá»™ nhá»› Ä‘á»‡m L3 cá»§a CPU (thÆ°á»ng chá»‰ 16MB - 64MB). Tá»· lá»‡ trÆ°á»£t bá»™ Ä‘á»‡m (Cache Miss) xáº¥p xá»‰ 90%, khiáº¿n CPU pháº£i liÃªn tá»¥c chá» dá»¯ liá»‡u chuyá»ƒn tá»« thanh RAM sang, lÃ m cháº­m quÃ¡ trÃ¬nh duyá»‡t Ä‘á»“ thá»‹.

2. **DÆ° thá»«a tÃ­nh toÃ¡n á»Ÿ giai Ä‘oáº¡n Ä‘á»‹nh tuyáº¿n (Routing Redundancy):**
   á»ž cÃ¡c táº§ng cao vÃ  giai Ä‘oáº¡n Ä‘áº§u cá»§a táº§ng 0, má»¥c Ä‘Ã­ch cá»§a thuáº­t toÃ¡n chá»‰ lÃ  xÃ¡c Ä‘á»‹nh hÆ°á»›ng Ä‘i tá»•ng quÃ¡t. Viá»‡c sá»­ dá»¥ng toÃ n bá»™ vector float32 384 chiá»u Ä‘á»ƒ tÃ­nh khoáº£ng cÃ¡ch Euclide hoáº·c Cosine lÃ  lÃ£ng phÃ­ tÃ i nguyÃªn tÃ­nh toÃ¡n.

3. **Hiá»‡n tÆ°á»£ng giáº«m chÃ¢n táº¡i chá»— á»Ÿ giai Ä‘oáº¡n há»™i tá»¥:**
   Khi Ä‘Ã£ Ä‘áº¿n ráº¥t gáº§n cá»¥m dá»¯ liá»‡u chá»©a káº¿t quáº£, thuáº­t toÃ¡n HNSW truyá»n thá»‘ng váº«n tiáº¿p tá»¥c duyá»‡t Ä‘á»§ sá»‘ lÆ°á»£ng á»©ng viÃªn theo tham sá»‘ cáº¥u hÃ¬nh tÄ©nh (`efSearch`). Äiá»u nÃ y gÃ¢y ra nhiá»u phÃ©p tÃ­nh khoáº£ng cÃ¡ch khÃ´ng cáº§n thiáº¿t nhÆ°ng khÃ´ng cáº£i thiá»‡n thÃªm Ä‘á»™ chÃ­nh xÃ¡c.

---

## CHÆ¯Æ NG 3: Äá»€ XUáº¤T Cáº¢I TIáº¾N: LÆ¯á»¢NG Tá»¬ HÃ“A HAI Táº¦NG VÃ€ Dá»ªNG Sá»šM THÃCH á»¨NG

Äá»ƒ giáº£i quyáº¿t cÃ¡c Ä‘iá»ƒm báº¥t lá»£i trÃªn vÃ  má»Ÿ ra hÆ°á»›ng nghiÃªn cá»©u thÃ nh bÃ i bÃ¡o khoa há»c, Ä‘á» tÃ i Ä‘á» xuáº¥t kiáº¿n trÃºc káº¿t há»£p:

```
[Vector Truy Váº¥n q]
        â”‚
        â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ GIAI ÄOáº N 1: Äá»ŠNH TUYáº¾N TRÃŠN Äá»’ THá»Š LÆ¯á»¢NG Tá»¬ HÃ“A         â”‚
â”‚ * Äá»“ thá»‹ HNSW dÃ¹ng vector nÃ©n 8-bit (Scalar Quantization) â”‚
â”‚ * KÃ­ch thÆ°á»›c vector giáº£m tá»« 1536 byte -> 384 byte        â”‚
â”‚ * TÃ­nh toÃ¡n khoáº£ng cÃ¡ch báº±ng lá»‡nh SIMD/AVX2 siÃªu nhanh   â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
        â”‚
        â–¼  Ãp dá»¥ng cÆ¡ cháº¿ Dynamic Early-Exit:
        â”‚  Náº¿u sau Ï„ bÆ°á»›c nháº£y khoáº£ng cÃ¡ch khÃ´ng giáº£m > Îµ
        â”‚  --> Dá»«ng duyá»‡t Ä‘á»“ thá»‹ ngay láº­p tá»©c
        â”‚
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ GIAI ÄOáº N 2: XÃC THá»°C VÃ€ TÃI Sáº®P Xáº¾P (RE-RANKING)        â”‚
â”‚ * Chá»n Top-K á»©ng viÃªn (K=50 hoáº·c 100)                    â”‚
â”‚ * Äá»c vector gá»‘c float32 tá»« tá»‡p Memory-Mapped trÃªn á»• cá»©ngâ”‚
â”‚ * TÃ­nh khoáº£ng cÃ¡ch chÃ­nh xÃ¡c Ä‘á»ƒ tráº£ vá» Top-10            â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### 3.1. CÆ¡ cháº¿ LÆ°á»£ng tá»­ hÃ³a hai táº§ng (Two-Tier Quantization)
* **Tier 1 (In-Memory Index):** Vector 384 chiá»u kiá»ƒu float32 (4 byte/chiá»u) Ä‘Æ°á»£c lÆ°á»£ng tá»­ hÃ³a thÃ nh sá»‘ nguyÃªn int8 (1 byte/chiá»u). Dung lÆ°á»£ng 10 triá»‡u vector giáº£m tá»« 15.36 GB xuá»‘ng 3.84 GB, náº±m hoÃ n toÃ n trong RAM cá»§a mÃ¡y tÃ­nh thÃ´ng thÆ°á»ng.
* **Tier 2 (Disk-Backed Full Vector):** Vector float32 nguyÃªn báº£n Ä‘Æ°á»£c lÆ°u trá»¯ dÆ°á»›i dáº¡ng tá»‡p Ã¡nh xáº¡ bá»™ nhá»› (Memory-mapped file / `np.memmap`). Dá»¯ liá»‡u nÃ y náº±m trÃªn á»• cá»©ng SSD vÃ  chá»‰ Ä‘Æ°á»£c náº¡p lÃªn RAM Ä‘Ãºng $K$ báº£n ghi á»Ÿ bÆ°á»›c xáº¿p háº¡ng cuá»‘i cÃ¹ng.

### 3.2. Thuáº­t toÃ¡n Dá»«ng sá»›m thÃ­ch á»©ng (Adaptive Early-Exit)
Thay vÃ¬ duy trÃ¬ hÃ ng Ä‘á»£i Æ°u tiÃªn cÃ³ kÃ­ch thÆ°á»›c cá»‘ Ä‘á»‹nh `efSearch`, thuáº­t toÃ¡n theo dÃµi Ä‘á»™ suy giáº£m khoáº£ng cÃ¡ch qua cÃ¡c bÆ°á»›c duyá»‡t:
$$\Delta d_t = d_{t - \tau} - d_t$$
Náº¿u sau $\tau$ bÆ°á»›c nháº£y liÃªn tiáº¿p mÃ  khoáº£ng cÃ¡ch tá»« á»©ng viÃªn tá»‘t nháº¥t tá»›i vector truy váº¥n giáº£m Ã­t hÆ¡n má»™t ngÆ°á»¡ng $\varepsilon$, thuáº­t toÃ¡n xÃ¡c Ä‘á»‹nh Ä‘Ã£ rÆ¡i vÃ o vÃ¹ng cá»±c tiá»ƒu cá»¥c bá»™ vÃ  láº­p tá»©c thoÃ¡t khá»i vÃ²ng láº·p tÃ¬m kiáº¿m.

---

## CHÆ¯Æ NG 4: Káº¾ HOáº CH THá»°C HIá»†N VÃ€ PHÃ‚N CÃ”NG NHIá»†M Vá»¤

Quy mÃ´ 10 triá»‡u báº£n ghi Ä‘Ã²i há»i quy trÃ¬nh ká»¹ thuáº­t cháº·t cháº½ giá»¯a 2 thÃ nh viÃªn:

```
[THÃ€NH VIÃŠN 1: DATA PIPELINE]           [THÃ€NH VIÃŠN 2: ALGORITHM & EVAL]
1. Thu tháº­p dá»¯ liá»‡u (>10M báº£n ghi)        1. Thiáº¿t láº­p háº¡ táº§ng Benchmark
   â”œâ”€â”€ Táº£i táº­p dá»¯ liá»‡u má»Ÿ (9.5M)             â”œâ”€â”€ CÃ i Ä‘áº·t Flat Search (Baseline chuáº©n)
   â””â”€â”€ Tá»± viáº¿t crawler (500K tin má»›i)        â”œâ”€â”€ CÃ i Ä‘áº·t HNSW chuáº©n (hnswlib/faiss)
2. Tiá»n xá»­ lÃ½ & LÃ m sáº¡ch dáº¡ng Stream         â””â”€â”€ CÃ i Ä‘áº·t IVF-PQ (Baseline nÃ©n)
   â”œâ”€â”€ Chuáº©n hÃ³a Unicode NFC              2. CÃ i Ä‘áº·t thuáº­t toÃ¡n Cáº£i tiáº¿n
   â”œâ”€â”€ Lá»c rÃ¡c & trÃ¹ng láº·p (MinHash)         â”œâ”€â”€ Module nÃ©n int8 SIMD
   â””â”€â”€ TÃ¡ch tá»« tiáº¿ng Viá»‡t                    â””â”€â”€ Module Dynamic Early-Exit
3. Vector Embedding Pipeline              3. Thá»±c nghiá»‡m, Äo lÆ°á»ng & PhÃ¢n tÃ­ch
   â”œâ”€â”€ Cháº¡y mÃ´ hÃ¬nh sinh vector              â”œâ”€â”€ Äo Recall@10, QPS, Äá»™ trá»… p95/p99
   â””â”€â”€ Xuáº¥t tá»‡p nhá»‹ phÃ¢n Memmap (10M x 384)   â””â”€â”€ PhÃ¢n tÃ­ch nguyÃªn nhÃ¢n hiá»‡u nÄƒng
```

### 4.1. Nhiá»‡m vá»¥ cá»§a ThÃ nh viÃªn 1: Ká»¹ thuáº­t Dá»¯ liá»‡u (Data Pipeline)

#### BÆ°á»›c 1: Nguá»“n dá»¯ liá»‡u (Äáº£m báº£o > 10 triá»‡u báº£n ghi)
1. **Nguá»“n cÃ³ sáºµn (Ná»n táº£ng):**
   * Sá»­ dá»¥ng táº­p dá»¯ liá»‡u `fsnaix/vietnamese-corpus-large` tá»« Hugging Face (phÃ¢n vÃ¹ng tin tá»©c vÃ  web, trÃ­ch xuáº¥t 9.5 triá»‡u vÄƒn báº£n).
2. **Nguá»“n tá»± thu tháº­p (Äiá»ƒm cá»™ng lá»›n cho Ä‘á» tÃ i):**
   * Viáº¿t module cÃ o dá»¯ liá»‡u (Crawler) báº±ng Python (`Scrapy` / `Asyncio` + `Playwright`) thu tháº­p tá»‘i thiá»ƒu **500.000 bÃ i viáº¿t** má»›i nháº¥t tá»« cÃ¡c trang bÃ¡o Ä‘iá»‡n tá»­ (VnExpress, DÃ¢n TrÃ­, Tuá»•i Tráº») vÃ  trang há»i Ä‘Ã¡p/diá»…n Ä‘Ã n.
   * Ghi log thá»i gian, nguá»“n thu tháº­p vÃ  cáº¥u trÃºc hÃ³a dá»¯ liá»‡u (tiÃªu Ä‘á», thá»i gian, ná»™i dung, chuyÃªn má»¥c).
   * **Tá»•ng há»£p:** Äáº¡t 10.000.000 báº£n ghi vÄƒn báº£n há»£p lá»‡.

#### BÆ°á»›c 2: Pipeline lÃ m sáº¡ch vÃ  xá»­ lÃ½ dá»¯ liá»‡u lá»›n (Streaming)
Do 10 triá»‡u vÄƒn báº£n vÄƒn báº£n thÃ´ chiáº¿m khoáº£ng 25-30 GB, viá»‡c xá»­ lÃ½ buá»™c pháº£i dÃ¹ng ká»¹ thuáº­t Ä‘á»c luá»“ng (Streaming):
* XÃ¢y dá»±ng script tiá»n xá»­ lÃ½: Chuáº©n hÃ³a báº£ng mÃ£ Unicode NFC, loáº¡i bá» mÃ£ HTML, URL, kÃ½ tá»± Ä‘áº·c biá»‡t.
* Sá»­ dá»¥ng thuáº­t toÃ¡n MinHash LSH (thÆ° viá»‡n `datasketch`) xá»­ lÃ½ phÃ¢n Ä‘oáº¡n Ä‘á»ƒ lá»c bá» cÃ¡c bÃ i viáº¿t trÃ¹ng láº·p hoáº·c sao chÃ©p ná»™i dung (>80% tÆ°Æ¡ng Ä‘á»“ng).
* TÃ¡ch tá»« tiáº¿ng Viá»‡t sá»­ dá»¥ng cÃ´ng cá»¥ nháº¹ (`pyvi` hoáº·c `underthesea`).

#### BÆ°á»›c 3: Táº¡o Vector Embeddings á»Ÿ quy mÃ´ lá»›n
* Chá»n mÃ´ hÃ¬nh: `paraphrase-multilingual-MiniLM-L12-v2` hoáº·c `bkai-foundation-models/vietnamese-bi-encoder` (chiá»u vector $D = 384$, vá»«a Ä‘á»§ cho Ä‘á»™ chÃ­nh xÃ¡c vÃ  nháº¹ vá» tÃ­nh toÃ¡n).
* Ká»¹ thuáº­t lÆ°u trá»¯: Ghi trá»±c tiáº¿p ra Ä‘Ä©a dÆ°á»›i dáº¡ng tá»‡p `float32 binary format` hoáº·c `numpy memory-mapped (.dat / .npy)` theo tá»«ng lÃ´ (batch 2048 vÄƒn báº£n) Ä‘á»ƒ trÃ¡nh Ä‘áº§y RAM:
  $$\text{Dung lÆ°á»£ng tá»‡p vector} = 10.000.000 \times 384 \times 4 \text{ bytes} \approx 15.36 \text{ GB}$$

---

### 4.2. Nhiá»‡m vá»¥ cá»§a ThÃ nh viÃªn 2: Thuáº­t toÃ¡n vÃ  Thá»±c nghiá»‡m (Algorithm & Benchmark)

#### BÆ°á»›c 1: CÃ i Ä‘áº·t há»‡ thá»‘ng Ä‘á»‘i chuáº©n (Baselines)
1. **Exact Search (Ground Truth):**
   * Láº¥y máº«u 1.000 cÃ¢u truy váº¥n thá»­ nghiá»‡m.
   * Sá»­ dá»¥ng Flat Index tÃ­nh toÃ¡n chÃ­nh xÃ¡c Ä‘á»ƒ xuáº¥t file káº¿t quáº£ Ground Truth (Top-100 káº¿t quáº£ Ä‘Ãºng nháº¥t cho má»—i truy váº¥n).
2. **Standard HNSW:**
   * Sá»­ dá»¥ng thÆ° viá»‡n `hnswlib` hoáº·c `faiss` vá»›i vector float32. Äo Ä‘áº¡c dung lÆ°á»£ng bá»™ nhá»› thá»±c táº¿ vÃ  thá»i gian láº­p chá»‰ má»¥c.
3. **IVF-PQ (Inverted File with Product Quantization):**
   * Äáº¡i diá»‡n cho trÆ°á»ng phÃ¡i nÃ©n truyá»n thá»‘ng Ä‘á»ƒ so sÃ¡nh má»©c Ä‘á»™ máº¥t mÃ¡t Ä‘á»™ chÃ­nh xÃ¡c.

#### BÆ°á»›c 2: CÃ i Ä‘áº·t Thuáº­t toÃ¡n Äá» xuáº¥t (Quantized HNSW + Early Exit)
* XÃ¢y dá»±ng lá»›p chá»‰ má»¥c káº¿ thá»«a cáº¥u trÃºc Ä‘á»“ thá»‹ cá»§a HNSW nhÆ°ng nÃ©n dá»¯ liá»‡u vector sang Ä‘á»‹nh dáº¡ng int8 kÃ¨m há»‡ sá»‘ tá»· lá»‡ cá»¥c bá»™ (local scaling factor).
* TÃ­ch há»£p Ä‘iá»u kiá»‡n dá»«ng sá»›m thÃ­ch á»©ng vÃ o vÃ²ng láº·p tÃ¬m kiáº¿m `searchKnn`.
* XÃ¢y dá»±ng táº§ng Re-ranking: Äá»c Top-$K$ á»©ng viÃªn tá»« tá»‡p nhá»‹ phÃ¢n memmap trÃªn SSD Ä‘á»ƒ tÃ­nh khoáº£ng cÃ¡ch float32 chÃ­nh xÃ¡c.

#### BÆ°á»›c 3: Äo lÆ°á»ng vÃ  Thu tháº­p sá»‘ liá»‡u
Äo Ä‘áº¡c chÃ­nh xÃ¡c 5 chá»‰ sá»‘ ká»¹ thuáº­t:
1. **Index Memory Footprint (GB):** LÆ°á»£ng RAM tiÃªu thá»¥ khi chá»‰ má»¥c náº¡p hoÃ n toÃ n.
2. **Build Time (Hours):** Thá»i gian xÃ¢y dá»±ng chá»‰ má»¥c cho 10 triá»‡u vector.
3. **Recall@10 (%):** Tá»· lá»‡ cÃ¡c káº¿t quáº£ trong Top-10 cá»§a thuáº­t toÃ¡n trÃ¹ng khá»›p vá»›i Ground Truth.
4. **Latency (p50, p95, p99 in ms):** Äá»™ trá»… pháº£n há»“i cá»§a cÃ¢u truy váº¥n.
5. **Throughput (QPS):** Sá»‘ lÆ°á»£ng truy váº¥n xá»­ lÃ½ Ä‘Æ°á»£c trong má»™t giÃ¢y á»Ÿ cháº¿ Ä‘á»™ Ä‘a luá»“ng.

---

## CHÆ¯Æ NG 5: Ká»ŠCH Báº¢N THá»°C NGHIá»†M VÃ€ ÄÃNH GIÃ NGUYÃŠN NHÃ‚N HIá»†U NÄ‚NG

### 5.1. Báº£ng sá»‘ liá»‡u Ä‘á»‘i sÃ¡nh ká»³ vá»ng (Dá»± kiáº¿n trong bÃ¡o cÃ¡o)

| Thuáº­t toÃ¡n | Cáº¥u hÃ¬nh | Dung lÆ°á»£ng RAM | Thá»i gian Build | Recall@10 | Latency p95 | Throughput (QPS) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Flat L2 (Baseline)** | Float32 | 15.4 GB | 0 | 100% | 450 ms | 2.2 |
| **HNSW Chuáº©n** | $M=32, ef=100$ | **46.2 GB** (OOM mÃ¡y nhá») | 4.2 giá» | 97.8% | 2.1 ms | 480 |
| **IVF-PQ** | $nlist=4096, m=32$ | 2.8 GB | 1.1 giá» | **78.4%** (Tá»¥t sÃ¢u) | 3.5 ms | 280 |
| **Äá» xuáº¥t (Two-Tier HNSW)**| $M=32, \text{int8} + \tau=3$ | **7.5 GB** (Giáº£m 84%) | 2.6 giá» | **94.6%** (Giá»¯ tá»‘t) | **1.2 ms** | **820** |

### 5.2. PhÆ°Æ¡ng phÃ¡p phÃ¢n tÃ­ch nguyÃªn nhÃ¢n hiá»‡u nÄƒng (DÃ nh cho pháº§n Tháº£o luáº­n)

Trong bÃ¡o cÃ¡o, nhÃ³m cáº§n phÃ¢n tÃ­ch sÃ¢u 3 luáº­n Ä‘iá»ƒm ká»¹ thuáº­t sau Ä‘á»ƒ Ä‘áº¡t Ä‘iá»ƒm tá»‘i Ä‘a:

1. **Táº¡i sao bá»™ nhá»› giáº£m tá»« 46.2 GB xuá»‘ng 7.5 GB?**
   * Vector biá»ƒu diá»…n giáº£m tá»« 15.36 GB xuá»‘ng 3.84 GB nhá» chuyá»ƒn Ä‘á»•i tá»« float32 (4 byte) sang int8 (1 byte).
   * Äá»“ thá»‹ táº§ng Ä‘Ã¡y (Layer 0) Ä‘Æ°á»£c tinh gá»n kÃ­ch thÆ°á»›c lÃ¢n cáº­n dá»±a trÃªn ma tráº­n khoáº£ng cÃ¡ch lÆ°á»£ng tá»­ hÃ³a, giáº£m kÃ­ch thÆ°á»›c con trá» liÃªn káº¿t.

2. **Táº¡i sao Ä‘á»™ trá»… (Latency) cáº£i thiá»‡n tá»« 2.1 ms xuá»‘ng 1.2 ms máº·c dÃ¹ pháº£i thÃªm bÆ°á»›c Re-ranking?**
   * PhÃ©p tÃ­nh khoáº£ng cÃ¡ch giá»¯a hai vector int8 Ä‘Æ°á»£c thá»±c thi thÃ´ng qua táº­p lá»‡nh SIMD (AVX-512 / AVX2) vá»›i chá»‰ 1 chu ká»³ xung nhá»‹p CPU cho 32 pháº§n tá»­, nhanh gáº¥p 4 láº§n so vá»›i phÃ©p tÃ­nh float32.
   * CÆ¡ cháº¿ Dá»«ng sá»›m thÃ­ch á»©ng (Early-exit) cáº¯t bá» trung bÃ¬nh 35% cÃ¡c bÆ°á»›c duyá»‡t láº·p vÃ´ nghÄ©a á»Ÿ cuá»‘i Ä‘á»“ thá»‹.
   * BÆ°á»›c Re-ranking chá»‰ Ä‘á»c 50 vector tá»« SSD thÃ´ng qua Linux Page Cache (bá»™ Ä‘á»‡m trang há»‡ Ä‘iá»u hÃ nh), tá»‘n chÆ°a tá»›i 0.2 ms.

3. **Táº¡i sao Recall@10 giá»¯ Ä‘Æ°á»£c á»Ÿ má»©c 94.6% (khÃ´ng bá»‹ rá»›t tháº£m háº¡i nhÆ° IVF-PQ)?**
   * IVF-PQ nhÃ³m cÃ¡c vector thÃ nh cÃ¡c cá»¥m tÄ©nh (Voronoi cells), náº¿u vector truy váº¥n náº±m sÃ¡t biÃªn cá»§a cá»¥m sáº½ bá»‹ máº¥t hoÃ n toÃ n thÃ´ng tin cá»¥m káº¿ bÃªn.
   * NgÆ°á»£c láº¡i, Ä‘á»“ thá»‹ HNSW duy trÃ¬ cÃ¡c liÃªn káº¿t Small-world liÃªn tá»¥c, sai sá»‘ lÆ°á»£ng tá»­ hÃ³a int8 chá»‰ lÃ m thay Ä‘á»•i nháº¹ thá»© tá»± duyá»‡t cá»¥c bá»™ chá»© khÃ´ng lÃ m chá»‡ch hÆ°á»›ng Ä‘Æ°á»ng Ä‘i tá»•ng quÃ¡t cá»§a Ä‘á»“ thá»‹. BÆ°á»›c Re-ranking cuá»‘i cÃ¹ng Ä‘Ã£ khÃ´i phá»¥c láº¡i thá»© tá»± chÃ­nh xÃ¡c hoÃ n toÃ n.

---

## CHÆ¯Æ NG 6: HÆ¯á»šNG PHÃT TRIá»‚N NÃ‚NG Cáº¤P THÃ€NH BÃ€I BÃO KHOA Há»ŒC (PAPER ROADMAP)

Sau khi hoÃ n thÃ nh bÃ i táº­p mÃ´n há»c, Ä‘á»“ Ã¡n nÃ y cÃ³ ná»n táº£ng vá»¯ng cháº¯c Ä‘á»ƒ chuyá»ƒn giao thÃ nh bÃ i bÃ¡o há»™i nghá»‹ chuyÃªn ngÃ nh (nhÆ° RIVF, KSE, hoáº·c FAIR táº¡i Viá»‡t Nam):

1. **LÆ°á»£ng tá»­ hÃ³a báº­c cao (1-bit / RaBitQ Integration):** Thay vÃ¬ dá»«ng láº¡i á»Ÿ int8 (giáº£m 4 láº§n), nghiÃªn cá»©u Ã¡p dá»¥ng ká»¹ thuáº­t 1-bit Randomized Quantization káº¿t há»£p vá»›i biáº¿n Ä‘á»•i trá»±c giao (Orthogonal Transform) Ä‘á»ƒ giáº£m kÃ­ch thÆ°á»›c vector xuá»‘ng 32 láº§n (384 bit = 48 byte).
2. **CÆ¡ cháº¿ cáº­p nháº­t luá»“ng Ä‘á»™ng (Dynamic Streaming Updates):** Giáº£i quyáº¿t nhÆ°á»£c Ä‘iá»ƒm khÃ´ng thá»ƒ xÃ³a/sá»­a node cá»§a Ä‘á»“ thá»‹ HNSW báº±ng cÃ¡ch Ã¡p dá»¥ng thuáº­t toÃ¡n tÃ¡i cÃ¢n báº±ng liÃªn káº¿t cá»¥c bá»™ khi cÃ³ tÃ i liá»‡u má»›i cÃ o vá» theo thá»i gian thá»±c.
3. **ÄÃ¡nh giÃ¡ trÃªn Ä‘a dáº¡ng táº­p dá»¯ liá»‡u chuáº©n tháº¿ giá»›i:** Má»Ÿ rá»™ng thá»±c nghiá»‡m trÃªn cÃ¡c táº­p dá»¯ liá»‡u Big ANN Benchmark chuáº©n (Deep1B, SIFT1B, Text2Image-1B) Ä‘á»ƒ cÃ´ng bá»‘ káº¿t quáº£ há»c thuáº­t khÃ¡ch quan.



TÃ i liá»‡u Tham kháº£o Há»c thuáº­t & Ká»¹ thuáº­t
ðŸ“Œ Thuáº­t toÃ¡n ChÃ­nh & Cáº¥u trÃºc Dá»¯ liá»‡u
[1] HNSW - Thuáº­t toÃ¡n ná»n táº£ng cá»§a Ä‘á» tÃ i

Malkov, Y. A., & Yashunin, D. A. (2018). Efficient and robust approximate nearest neighbor search using Hierarchical Navigable Small World graphs. IEEE Transactions on Pattern Analysis and Machine Intelligence, 42(4), 824â€“836.
DOI: https://doi.org/10.1109/TPAMI.2018.2889473
arXiv: https://arxiv.org/abs/1603.09320
[2] IVF-PQ - Thuáº­t toÃ¡n Ä‘á»‘i chuáº©n

JÃ©gou, H., Douze, M., & Schmid, C. (2011). Product quantization for nearest neighbor search. IEEE Transactions on Pattern Analysis and Machine Intelligence, 33(1), 117â€“128.
DOI: https://doi.org/10.1109/TPAMI.2010.57
PDF: https://inria.hal.science/inria-00514462/document
[3] Scalar Quantization & LÆ°á»£ng tá»­ hÃ³a Vector

Gersho, A., & Gray, R. M. (1991). Vector Quantization and Signal Compression. Springer.
DOI: https://doi.org/10.1007/978-1-4615-3626-0
[4] NSW / Small World Graph - Tiá»n thÃ¢n cá»§a HNSW

Malkov, Y., Ponomarenko, A., Logvinov, A., & Krylov, V. (2014). Approximate nearest neighbor algorithm based on navigable small world graphs. Information Systems, 45, 61â€“68.
DOI: https://doi.org/10.1016/j.is.2013.10.006
ðŸ“Œ Lá»c TrÃ¹ng láº·p - MinHash LSH
[5] MinHash & Locality-Sensitive Hashing

Broder, A. Z. (1997). On the resemblance and containment of documents. In Proceedings of the Compression and Complexity of Sequences, 21â€“29.
URL: https://cs.brown.edu/courses/cs253/papers/nearduplicate.pdf
[6] LSH Tá»•ng quÃ¡t

Indyk, P., & Motwani, R. (1998). Approximate nearest neighbors: Towards removing the curse of dimensionality. STOC '98.
URL: https://people.csail.mit.edu/indyk/p117-indyk.pdf
ðŸ“Œ Embedding & NLP
[7] Sentence-BERT - MÃ´ hÃ¬nh sinh vector D=384

Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence embeddings using siamese BERT-networks. EMNLP 2019.
arXiv: https://arxiv.org/abs/1908.10084
ThÆ° viá»‡n: https://www.sbert.net/
[8] BERT gá»‘c

Devlin, J., Chang, M. W., Lee, K., & Toutanova, K. (2019). BERT: Pre-training of deep bidirectional transformers for language understanding. NAACL 2019.
arXiv: https://arxiv.org/abs/1810.04805
ðŸ“Œ ThÆ° viá»‡n & CÃ´ng cá»¥ Thá»±c thi
[9] FAISS - Facebook AI Similarity Search (tham kháº£o thiáº¿t káº¿)

Johnson, J., Douze, M., & JÃ©gou, H. (2021). Billion-scale similarity search with GPUs. IEEE Transactions on Big Data, 7(3), 535â€“547.
arXiv: https://arxiv.org/abs/1702.08734
GitHub: https://github.com/facebookresearch/faiss
[10] NumPy memmap - CÆ¡ cháº¿ lÆ°u trá»¯ Tier 2

Harris, C. R., et al. (2020). Array programming with NumPy. Nature, 585, 357â€“362.
DOI: https://doi.org/10.1038/s41586-020-2649-2
TÃ i liá»‡u ká»¹ thuáº­t np.memmap: https://numpy.org/doc/stable/reference/generated/numpy.memmap.html
[11] ANN Benchmarks - CÆ¡ sá»Ÿ Ä‘o Ä‘áº¡c Recall & Latency

Aumuller, M., Bernhardsson, E., & Faithfull, A. (2020). ANN-benchmarks: A benchmarking tool for approximate nearest neighbor algorithms. Information Systems, 87, 101374.
DOI: https://doi.org/10.1016/j.is.2019.02.006
Website: https://ann-benchmarks.com/
ðŸ“Œ Dá»¯ liá»‡u Tiáº¿ng Viá»‡t & NLP
[12] PhoBERT - MÃ´ hÃ¬nh ngÃ´n ngá»¯ tiáº¿ng Viá»‡t

Nguyen, D. Q., & Nguyen, A. T. (2020). PhoBERT: Pre-trained language models for Vietnamese. EMNLP Findings 2020.
arXiv: https://arxiv.org/abs/2003.00744
[13] PyVi - TÃ¡ch tá»« tiáº¿ng Viá»‡t

GitHub: https://github.com/trungtv/pyvi
TÃ i liá»‡u: Tokenizer dá»±a trÃªn Conditional Random Field (CRF) cho tiáº¿ng Viá»‡t
[14] Hugging Face Datasets - Nguá»“n dá»¯ liá»‡u luá»“ng

Lhoest, Q., et al. (2021). Datasets: A community library for natural language processing. EMNLP 2021.
arXiv: https://arxiv.org/abs/2109.02846
TÃ i liá»‡u streaming API: https://huggingface.co/docs/datasets/stream
ðŸ“Œ ÄÃ¡nh giÃ¡ Hiá»‡u nÄƒng & Há»‡ thá»‘ng
[15] Early-Exit trong Neural Networks (ná»n táº£ng lÃ½ thuyáº¿t)

Teerapittayanon, S., McDanel, B., & Kung, H. T. (2016). BranchyNet: Fast inference via early exiting from deep neural networks. ICPR 2016.
arXiv: https://arxiv.org/abs/1709.01686
[16] Memory-Mapped Files & SSD Random Access

TÃ i liá»‡u ká»¹ thuáº­t Microsoft / Linux: Memory-Mapped I/O and File Mapping.
URL: https://learn.microsoft.com/en-us/dotnet/standard/io/memory-mapped-files
[17] Beam Search & Greedy Graph Traversal

Harwood, B., & Drummond, T. (2016). FANNG: Fast approximate nearest neighbour graphs. CVPR 2016.
URL: https://openaccess.thecvf.com/content_cvpr_2016/papers/Harwood_FANNG_Fast_Approximate_CVPR_2016_paper.pdf

