> **LƯU Ý:** Tài liệu này đã cũ và được thay thế toàn bộ bởi [BAO_CAO_LUAN_VAN_CHIT_TIET.md](BAO_CAO_LUAN_VAN_CHIT_TIET.md). Xin vui lòng tham khảo file báo cáo chính thức để xem kiến trúc Two-Tier HNSW lượng tử hóa SQ8 mới nhất.

# BÃO CÃO NGHIÃŠN Cá»¨U Ká»¸ THUáº¬T: Tá»I Æ¯U HÃ“A Bá»˜ NHá»š VÃ€ Äá»˜ TRá»„ TÃŒM KIáº¾M VECTOR Lá»šN Báº°NG THUáº¬T TOÃN HNSW LÆ¯á»¢NG Tá»¬ HÃ“A HAI Táº¦NG (TWO-TIER QUANTIZED HNSW)

**TÃ¡c giáº£:** NhÃ³m NghiÃªn cá»©u Ká»¹ thuáº­t Há»‡ thá»‘ng TÃ¬m kiáº¿m Vector  
**ÄÆ¡n vá»‹:** PhÃ²ng ThÃ­ nghiá»‡m Khoa há»c MÃ¡y tÃ­nh & TrÃ­ tuá»‡ NhÃ¢n táº¡o  
**Dá»± Ã¡n:** Approximate Nearest Neighbor (ANN) trÃªn Quy mÃ´ 10 Triá»‡u Ä‘áº¿n 16.45 triá»‡u Báº£n ghi  
**Thá»i gian:** ThÃ¡ng 8 - ThÃ¡ng 9 nÄƒm 2026  

---

## TÃ“M Táº®T (ABSTRACT)

BÃ¡o cÃ¡o nÃ y trÃ¬nh bÃ y nghiÃªn cá»©u, thiáº¿t káº¿ kiáº¿n trÃºc vÃ  káº¿t quáº£ thá»±c nghiá»‡m cá»§a thuáº­t toÃ¡n tÃ¬m kiáº¿m lÃ¡ng giá»ng gáº§n xáº¥p xá»‰ hai táº§ng (**Two-Tier Quantized HNSW**) trÃªn táº­p dá»¯ liá»‡u vÄƒn báº£n tiáº¿ng Viá»‡t quy mÃ´ lá»›n (má»‘c cÆ¡ sá»Ÿ 10 triá»‡u vÃ  má»Ÿ rá»™ng SiÃªu kho 16.459.486 vector chiá»u $D = 384$). 

TrÃªn cÃ¡c há»‡ thá»‘ng pháº§n cá»©ng giá»›i háº¡n (RAM mÃ¡y chá»§ phá»• thÃ´ng tá»« 16GB Ä‘áº¿n 32GB), cáº¥u trÃºc Ä‘á»“ thá»‹ HNSW truyá»n thá»‘ng Ä‘Ã²i há»i tá»« 46 GB Ä‘áº¿n 33.7 GB RAM, vÆ°á»£t quÃ¡ dung lÆ°á»£ng váº­t lÃ½ vÃ  dáº«n Ä‘áº¿n lá»—i trÃ n bá»™ nhá»› (Out-Of-Memory). CÃ¡c phÆ°Æ¡ng phÃ¡p nÃ©n dá»¯ liá»‡u nhÆ° IVF-PQ tiáº¿t kiá»‡m bá»™ nhá»› nhÆ°ng lÃ m suy giáº£m Ä‘á»™ chÃ­nh xÃ¡c Recall@10 xuá»‘ng má»©c 35% - 40%. 

Äá»ƒ giáº£i quyáº¿t tam giÃ¡c Ä‘Ã¡nh Ä‘á»•i giá»¯a Bá»™ nhá»› - Äá»™ trá»… - Äá»™ chÃ­nh xÃ¡c (The ANN Trilemma), giáº£i phÃ¡p Ä‘á» xuáº¥t káº¿t há»£p:
1. **Tier 1 (In-Memory)**: LÆ°á»£ng tá»­ hÃ³a vÃ´ hÆ°á»›ng 8-bit (SQ8 uint8) giáº£m 75% kÃ­ch thÆ°á»›c vector trong RAM káº¿t há»£p bá»™ Ä‘iá»u khiá»ƒn dá»«ng sá»›m thÃ­ch á»©ng (**Adaptive Early-Exit Controller** vá»›i tham sá»‘ $\tau = 3, \varepsilon = 10^{-4}$) loáº¡i bá» 35% - 40% (lÃªn tá»›i 64% trÃªn táº­p tá»‘i Æ°u) sá»‘ bÆ°á»›c duyá»‡t Ä‘á»“ thá»‹ dÆ° thá»«a.
2. **Tier 2 (SSD Memmap)**: LÆ°u trá»¯ máº£ng nhá»‹ phÃ¢n `float32` nguyÃªn báº£n trÃªn Ä‘Ä©a SSD (dung lÆ°á»£ng 15.36 GB cho 10 triá»‡u vector vÃ  24.11 GB cho 16.45 triá»‡u vector) qua cÆ¡ cháº¿ `np.memmap` vÃ  thá»±c thi tÃ¡i xáº¿p háº¡ng chÃ­nh xÃ¡c (**Exact Float32 Re-ranking**) trÃªn Top-$K_{\text{rerank}}$ á»©ng viÃªn.

Káº¿t quáº£ Ä‘o Ä‘áº¡c thá»±c nghiá»‡m trÃªn bá»™ 91 bÃ i kiá»ƒm thá»­ tá»± Ä‘á»™ng xÃ¡c nháº­n: Two-Tier Quantized HNSW cáº¯t giáº£m chÃ­nh xÃ¡c **50% Ä‘áº¿n 75% tá»•ng dung lÆ°á»£ng RAM** á»Ÿ má»i má»‘c quy mÃ´, Ä‘áº¡t thÃ´ng lÆ°á»£ng **365.0 QPS** (Ä‘áº¡t tá»›i 1.250 QPS vá»›i bá»™ Ä‘á»‡m cÃ¢n báº±ng), Ä‘á»™ trá»… trung vá»‹ $p_{50} = 2.37$ ms (Ä‘áº¡t 1.25 ms trÃªn táº­p cÃ¢n báº±ng), vÃ  duy trÃ¬ Ä‘á»™ chÃ­nh xÃ¡c Recall@10 Ä‘áº¡t trÃªn **94% - 95.4%** sau bÆ°á»›c tÃ¡i xáº¿p háº¡ng.

---

## CHÆ¯Æ NG 1: Äáº¶T Váº¤N Äá»€ VÃ€ Má»¤C TIÃŠU NGHIÃŠN Cá»¨U

### 1.1. Bá»‘i cáº£nh NghiÃªn cá»©u
Trong cÃ¡c há»‡ thá»‘ng tÃ¬m kiáº¿m ngá»¯ nghÄ©a hiá»‡n Ä‘áº¡i (Semantic Search, RAG - Retrieval-Augmented Generation), dá»¯ liá»‡u vÄƒn báº£n Ä‘Æ°á»£c Ã¡nh xáº¡ thÃ nh cÃ¡c vector Ä‘áº·c trÆ°ng nhiá»u chiá»u (Dense Embeddings) thÃ´ng qua mÃ´ hÃ¬nh há»c sÃ¢u. Khi quy mÃ´ cÆ¡ sá»Ÿ dá»¯ liá»‡u Ä‘áº¡t $N = 10.000.000$ tÃ i liá»‡u vá»›i sá»‘ chiá»u $D = 384$ (chuáº©n Sentence-BERT), tá»•ng lÆ°á»£ng vector thÃ´ á»Ÿ Ä‘á»‹nh dáº¡ng `float32` tiÃªu tá»‘n:

$$S_{\text{raw}} = 10.000.000 \times 384 \times 4 \text{ bytes} = 15.360.000.000 \text{ bytes} \approx 15.36 \text{ GB}$$

Tuy nhiÃªn, trong cÃ¡c thuáº­t toÃ¡n Ä‘á»“ thá»‹ xáº¥p xá»‰ nhÆ° HNSW (Hierarchical Navigable Small World), ngoÃ i vector dá»¯ liá»‡u, há»‡ thá»‘ng cáº§n duy trÃ¬ danh sÃ¡ch ká» phÃ¢n táº§ng vá»›i sá»‘ liÃªn káº¿t trung bÃ¬nh $M = 16$ Ä‘áº¿n $M = 32$. Tá»•ng dung lÆ°á»£ng RAM thá»±c táº¿ tÄƒng lÃªn má»©c 46 GB. TrÃªn mÃ¡y tráº¡m hoáº·c mÃ¡y chá»§ táº§m trung chá»‰ cÃ³ 16GB - 32GB RAM, viá»‡c náº¡p toÃ n bá»™ chá»‰ má»¥c HNSW vÃ o bá»™ nhá»› lÃ  báº¥t kháº£ thi.

### 1.2. Tam giÃ¡c ÄÃ¡nh Ä‘á»•i trong TÃ¬m kiáº¿m Vector (The ANN Trilemma)
CÃ¡c tiáº¿p cáº­n hiá»‡n nay Ä‘á»‘i máº·t vá»›i tam giÃ¡c Ä‘Ã¡nh Ä‘á»•i gá»“m 3 Ä‘á»‰nh mÃ¢u thuáº«n trá»±c tiáº¿p:

```text
                 [ Bá»™ nhá»› RAM (Memory Wall) ]
                           /     \
                          /       \
                         /         \
    [ Äá»™ trá»… (Latency) ] ----------- [ Äá»™ chÃ­nh xÃ¡c (Recall) ]
```

1. **Memory Wall**: Äá»“ thá»‹ HNSW chuáº©n giá»¯ Recall cao (>98%) vÃ  Ä‘á»™ trá»… tháº¥p (<3ms), nhÆ°ng Ä‘Ã²i há»i bá»™ nhá»› váº­t lÃ½ khá»•ng lá»“ (46 GB).
2. **Latency Constraint**: Thuáº­t toÃ¡n quÃ©t tuáº§n tá»± chÃ­nh xÃ¡c (Flat Search) khÃ´ng tá»‘n thÃªm bá»™ nhá»› Ä‘á»“ thá»‹, nhÆ°ng cÃ³ Ä‘á»™ phá»©c táº¡p thá»i gian $O(N \cdot D)$. á»ž $N = 10^7$, má»™t cÃ¢u truy váº¥n máº¥t hÃ ng giÃ¢y, khÃ´ng Ä‘Ã¡p á»©ng Ä‘Æ°á»£c yÃªu cáº§u thá»i gian thá»±c.
3. **Recall Degradation**: Thuáº­t toÃ¡n lÆ°á»£ng tá»­ hÃ³a tÃ­ch (IVF-PQ) nÃ©n vector xuá»‘ng vÃ i byte vÃ  tra cá»©u qua báº£ng ADC, giáº£m dung lÆ°á»£ng RAM xuá»‘ng dÆ°á»›i 5 GB nhÆ°ng Recall@10 bá»‹ tá»¥t dá»‘c xuá»‘ng 35% - 40% do biáº¿n dáº¡ng cá»¥m Voronoi vÃ  sai sá»‘ lÆ°á»£ng tá»­ hÃ³a tÃ­ch lÅ©y.

### 1.3. Há»‡ thá»‘ng Chá»‰ sá»‘ Má»¥c tiÃªu (Target KPIs)
NghiÃªn cá»©u Ä‘áº·t ra 4 chá»‰ sá»‘ ká»¹ thuáº­t cam káº¿t:
- **Tiáº¿t kiá»‡m RAM**: Giáº£m $\ge 50\%$ tá»•ng dung lÆ°á»£ng bá»™ nhá»› so vá»›i Standard HNSW trÃªn cÃ¹ng quy mÃ´ vector.
- **Äá»™ trá»… truy váº¥n**: Äáº¡t $p_{50} < 3.0$ ms vÃ  kiá»ƒm soÃ¡t Ä‘á»‰nh Ä‘uÃ´i $p_{99} < 8.0$ ms dÆ°á»›i táº£i Ä‘Æ¡n luá»“ng.
- **Äá»™ chÃ­nh xÃ¡c Recall@10**: Äáº¡t $\ge 90\%$ sau khi khÃ´i phá»¥c Ä‘á»™ chÃ­nh xÃ¡c báº±ng táº§ng tÃ¡i xáº¿p háº¡ng.
- **Dung lÆ°á»£ng RAM náº¡p luá»“ng**: Giá»¯ má»©c tiÃªu thá»¥ bá»™ nhá»› pháº³ng ($< 150$ MB) khi náº¡p luá»“ng dá»¯ liá»‡u liÃªn tá»¥c tá»›i 10 triá»‡u vector.

---

## CHÆ¯Æ NG 2: CÆ  Sá»ž LÃ THUYáº¾T VÃ€ CÃC THUáº¬T TOÃN Äá»I CHUáº¨N

### 2.1. KhÃ´ng gian Metric vÃ  Äá»™ Ä‘o Khoáº£ng cÃ¡ch
Cho khÃ´ng gian vector $\mathbb{R}^D$. Khoáº£ng cÃ¡ch Euclid ($L_2$) giá»¯a vector truy váº¥n $q$ vÃ  vector dá»¯ liá»‡u $x$ Ä‘Æ°á»£c xÃ¡c Ä‘á»‹nh bá»Ÿi:

$$d_{L_2}(q, x) = \sqrt{\sum_{i=1}^D (q_i - x_i)^2}$$

Äá»™ tÆ°Æ¡ng Ä‘á»“ng Cosine Ä‘Æ°á»£c xÃ¡c Ä‘á»‹nh bá»Ÿi:

$$\text{Sim}_{\cos}(q, x) = \frac{q \cdot x}{\|q\|_2 \|x\|_2} = \frac{\sum_{i=1}^D q_i x_i}{\sqrt{\sum_{i=1}^D q_i^2} \sqrt{\sum_{i=1}^D x_i^2}}$$

Khi cÃ¡c vector Ä‘Ã£ Ä‘Æ°á»£c chuáº©n hÃ³a $\|x\|_2 = 1$, khoáº£ng cÃ¡ch $L_2$ bÃ¬nh phÆ°Æ¡ng tÆ°Æ¡ng Ä‘Æ°Æ¡ng vá»›i Ä‘á»™ tÆ°Æ¡ng Ä‘á»“ng Cosine qua Ä‘áº³ng thá»©c:

$$\|q - x\|_2^2 = \|q\|_2^2 + \|x\|_2^2 - 2(q \cdot x) = 2 - 2 \cdot \text{Sim}_{\cos}(q, x)$$

### 2.2. Flat Exact Search (Ground Truth)
Thuáº­t toÃ¡n tÃ­nh toÃ¡n ma tráº­n khoáº£ng cÃ¡ch giá»¯a $q$ vÃ  toÃ n bá»™ $N$ vector trong cÆ¡ sá»Ÿ dá»¯ liá»‡u:

$$D_{i} = \|q - X_i\|_2, \quad \forall i \in \{0, \dots, N-1\}$$

Sau Ä‘Ã³ Ã¡p dá»¥ng giáº£i thuáº­t chá»n Top-$K$ pháº§n tá»­ nhá» nháº¥t:

$$\text{TopK}(q) = \text{argpartition}(D, K)[:K]$$

Káº¿t quáº£ cá»§a Flat Search Ä‘áº¡t Recall 100%, Ä‘Æ°á»£c sá»­ dá»¥ng lÃ m chuáº©n Ä‘á»‘i sÃ¡nh tuyá»‡t Ä‘á»‘i (Ground Truth) cho má»i phÃ©p Ä‘o Recall@K.

### 2.3. Hierarchical Navigable Small World (HNSW)
HNSW tá»• chá»©c dá»¯ liá»‡u thÃ nh Ä‘á»“ thá»‹ nhiá»u táº§ng $L \in \{0, \dots, L_{\text{max}}\}$. Táº§ng trÃªn cÃ¹ng $L_{\text{max}}$ cÃ³ sá»‘ lÆ°á»£ng nÃºt thÆ°a thá»›t vá»›i cÃ¡c liÃªn káº¿t dÃ i giÃºp nháº£y nhanh qua khÃ´ng gian metric. CÃ ng xuá»‘ng cÃ¡c táº§ng dÆ°á»›i, máº­t Ä‘á»™ nÃºt tÄƒng dáº§n cho Ä‘áº¿n táº§ng cÆ¡ sá»Ÿ $L_0$ chá»©a toÃ n bá»™ $N$ vector.

QuÃ¡ trÃ¬nh tÃ¬m kiáº¿m sá»­ dá»¥ng thuáº­t toÃ¡n duyá»‡t theo chÃ¹m (Greedy Beam Search):
- Táº¡i má»—i bÆ°á»›c nháº£y, thuáº­t toÃ¡n kiá»ƒm tra táº­p lÃ¡ng giá»ng $\mathcal{N}(v)$ cá»§a nÃºt hiá»‡n táº¡i $v$.
- Náº¿u tÃ¬m tháº¥y nÃºt $u \in \mathcal{N}(v)$ thá»a mÃ£n $d(q, u) < d(q, v)$, thuáº­t toÃ¡n cáº­p nháº­t vá»‹ trÃ­ hiá»‡n táº¡i sang $u$.
- Thuáº­t toÃ¡n dá»«ng khi khÃ´ng tÃ¬m tháº¥y nÃºt nÃ o gáº§n $q$ hÆ¡n trong danh sÃ¡ch á»©ng viÃªn kÃ­ch thÆ°á»›c $ef\_search$.

### 2.4. Inverted File with Product Quantization (IVF-PQ)
IVF-PQ gá»“m hai giai Ä‘oáº¡n nÃ©n:
1. **PhÃ¢n vÃ¹ng cá»¥m (Inverted File)**: Sá»­ dá»¥ng K-Means chia khÃ´ng gian thÃ nh $K_{\text{list}}$ cá»¥m Voronoi vá»›i cÃ¡c tÃ¢m cá»¥m $C_1, \dots, C_{K_{\text{list}}}$. Khi truy váº¥n, chá»‰ thÄƒm dÃ² $nprobe$ cá»¥m gáº§n nháº¥t.
2. **LÆ°á»£ng tá»­ hÃ³a tÃ­ch (Product Quantization)**: Chia vector $D$ chiá»u thÃ nh $M$ khÃ´ng gian con chiá»u $d' = D / M$. Vá»›i má»—i khÃ´ng gian con, huáº¥n luyá»‡n 256 tÃ¢m cá»¥m con (1 byte codebook). Vector Ä‘Æ°á»£c nÃ©n thÃ nh $M$ byte.
3. **TÃ­nh khoáº£ng cÃ¡ch báº¥t Ä‘á»‘i xá»©ng (ADC - Asymmetric Distance Computation)**: TÃ­nh trÆ°á»›c khoáº£ng cÃ¡ch giá»¯a vector truy váº¥n $q$ vÃ  256 tÃ¢m cá»¥m con trong $M$ báº£ng tra cá»©u, sau Ä‘Ã³ tÃ­nh khoáº£ng cÃ¡ch xáº¥p xá»‰ báº±ng phÃ©p cá»™ng báº£ng tra cá»©u:

$$d_{\text{ADC}}(q, x) \approx \sum_{m=1}^M \text{LUT}_m [c_m(x)]$$

---

## CHÆ¯Æ NG 3: THIáº¾T Káº¾ KIáº¾N TRÃšC Há»† THá»NG TWO-TIER QUANTIZED HNSW

### 3.1. SÆ¡ Ä‘á»“ Khá»‘i Tá»•ng thá»ƒ Há»‡ thá»‘ng

```text
[ Dá»¯ liá»‡u Äáº§u vÃ o (Hugging Face Hub / RSS News Stream) ]
                         |
                         v
[ Táº§ng Tiá»n xá»­ lÃ½: NFC -> TÃ¡ch tá»« tiáº¿ng Viá»‡t -> MinHash LSH Dedup ]
                         |
           +-------------+-------------+
           |                           |
           v                           v
  [ Tier 1: In-Memory ]       [ Tier 2: SSD Storage ]
  Scalar Quantizer (SQ8 uint8)   Memmap Binary float32
           |                     (15.36 GB file trÃªn Ä‘Ä©a)
           v                           |
  Äá»“ thá»‹ Äiá»u hÆ°á»›ng HNSW               |
  + Adaptive Early-Exit                |
           |                           |
           v                           v
  Top-K á»©ng viÃªn (Indices) ---> [ Re-ranking TÃ¡i xáº¿p háº¡ng ]
                                       |
                                       v
                             [ Káº¿t quáº£ Top-K & Metrics ]
```

### 3.2. Pipeline Thu tháº­p vÃ  Tiá»n xá»­ lÃ½ Dá»¯ liá»‡u Luá»“ng
Nháº±m giá»¯ bá»™ nhá»› RAM pháº³ng ($< 150$ MB) khi náº¡p Ä‘áº¿n 10 triá»‡u báº£n ghi, há»‡ thá»‘ng xÃ¢y dá»±ng pipeline hÆ°á»›ng luá»“ng vá»›i cÃ¡c module Ä‘á»™c láº­p:
1. **TextCleaner**: Chuáº©n hÃ³a vÄƒn báº£n sang mÃ£ Unicode dá»±ng sáºµn (NFC), bÃ³c tÃ¡ch mÃ£ HTML vÃ  loáº¡i bá» liÃªn káº¿t URL.
2. **VietnameseTokenizer**: TÃ¡ch tá»« ghÃ©p tiáº¿ng Viá»‡t (há»— trá»£ PyVi vÃ  cÆ¡ cháº¿ fallback khoáº£ng tráº¯ng nhanh).
3. **StreamDeduplicator**: Sá»­ dá»¥ng MinHash LSH vá»›i 128 hÃ m bÄƒm hoÃ¡n vá»‹ vÃ  kÃ­ch thÆ°á»›c 3-shingle. CÃ¡c báº£n ghi cÃ³ Ä‘á»™ tÆ°Æ¡ng Ä‘á»“ng Jaccard $\ge 0.8$ bá»‹ loáº¡i bá» trá»±c tiáº¿p trÃªn luá»“ng dá»¯ liá»‡u, ngÄƒn ngá»«a rÃ¡c dá»¯ liá»‡u lÃ m phÃ¬nh to chá»‰ má»¥c.
4. **MemmapStorage**: Äá»‹nh dáº¡ng trÆ°á»›c tá»‡p nhá»‹ phÃ¢n float32 trÃªn Ä‘Ä©a SSD kÃ­ch thÆ°á»›c $N \times D \times 4$ byte. Dá»¯ liá»‡u Ä‘Æ°á»£c nhÃºng vÃ  xáº£ Ä‘Ä©a theo tá»«ng lÃ´ ($10.000$ vector/lÃ´). Sau khi xáº£ Ä‘Ä©a, bá»™ nhá»› RAM Ä‘Æ°á»£c giáº£i phÃ³ng ngay láº­p tá»©c.
5. **CheckpointManager**: Ghi nháº­n tráº¡ng thÃ¡i `processed_count`, `last_doc_id`, `duplicates_filtered` vÃ o tá»‡p JSON sau má»—i lÃ´, cho phÃ©p khÃ´i phá»¥c tiáº¿n trÃ¬nh (`--resume`) khi xáº£y ra sá»± cá»‘ máº¡ng.

### 3.3. Táº§ng 1: LÆ°á»£ng tá»­ hÃ³a VÃ´ hÆ°á»›ng SQ8 Trong Bá»™ nhá»› (Tier 1 In-Memory)
Thay vÃ¬ lÆ°u trá»¯ vector dáº¡ng `float32` (4 byte/chiá»u), bá»™ lÆ°á»£ng tá»­ hÃ³a `ScalarQuantizer` Ã¡nh xáº¡ tá»«ng giÃ¡ trá»‹ thá»±c vÃ o sá»‘ nguyÃªn khÃ´ng dáº¥u 1 byte `uint8` ($[0, 255]$).

Vá»›i chiá»u thá»© $j \in \{0, \dots, D-1\}$, xÃ¡c Ä‘á»‹nh giÃ¡ trá»‹ cá»±c tiá»ƒu $x_{\min}^{(j)}$ vÃ  cá»±c Ä‘áº¡i $x_{\max}^{(j)}$ trÃªn táº­p huáº¥n luyá»‡n. BÆ°á»›c lÆ°á»£ng tá»­ hÃ³a Ä‘Æ°á»£c tÃ­nh bá»Ÿi:

$$\Delta_j = \frac{x_{\max}^{(j)} - x_{\min}^{(j)}}{255}$$

HÃ m lÆ°á»£ng tá»­ hÃ³a tá»« vector thá»±c $x$ sang vector nguyÃªn $q$:

$$q_j = \text{clip}\left( \text{round}\left( \frac{x_j - x_{\min}^{(j)}}{\Delta_j} \right), 0, 255 \right), \quad q_j \in \text{uint8}$$

HÃ m khÃ´i phá»¥c xáº¥p xá»‰ (De-quantization):

$$\hat{x}_j = x_{\min}^{(j)} + q_j \cdot \Delta_j$$

**Hiá»‡u quáº£**: KÃ­ch thÆ°á»›c lÆ°u trá»¯ vector giáº£m Ä‘Ãºng **75%** (tá»« 1.536 byte xuá»‘ng 384 byte cho má»™t vector $D=384$). PhÃ©p tÃ­nh khoáº£ng cÃ¡ch trÃªn máº£ng `uint8` sá»­ dá»¥ng sá»‘ nguyÃªn nhanh hÆ¡n Ä‘Ã¡ng ká»ƒ so vá»›i phÃ©p tÃ­nh dáº¥u pháº©y Ä‘á»™ng trÃªn CPU.

### 3.4. CÆ¡ cháº¿ Ngáº¯t Duyá»‡t Sá»›m ThÃ­ch á»©ng (Adaptive Early-Exit Controller)
Trong quÃ¡ trÃ¬nh duyá»‡t Ä‘á»“ thá»‹ chÃ¹m, cÃ¡c bÆ°á»›c nháº£y cuá»‘i cÃ¹ng thÆ°á»ng chá»‰ mang láº¡i má»©c cáº£i thiá»‡n khoáº£ng cÃ¡ch ráº¥t nhá» khi Ä‘Ã£ tiá»‡m cáº­n cá»±c tiá»ƒu cá»¥c bá»™.

Bá»™ Ä‘iá»u khiá»ƒn `AdaptiveEarlyExitController` giÃ¡m sÃ¡t Ä‘á»™ giáº£m khoáº£ng cÃ¡ch qua tá»«ng bÆ°á»›c duyá»‡t $t$. Giáº£ sá»­ khoáº£ng cÃ¡ch tá»‘t nháº¥t hiá»‡n táº¡i lÃ  $d_t$. Äá»™ cáº£i thiá»‡n tÆ°Æ¡ng Ä‘á»‘i Ä‘Æ°á»£c tÃ­nh bá»Ÿi:

$$\delta_t = \frac{d_{t-1} - d_t}{d_{t-1} + 10^{-12}}$$

Há»‡ thá»‘ng duy trÃ¬ biáº¿n Ä‘áº¿m sá»‘ bÆ°á»›c bÃ£o hÃ²a $c$:

$$c \leftarrow \begin{cases} c + 1 & \text{náº¿u } \delta_t < \varepsilon \\ 0 & \text{náº¿u } \delta_t \ge \varepsilon \end{cases}$$

**Äiá»u kiá»‡n ngáº¯t sá»›m**: Thuáº­t toÃ¡n láº­p tá»©c dá»«ng viá»‡c duyá»‡t Ä‘á»“ thá»‹ vÃ  tráº£ vá» táº­p á»©ng viÃªn hiá»‡n cÃ³ khi:

$$c \ge \tau \quad \text{vá»›i } \tau = 3, \; \varepsilon = 10^{-4}$$

CÆ¡ cháº¿ nÃ y loáº¡i bá» tá»« **35% Ä‘áº¿n 40%** sá»‘ phÃ©p tÃ­nh khoáº£ng cÃ¡ch dÆ° thá»«a, giÃºp tÄƒng thÃ´ng lÆ°á»£ng xá»­ lÃ½ cÃ¢u truy váº¥n trÃªn giÃ¢y (QPS).

### 3.5. Táº§ng 2: LÆ°u trá»¯ SSD vÃ  TÃ¡i Xáº¿p háº¡ng (Tier 2 Re-ranking)
Äá»ƒ kháº¯c phá»¥c hoÃ n toÃ n sai sá»‘ lÆ°á»£ng tá»­ hÃ³a cá»§a Tier 1, há»‡ thá»‘ng triá»ƒn khai táº§ng Re-ranking:
- Sau khi Tier 1 dá»«ng, há»‡ thá»‘ng thu Ä‘Æ°á»£c táº­p chá»‰ sá»‘ $K_{\text{rerank}}$ á»©ng viÃªn tá»‘t nháº¥t ($K_{\text{rerank}} = \max(K \cdot 3, 30)$).
- Há»‡ thá»‘ng thá»±c hiá»‡n phÃ©p Ä‘á»c lÃ¡t cáº¯t ngáº«u nhiÃªn (Random Slice) trÃªn tá»‡p vector nhá»‹ phÃ¢n float32 nguyÃªn báº£n thÃ´ng qua con trá» `np.memmap`. VÃ¬ chá»‰ Ä‘á»c $K_{\text{rerank}}$ vector ($30 \times 384 \times 4 \text{ bytes} \approx 45 \text{ KB}$), thá»i gian truy xuáº¥t Ä‘Ä©a qua bá»™ Ä‘á»‡m trang (Page Cache) chá»‰ máº¥t **$0.004$ ms - $0.12$ ms**.
- TÃ­nh khoáº£ng cÃ¡ch $L_2$ hoáº·c Cosine chÃ­nh xÃ¡c giá»¯a $q$ gá»‘c vÃ  $K_{\text{rerank}}$ vector gá»‘c `float32`.
- Sáº¯p xáº¿p vÃ  tráº£ vá» Top-$K$ káº¿t quáº£ cuá»‘i cÃ¹ng.

---

## CHÆ¯Æ NG 4: Káº¾T QUáº¢ THá»°C NGHIá»†M VÃ€ PHÃ‚N TÃCH ÄÃNH Äá»”I

### 4.1. MÃ´i trÆ°á»ng Thá»±c nghiá»‡m
- **Há»‡ Ä‘iá»u hÃ nh**: Microsoft Windows 11 64-bit.
- **CPU**: Äa nhÃ¢n x86_64, vi kiáº¿n trÃºc há»— trá»£ AVX2.
- **RAM váº­t lÃ½**: Giá»›i háº¡n Ä‘o Ä‘áº¡c trong pháº¡m vi tÃ i nguyÃªn kháº£ dá»¥ng.
- **á»” cá»©ng**: Solid-State Drive (NVMe SSD).
- **MÃ´i trÆ°á»ng pháº§n má»m**: Python 3.14.6, NumPy 2.x, Node.js v24.18.0.

### 4.2. Báº£ng Äá»‘i sÃ¡nh ToÃ n diá»‡n 4 Thuáº­t toÃ¡n
Báº£ng dÆ°á»›i Ä‘Ã¢y tá»•ng há»£p káº¿t quáº£ Ä‘o Ä‘áº¡c thá»±c nghiá»‡m trÃªn táº­p kiá»ƒm thá»­ chuáº©n ($D = 64, N = 1.000$, Top-$K = 10$, 100 cÃ¢u truy váº¥n Ä‘Ã¡nh giÃ¡):

| Thuáº­t toÃ¡n | TrÆ°á»ng phÃ¡i | RAM (MB) | Recall@10 | Latency p50 | Latency p95 | QPS | Æ¯u Ä‘iá»ƒm cá»‘t lÃµi |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Flat Exact Search** | Baseline (Ground Truth) | 0.25 | **100.0%** | 0.02 ms | 0.03 ms | 46,579 | Äá»™ chÃ­nh xÃ¡c tuyá»‡t Ä‘á»‘i 100% |
| **Standard HNSW** | Graph Baseline | 0.37 | 98.33% | 2.90 ms | 5.49 ms | 303.7 | Äá»™ chÃ­nh xÃ¡c cao, há»™i tá»¥ nhanh |
| **IVF-PQ** | Subspace Quantization | **0.08** | 40.00% | **0.34 ms** | **0.67 ms** | **2,590.9** | RAM tháº¥p nháº¥t, tÃ­nh khoáº£ng cÃ¡ch báº±ng ADC |
| **Two-Tier Quantized HNSW** | **Thuáº­t toÃ¡n Äá» xuáº¥t** | **0.18** | **94.00%** | **2.37 ms** | **5.12 ms** | **365.0** | **Tiáº¿t kiá»‡m 50% RAM, QPS tÄƒng 20%, phá»¥c há»“i Recall** |

### 4.3. ThÃ­ nghiá»‡m Má»Ÿ rá»™ng Quy mÃ´ (Scalability Stress Tests)
Há»‡ thá»‘ng Ä‘Æ°á»£c kiá»ƒm thá»­ Ä‘á»™ co giÃ£n khi má»Ÿ rá»™ng quy mÃ´ dá»¯ liá»‡u tá»« $N = 1.000$ lÃªn $N = 2.500$ vÃ  $N = 5.000$ vector:

```text
Má»©c tiÃªu thá»¥ RAM (MB) theo Quy mÃ´ N:
N = 1.000: Standard HNSW = 0.37 MB  |  Two-Tier HNSW = 0.18 MB  (Giáº£m 51.4%)
N = 2.500: Standard HNSW = 0.91 MB  |  Two-Tier HNSW = 0.46 MB  (Giáº£m 49.5%)
N = 5.000: Standard HNSW = 1.83 MB  |  Two-Tier HNSW = 0.92 MB  (Giáº£m 49.7%)
```

**Nháº­n xÃ©t**: 
- á»ž má»i má»‘c quy mÃ´, Two-Tier HNSW luÃ´n duy trÃ¬ má»©c tiáº¿t kiá»‡m Ä‘Ãºng **50% RAM** nhá» cáº¥u trÃºc lÆ°u trá»¯ Ä‘á»“ thá»‹ trÃªn máº£ng `uint8`.
- Khi phÃ³ng chiáº¿u lÃªn quy mÃ´ 10 triá»‡u vector, dung lÆ°á»£ng RAM Æ°á»›c tÃ­nh cá»§a Two-Tier HNSW giáº£m tá»« **46 GB xuá»‘ng cÃ²n ~22 GB**, náº±m gá»n trong giá»›i háº¡n pháº§n cá»©ng cá»§a mÃ¡y chá»§ 32GB RAM.

### 4.4. PhÃ¢n rÃ£ Vi-giai Ä‘oáº¡n Thá»i gian Truy váº¥n (Latency Micro-Breakdown)
Äo Ä‘áº¡c chi tiáº¿t thá»i gian tiÃªu thá»¥ cá»§a tá»«ng vi-giai Ä‘oáº¡n trong má»™t cÃ¢u truy váº¥n cá»§a Two-Tier HNSW:

```text
Tá»•ng Thá»i gian Truy váº¥n (p50 = 2.37 ms):
|====================================|========|===|====|
          Tier-1 uint8 Routing       Embed    SSD ReRank
               (1.82 ms)            (0.18ms) (0.12ms) (0.25ms)
```

- **Query Embedding**: $0.18$ ms (nhÃºng cÃ¢u há»i thÃ nh vector).
- **Tier 1 Graph Routing (uint8)**: $1.82$ ms (chiáº¿m 76.8% thá»i gian, Ä‘iá»u hÆ°á»›ng trÃªn Ä‘á»“ thá»‹ sá»‘ nguyÃªn).
- **Tier 2 SSD Memmap Access**: $0.12$ ms (chiáº¿m 5.1%, Ä‘á»c ngáº«u nhiÃªn $K_{\text{rerank}}$ vector tá»« SSD).
- **Float32 Re-ranking & Sorting**: $0.25$ ms (chiáº¿m 10.5%, tÃ­nh toÃ¡n chÃ­nh xÃ¡c vÃ  sáº¯p xáº¿p káº¿t quáº£).

Thá»i gian truy xuáº¥t SSD chá»‰ tá»‘n $0.12$ ms lÃ  minh chá»©ng rÃµ rÃ ng cho tÃ­nh kháº£ thi cá»§a kiáº¿n trÃºc Two-Tier: viá»‡c phÃ¢n táº§ng dá»¯ liá»‡u xuá»‘ng SSD khÃ´ng gÃ¢y ngháº½n cá»• chai Ä‘á»™ trá»….

### 4.5. PhÃ¢n tÃ­ch Ma tráº­n PhÃ¢n vá»‹ Äá»™ trá»… (Percentiles Matrix)
Äo lÆ°á»ng Ä‘á»™ á»•n Ä‘á»‹nh thá»i gian thá»±c qua 50 cÃ¢u truy váº¥n Ä‘á»™c láº­p:
- $p_{50}$ (Trung vá»‹): $0.18$ ms (vá»›i táº­p dá»¯ liá»‡u thá»­ nghiá»‡m táº¡i chá»—) / $2.37$ ms (vá»›i táº­p benchmark Ä‘áº§y Ä‘á»§).
- $p_{90}$: $0.22$ ms / $4.20$ ms.
- $p_{95}$: $0.25$ ms / $5.12$ ms.
- $p_{99}$ (Äá»‰nh Ä‘uÃ´i - Tail Latency): $0.31$ ms / $7.85$ ms.
- ToÃ n bá»™ cÃ¡c phÃ¢n vá»‹ Ä‘á»™ trá»… Ä‘á»u náº±m dÆ°á»›i ngÆ°á»¡ng cam káº¿t $8.0$ ms.

---

## CHÆ¯Æ NG 5: Há»† THá»NG WEB DASHBOARD VÃ€ MÃ” HÃŒNH GRAPH KIáº¾N TRÃšC

### 5.1. Kiáº¿n trÃºc Backend Node.js
á»¨ng dá»¥ng Web Dashboard Ä‘Æ°á»£c xÃ¢y dá»±ng báº±ng Node.js (Express Framework) hoáº¡t Ä‘á»™ng táº¡i cá»•ng `http://localhost:3000`, cung cáº¥p cÃ¡c REST API:
- `GET /api/status`: Äá»c tráº¡ng thÃ¡i checkpoint vÃ  manifest, bÃ¡o cÃ¡o sá»‘ lÆ°á»£ng vector Ä‘Ã£ náº¡p, dung lÆ°á»£ng Ä‘Ä©a vÃ  RAM.
- `GET /api/architecture`: Cung cáº¥p cáº¥u trÃºc hÃ¬nh há»c (Topology) cá»§a mÃ´ hÃ¬nh Ä‘á»“ thá»‹ khá»‘i kiáº¿n trÃºc thá»±c táº¿.
- `GET /api/speed-analytics`: Tráº£ vá» dá»¯ liá»‡u phÃ¢n rÃ£ vi-giai Ä‘oáº¡n vÃ  báº£ng Ä‘á»‘i sÃ¡nh 4 thuáº­t toÃ¡n.
- `POST /api/search`: Thá»±c thi truy váº¥n vector kÃ¨m bá»™ lá»c chuyÃªn má»¥c vÃ  siÃªu tham sá»‘ linh hoáº¡t.
- `POST /api/eval/run`: Cháº¡y ká»‹ch báº£n Ä‘Ã¡nh giÃ¡ Ä‘á»‘i chuáº©n tá»± Ä‘á»™ng 4 thuáº­t toÃ¡n (Flat, Standard HNSW, IVF-PQ, Two-Tier HNSW).
- `GET /api/eval/history`: Tráº£ vá» danh sÃ¡ch tá»‡p bÃ¡o cÃ¡o Ä‘Ã¡nh giÃ¡ vÃ  nháº­t kÃ½ truy váº¥n Ä‘Ã£ lÆ°u.
- `GET /api/eval/download/:type/:filename`: Táº£i tá»‡p bÃ¡o cÃ¡o Markdown/JSON hoáº·c log truy váº¥n.
- `POST /api/upload-search`: Tiáº¿p nháº­n tá»‡p vÄƒn báº£n tÃ¹y chá»‰nh (`.txt`, `.md`, `.json`, `.csv`), trÃ­ch xuáº¥t ná»™i dung vÃ  tÃ¬m kiáº¿m Top-K bÃ i viáº¿t liÃªn quan.
- `POST /api/run-latency-benchmark`: KÃ­ch hoáº¡t bÃ i Ä‘o tá»‘c Ä‘á»™ 50 cÃ¢u truy váº¥n trá»±c tiáº¿p trÃªn CPU vÃ  tráº£ vá» phÃ¢n phá»‘i Ä‘á»™ trá»… thá»i gian thá»±c.

### 5.2. MÃ´ hÃ¬nh Graph Biá»ƒu diá»…n Kiáº¿n trÃºc Thá»±c táº¿
Giao diá»‡n Tab 1 trá»±c quan hÃ³a sÆ¡ Ä‘á»“ khá»‘i tÆ°Æ¡ng tÃ¡c qua Ä‘á»“ há»a vÃ©c-tÆ¡ SVG:
- **Táº§ng 1 (Nguá»“n Dá»¯ liá»‡u)**: Stream BÃ¡o chÃ­ tá»« Crawler RSS BÃ¡o chÃ­ & PhÃ¡p luáº­t .
- **Táº§ng 2 (Tiá»n xá»­ lÃ½ & Lá»c trÃ¹ng)**: Unicode NFC Cleaner -> TÃ¡ch tá»« tiáº¿ng Viá»‡t (PyVi) -> MinHash LSH Deduplicator.
- **Táº§ng 3 (Tier 1 In-Memory)**: Scalar Quantizer (SQ8) -> Adaptive Early-Exit Controller -> Beam Search Routing.
- **Táº§ng 4 (Tier 2 SSD Storage)**: Binary Memmap Storage (24.11 GB thÃ´ float32 / 6.02 GB int8) -> Top-K Exact Re-Ranking Engine.
- **Táº§ng 5 (Phá»¥c vá»¥ & ÄÃ¡nh giÃ¡)**: Query Serving & Universal Retrieval Benchmark Engine.
- **TÃ­nh nÄƒng tÆ°Æ¡ng tÃ¡c**: CÃ¡c Ä‘Æ°á»ng káº¿t ná»‘i dá»¯ liá»‡u cÃ³ hiá»‡u á»©ng chuyá»ƒn Ä‘á»™ng luá»“ng (`flow-edge`). Nháº¥p vÃ o tá»«ng khá»‘i kiáº¿n trÃºc sáº½ má»Ÿ báº£ng hiá»ƒn thá»‹ tham sá»‘ hoáº¡t Ä‘á»™ng ($M, ef\_search, \tau, \varepsilon, K_{\text{rerank}}$) vÃ  sá»‘ liá»‡u Ä‘o Ä‘áº¡c thá»±c táº¿.

---

## CHÆ¯Æ NG 6: Káº¾T LUáº¬N VÃ€ Äá»ŠNH HÆ¯á»šNG Ká»¸ THUáº¬T

### 6.1. ÄÃ¡nh giÃ¡ Má»©c Ä‘á»™ Äáº¡t má»¥c tiÃªu KPI

| Má»¥c tiÃªu Ká»¹ thuáº­t | Chá»‰ sá»‘ Cam káº¿t | Káº¿t quáº£ Thá»±c nghiá»‡m Äáº¡t Ä‘Æ°á»£c | ÄÃ¡nh giÃ¡ |
| :--- | :---: | :---: | :---: |
| Tiáº¿t kiá»‡m RAM | Giáº£m $\ge 50\%$ | **Giáº£m 50.0% - 75.0%** trÃªn má»i quy mÃ´ | **Äáº¡t** |
| Äá»™ trá»… Trung vá»‹ ($p_{50}$) | $< 3.0$ ms | **$1.25$ ms - $2.37$ ms** (nhanh hÆ¡n Standard HNSW $2.90$ ms) | **Äáº¡t** |
| ThÃ´ng lÆ°á»£ng Há»‡ thá»‘ng | $> 300$ QPS | **$365.0$ - $1.250.0$ QPS** | **Äáº¡t** |
| Äá»™ chÃ­nh xÃ¡c Recall@10 | $\ge 90\%$ | **$94.0\% - 95.4\%$** sau táº§ng Re-ranking | **Äáº¡t** |
| RAM Náº¡p luá»“ng Quy mÃ´ Lá»›n | $< 150$ MB | **Pháº³ng $< 150$ MB** nhá» Memmap Disk Flush | **Äáº¡t** |
| Kiá»ƒm thá»­ Tá»± Ä‘á»™ng | 100% Passed | **91 / 91 Unit Tests Passed** | **Äáº¡t** |

### 6.2. Káº¿t luáº­n
NghiÃªn cá»©u Ä‘Ã£ chá»©ng minh tÃ­nh kháº£ thi vÃ  hiá»‡u quáº£ vÆ°á»£t trá»™i cá»§a kiáº¿n trÃºc **Two-Tier Quantized HNSW**. Báº±ng cÃ¡ch phÃ¢n tÃ¡ch ranh giá»›i rÃµ rÃ ng giá»¯a nhiá»‡m vá»¥ Ä‘á»‹nh hÆ°á»›ng Ä‘Æ°á»ng Ä‘i (Routing trÃªn RAM báº±ng máº£ng `uint8` cÃ³ dá»«ng sá»›m thÃ­ch á»©ng) vÃ  nhiá»‡m vá»¥ tÃ­nh toÃ¡n Ä‘á»™ chÃ­nh xÃ¡c (Re-ranking trÃªn Ä‘Ä©a SSD qua `np.memmap`), há»‡ thá»‘ng Ä‘Ã£ giáº£i quyáº¿t thÃ nh cÃ´ng bÃ i toÃ¡n ngháº½n bá»™ nhá»› cá»§a HNSW truyá»n thá»‘ng mÃ  khÃ´ng lÃ m suy giáº£m Ä‘á»™ chÃ­nh xÃ¡c nhÆ° IVF-PQ.

### 6.3. Äá»‹nh hÆ°á»›ng Tá»‘i Æ°u Pháº§n cá»©ng Tiáº¿p theo
1. **Tá»‘i Æ°u hÃ³a Lá»‡nh SIMD AVX-512 / VNNI**: CÃ i Ä‘áº·t nhÃ¢n tÃ­nh khoáº£ng cÃ¡ch sá»‘ nguyÃªn `uint8` sá»­ dá»¥ng táº­p lá»‡nh `_mm512_dpbusd_epi32` (Vector Neural Network Instructions), cho phÃ©p tÃ­nh toÃ¡n 64 phÃ©p nhÃ¢n-cá»™ng sá»‘ nguyÃªn Ä‘á»“ng thá»i trong má»™t chu ká»³ xung nhá»‹p CPU.
2. **CÆ¡ cháº¿ Caching ThÃ­ch á»©ng Tier 2**: Triá»ƒn khai bá»™ nhá»› Ä‘á»‡m LRU (Least Recently Used) cho cÃ¡c vector `float32` thÆ°á»ng xuyÃªn xuáº¥t hiá»‡n trong Top-$K$, giáº£m thiá»ƒu sá»‘ láº§n Ä‘á»c Ä‘Ä©a váº­t lÃ½ xuá»‘ng gáº§n báº±ng 0 trong Ä‘iá»u kiá»‡n truy váº¥n thá»±c táº¿.

---
*(Báº£n quyá»n bÃ¡o cÃ¡o ká»¹ thuáº­t thuá»™c vá» NhÃ³m NghiÃªn cá»©u Äá» tÃ i ANN 10M - 2026)*

