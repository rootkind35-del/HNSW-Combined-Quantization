> **LƯU Ý:** Tài liệu này đã cũ và được thay thế toàn bộ bởi [BAO_CAO_LUAN_VAN_CHIT_TIET.md](BAO_CAO_LUAN_VAN_CHIT_TIET.md). Xin vui lòng tham khảo file báo cáo chính thức để xem kiến trúc Two-Tier HNSW lượng tử hóa SQ8 mới nhất.

# BÃ¡o cÃ¡o Ká»¹ thuáº­t Chi tiáº¿t: Luá»“ng Xá»­ lÃ½ Dá»¯ liá»‡u vÃ  LÆ°á»£ng tá»­ hÃ³a Vector (Quantization Pipeline)

TÃ i liá»‡u nÃ y Ä‘Æ°á»£c biÃªn soáº¡n dÃ nh cho ká»¹ sÆ° má»›i nháº±m giáº£i thÃ­ch báº£n cháº¥t toÃ¡n há»c, kiáº¿n trÃºc pháº§n má»m, nguyÃªn lÃ½ tá»‘i Æ°u hÃ³a pháº§n cá»©ng GPU vÃ  chi tiáº¿t tá»«ng hÃ m trong luá»“ng xá»­ lÃ½ vÃ  lÆ°á»£ng tá»­ hÃ³a vector quy mÃ´ lá»›n.

---

## 1. Tá»•ng quan Kiáº¿n trÃºc Luá»“ng LÆ°á»£ng tá»­ hÃ³a

Trong cÃ¡c há»‡ thá»‘ng tÃ¬m kiáº¿m ngá»¯ nghÄ©a quy mÃ´ hÃ ng chá»¥c triá»‡u báº£n ghi, viá»‡c lÆ°u trá»¯ vector dáº¡ng dáº¥u pháº©y Ä‘á»™ng 32-bit (`float32`) trá»±c tiáº¿p trÃªn RAM lÃ  khÃ´ng kháº£ thi:
- 10 triá»‡u vector 384 chiá»u kiá»ƒu `float32` tiÃªu tá»‘n:
  $$10.000.000 \times 384 \times 4 \text{ bytes} = 15.360.000.000 \text{ bytes} \approx 15,36 \text{ GB RAM}$$
- Khi má»Ÿ rá»™ng lÃªn 16,5 triá»‡u vector (sau khi phÃ¢n tÃ¡ch chunk), dung lÆ°á»£ng RAM yÃªu cáº§u vÆ°á»£t quÃ¡ **24,11 GB**, gÃ¢y trÃ n bá»™ nhá»› trÃªn háº§u háº¿t cÃ¡c mÃ¡y chá»§ tiÃªu chuáº©n.

**Giáº£i phÃ¡p LÆ°á»£ng tá»­ hÃ³a VÃ´ hÆ°á»›ng 8-bit (Scalar Quantization - SQ8):**
NÃ©n má»—i chiá»u khÃ´ng gian tá»« 4 bytes (`float32`) xuá»‘ng Ä‘Ãºng 1 byte (`int8`), giáº£m **75% dung lÆ°á»£ng bá»™ nhá»›**, Ä‘Æ°a toÃ n bá»™ kho 16,5 triá»‡u vector vá» má»©c **6,32 GB**, cÃ³ thá»ƒ Ã¡nh xáº¡ bá»™ nhá»› (`numpy.memmap`) vÃ  tÃ¬m kiáº¿m thá»i gian thá»±c vá»›i Ä‘á»™ suy hao ngá»¯ nghÄ©a (Cosine Similarity Loss) dÆ°á»›i $0,5\%$.

```mermaid
flowchart TD
    subgraph Input ["Äáº§u vÃ o Shard ToÃ n vÄƒn"]
        S["CÃ¡c tá»‡p Shard JSONL<br/>(data/crawl/ hoáº·c data/crawl_wiki/)"]
    end

    subgraph Step1 ["BÆ°á»›c 1: PhÃ¢n Ä‘oáº¡n Ngá»¯ cáº£nh"]
        TC["TextChunker (src/quantizer/chunker.py)<br/>â€¢ Window: 300 tá»«<br/>â€¢ Overlap: 50 tá»« gá»‘i Ä‘áº§u<br/>â€¢ Giá»¯ nguyÃªn cáº¥u trÃºc vÄƒn báº£n"]
    end

    subgraph Step2 ["BÆ°á»›c 2: NhÃºng Ngá»¯ nghÄ©a GPU"]
        EM["SentenceTransformerEmbedder (src/ann_data/embedder.py)<br/>â€¢ Model: paraphrase-multilingual-MiniLM-L12-v2<br/>â€¢ NVIDIA RTX 4060 GPU (CUDA)<br/>â€¢ Batch size: 512 (~2.670 vecs/s)"]
    end

    subgraph Step3 ["BÆ°á»›c 3: LÆ°á»£ng tá»­ hÃ³a VÃ´ hÆ°á»›ng"]
        SQ["ScalarQuantizer8 (src/quantizer/sq8.py)<br/>â€¢ Fit min/max per dimension<br/>â€¢ Linear projection: float32 -> int8 [-128, 127]<br/>â€¢ Giáº£m 75% RAM"]
    end

    subgraph Step4 ["BÆ°á»›c 4: LÆ°u trá»¯ Memmap & SiÃªu dá»¯ liá»‡u"]
        QS["QuantizedStorage (src/quantizer/storage.py)<br/>â€¢ vectors_int8.dat (nhá»‹ phÃ¢n memmap)<br/>â€¢ metadata.jsonl (tra cá»©u toÃ n vÄƒn)<br/>â€¢ quantization_params.json<br/>â€¢ Checkpoint & Manifest"]
    end

    subgraph SearchEngine ["BÆ°á»›c 5: TÃ¬m kiáº¿m Ngá»¯ nghÄ©a Thá»i gian thá»±c"]
        SE["SemanticSearchEngine (src/ann_data/search/semantic_engine.py)<br/>â€¢ Scaled dot-product trÃªn vector int8<br/>â€¢ QuÃ©t 16+ triá»‡u vector trong < 1.5 giÃ¢y<br/>â€¢ Single-pass metadata retrieval"]
    end

    S --> TC --> EM --> SQ --> QS --> SearchEngine
```

---

## 2. Ná»n táº£ng ToÃ¡n há»c cá»§a Thuáº­t toÃ¡n Scalar Quantization (SQ8)

### 2.1. CÃ´ng thá»©c nÃ©n (Quantization)
Cho máº£ng vector Ä‘áº·c trÆ°ng Ä‘áº§u vÃ o $X \in \mathbb{R}^{N \times D}$ ($D = 384$). Vá»›i má»—i chiá»u khÃ´ng gian $d \in [0, D-1]$:
1. TÃ¬m giÃ¡ trá»‹ nhá» nháº¥t vÃ  lá»›n nháº¥t trÃªn táº­p huáº¥n luyá»‡n máº«u:
   $$\min_d = \min_{i} X_{i, d}, \quad \max_d = \max_{i} X_{i, d}$$
2. XÃ¡c Ä‘á»‹nh há»‡ sá»‘ co giÃ£n (Scaling factor) phÃ¢n bá»‘ Ä‘á»u trÃªn 255 má»©c:
   $$\text{scale}_d = \frac{\max_d - \min_d}{255.0}$$
3. Chuyá»ƒn Ä‘á»•i giÃ¡ trá»‹ liÃªn tá»¥c $x \in [\min_d, \max_d]$ sang sá»‘ nguyÃªn cÃ³ dáº¥u 8-bit $q \in [-128, 127]$:
   $$\text{norm}_d = \text{clip}\left(\frac{x - \min_d}{\text{scale}_d}, 0, 255\right)$$
   $$q = \text{round}(\text{norm}_d) - 128$$

### 2.2. CÃ´ng thá»©c khÃ´i phá»¥c (Dequantization)
Khi cáº§n tÃ¡i táº¡o láº¡i vector xáº¥p xá»‰ $\hat{x} \in \mathbb{R}$ tá»« sá»‘ nguyÃªn $q \in [-128, 127]$:
$$\hat{x} = (q + 128) \times \text{scale}_d + \min_d$$

### 2.3. Tá»‘i Æ°u hÃ³a tÃ­nh tÃ­ch vÃ´ hÆ°á»›ng (Inner Product Acceleration)
Khi thá»±c hiá»‡n truy váº¥n vá»›i vector cÃ¢u há»i $Q \in \mathbb{R}^D$ vÃ  vector tÃ i liá»‡u Ä‘Ã£ lÆ°á»£ng tá»­ hÃ³a $V_{\text{int8}} \in \mathbb{Z}^D$:
$$\langle Q, \hat{V} \rangle = \sum_{d=0}^{D-1} Q_d \cdot \left[(V_{\text{int8}, d} + 128) \cdot \text{scale}_d + \min_d\right]$$
Biáº¿n Ä‘á»•i Ä‘áº¡i sá»‘:
$$\langle Q, \hat{V} \rangle = \sum_{d=0}^{D-1} \underbrace{(Q_d \cdot \text{scale}_d)}_{Q'_d} \cdot V_{\text{int8}, d} + \underbrace{\sum_{d=0}^{D-1} Q_d \cdot (128 \cdot \text{scale}_d + \min_d)}_{\text{Háº±ng sá»‘ } C_Q \text{ tÃ­nh 1 láº§n duy nháº¥t}}$$
Nhá» biáº¿n Ä‘á»•i nÃ y, cÃ¢u truy váº¥n chá»‰ cáº§n nhÃ¢n trÆ°á»›c vá»›i $\text{scale}_d$ Ä‘á»ƒ táº¡o ra $Q'$, sau Ä‘Ã³ phÃ©p tÃ­nh khoáº£ng cÃ¡ch trÃªn hÃ ng triá»‡u vector trá»Ÿ thÃ nh **phÃ©p nhÃ¢n ma tráº­n sá»‘ nguyÃªn siÃªu tá»‘c (BLAS dot product)**, loáº¡i bá» hoÃ n toÃ n chi phÃ­ giáº£i nÃ©n tá»«ng vector.

---

## 3. PhÃ¢n tÃ­ch Chi tiáº¿t Tá»«ng Module MÃ£ Nguá»“n

### 3.1. PhÃ¢n Ä‘oáº¡n vÄƒn báº£n: `src/quantizer/chunker.py`

#### Má»¥c Ä‘Ã­ch vÃ  vai trÃ²
CÃ¡c mÃ´ hÃ¬nh Transformer nhÆ° MiniLM cÃ³ giá»›i háº¡n cá»­a sá»• ngá»¯ cáº£nh (Context Length) tá»‘i Ä‘a 256 - 512 tokens. Náº¿u Ä‘Æ°a cáº£ bÃ i bÃ¡o dÃ i 3.000 tá»« vÃ o, mÃ´ hÃ¬nh sáº½ tá»± Ä‘á»™ng cáº¯t bá» pháº§n Ä‘uÃ´i bÃ i viáº¿t. `TextChunker` Ä‘áº£m báº£o má»i phÃ¢n Ä‘oáº¡n cá»§a bÃ i viáº¿t Ä‘á»u Ä‘Æ°á»£c láº­p chá»‰ má»¥c Ä‘áº§y Ä‘á»§.

#### CÃ¡c thÃ nh pháº§n chÃ­nh trong `TextChunker`
```python
class TextChunker:
    def __init__(self, chunk_size: int = 300, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
```
- **HÃ m `chunk_document(self, doc_id, title, full_text)`:**
  - TÃ¡ch vÄƒn báº£n thÃ nh danh sÃ¡ch tá»«: `words = full_text.split()`.
  - Náº¿u `total_words <= chunk_size` (300 tá»«): Tráº£ vá» 1 chunk duy nháº¥t vá»›i chá»‰ sá»‘ `_c0`.
  - Náº¿u bÃ i viáº¿t dÃ i: DÃ¹ng cá»­a sá»• trÆ°á»£t vá»›i bÆ°á»›c nháº£y $\text{step} = \text{chunk\_size} - \text{chunk\_overlap} = 300 - 50 = 250$ tá»«.
  - *Táº¡i sao cáº§n vÃ¹ng gá»‘i Ä‘áº§u (overlap 50 tá»«)?* Náº¿u má»™t cÃ¢u vÄƒn quan trá»ng náº±m Ä‘Ãºng ranh giá»›i cáº¯t giá»¯a tá»« thá»© 295 vÃ  305, viá»‡c gá»‘i Ä‘áº§u 50 tá»« sáº½ giá»¯ trá»n váº¹n ngá»¯ nghÄ©a cá»§a cÃ¢u á»Ÿ cáº£ hai Ä‘oáº¡n káº¿ tiáº¿p nhau, trÃ¡nh hiá»‡n tÆ°á»£ng Ä‘á»©t gÃ£y ngá»¯ cáº£nh khi ngÆ°á»i dÃ¹ng tÃ¬m kiáº¿m.
  - *Xá»­ lÃ½ Ä‘oáº¡n Ä‘uÃ´i (Tail Pruning):* Náº¿u Ä‘oáº¡n cuá»‘i cÃ¹ng cÃ³ Ã­t hÆ¡n 75 tá»« (`chunk_size // 4`), hÃ m sáº½ bá» qua hoáº·c gá»™p Ä‘á»ƒ trÃ¡nh táº¡o ra cÃ¡c chunk phÃ¢n máº£nh rÃ¡c.

---

### 3.2. Bá»™ nÃ©n lÆ°á»£ng tá»­ hÃ³a vÃ´ hÆ°á»›ng: `src/quantizer/sq8.py`

#### Má»¥c Ä‘Ã­ch vÃ  vai trÃ²
CÃ i Ä‘áº·t thuáº­t toÃ¡n nÃ©n SQ8 tá»« `float32` sang `int8`, Ä‘o lÆ°á»ng sai sá»‘ phá»¥c há»“i vÃ  xuáº¥t/nháº­p tham sá»‘ nÃ©n.

#### CÃ¡c hÃ m chÃ­nh trong `ScalarQuantizer8`
1. `fit(self, vectors: np.ndarray) -> "ScalarQuantizer8"`
   - Nháº­n máº£ng máº«u vector `float32` kÃ­ch thÆ°á»›c $(N, D)$.
   - TÃ­nh `min_vals = np.min(vectors, axis=0)` vÃ  `max_vals = np.max(vectors, axis=0)`.
   - TÃ­nh máº£ng tá»‰ lá»‡ `scales = (max_vals - min_vals) / 255.0`. Náº¿u hiá»‡u sá»‘ quÃ¡ nhá» ($< 10^{-8}$), gÃ¡n báº±ng $1.0$ Ä‘á»ƒ chá»‘ng lá»—i chia cho 0.
2. `quantize(self, vectors: np.ndarray) -> np.ndarray`
   - NÃ©n máº£ng $(N, D)$ sang kiá»ƒu `np.int8`.
   - Sá»­ dá»¥ng `np.clip` vÃ  `np.round` Ä‘á»ƒ chuyá»ƒn Ä‘á»•i tuyáº¿n tÃ­nh.
3. `dequantize(self, quantized_vectors: np.ndarray) -> np.ndarray`
   - KhÃ´i phá»¥c vector sang `np.float32`.
4. `compute_reconstruction_error(self, original_vectors: np.ndarray) -> Dict[str, float]`
   - Äo sai sá»‘ bÃ¬nh phÆ°Æ¡ng trung bÃ¬nh (MSE Loss) vÃ  Ä‘á»™ tÆ°Æ¡ng Ä‘á»“ng Cosine trung bÃ¬nh giá»¯a vector gá»‘c vÃ  vector sau khi nÃ©n-giáº£i nÃ©n.
   - *Káº¿t quáº£ thá»±c nghiá»‡m:* MSE Loss $< 0,0002$, Ä‘á»™ tÆ°Æ¡ng Ä‘á»“ng Cosine $> 0,9998$ (Ä‘á»™ chÃ­nh xÃ¡c báº£o toÃ n gáº§n nhÆ° tuyá»‡t Ä‘á»‘i).
5. `export_params()` vÃ  `load_params(params_dict)`
   - Chuyá»ƒn Ä‘á»•i cÃ¡c máº£ng NumPy `min_vals`, `max_vals`, `scales` thÃ nh danh sÃ¡ch chuáº©n Python Ä‘á»ƒ lÆ°u vÃ o `quantization_params.json` vÃ  tÃ¡i náº¡p láº¡i tá»©c thÃ¬ khi cáº§n.

---

### 3.3. Quáº£n lÃ½ lÆ°u trá»¯ Memmap Ä‘Ä©a: `src/quantizer/storage.py`

#### Má»¥c Ä‘Ã­ch vÃ  vai trÃ²
Cung cáº¥p cÆ¡ cháº¿ I/O tá»‘i Æ°u trÃªn Ä‘Ä©a SSD, cho phÃ©p á»©ng dá»¥ng Ä‘á»c/ghi hÃ ng chá»¥c triá»‡u vector mÃ  dung lÆ°á»£ng RAM sá»­ dá»¥ng chá»‰ tá»‘n vÃ i megabytes.

#### CÃ¡c ká»¹ thuáº­t láº­p trÃ¬nh há»‡ thá»‘ng Ä‘Æ°á»£c Ã¡p dá»¥ng
1. **Ãnh xáº¡ bá»™ nhá»› nhá»‹ phÃ¢n (`np.memmap`):**
   - Thay vÃ¬ náº¡p toÃ n bá»™ tá»‡p 6,32 GB vÃ o RAM, `np.memmap` liÃªn káº¿t trá»±c tiáº¿p Ä‘á»‹a chá»‰ bá»™ nhá»› áº£o cá»§a tiáº¿n trÃ¬nh vá»›i cÃ¡c khá»‘i trang (Page Blocks) trÃªn á»• cá»©ng SSD thÃ´ng qua nhÃ¢n há»‡ Ä‘iá»u hÃ nh (OS Virtual Memory Manager).
   - Chá»‰ nhá»¯ng trang dá»¯ liá»‡u nÃ o Ä‘Æ°á»£c CPU Ä‘á»c tá»›i má»›i Ä‘Æ°á»£c náº¡p vÃ o cache, giÃºp tiáº¿n trÃ¬nh khá»Ÿi Ä‘á»™ng ngay trong $0,001$ giÃ¢y dÃ¹ dá»¯ liá»‡u lá»›n hÃ ng chá»¥c gigabytes.
2. **CÆ¡ cháº¿ tiá»n cáº¥p phÃ¡t vÃ  co giÃ£n Ä‘á»™ng (`_resize_mmap`):**
   - HÃ m `initialize_storage` táº¡o tá»‡p tráº¯ng vÃ  gá»i `f.truncate(capacity * dim * 1)` Ä‘á»ƒ cáº¥p phÃ¡t trÆ°á»›c khÃ´ng gian liÃªn tá»¥c trÃªn báº£ng phÃ¢n bá»• tá»‡p NTFS, trÃ¡nh hiá»‡n tÆ°á»£ng phÃ¢n máº£nh Ä‘Ä©a.
   - Náº¿u sá»‘ lÆ°á»£ng vector vÆ°á»£t quÃ¡ sá»©c chá»©a ban Ä‘áº§u, `_resize_mmap` sáº½ tá»± Ä‘á»™ng nhÃ¢n Ä‘Ã´i kÃ­ch thÆ°á»›c Ä‘á»‡m (`capacity * 2`) vÃ  Ã¡nh xáº¡ láº¡i con trá».
3. **Chá»‘ng ngháº½n I/O (Disk Thrashing Mitigation):**
   - Náº¿u má»—i máº» 512 vector Ä‘á»u gá»i `mmap.flush()` vÃ  `meta_f.flush()`, á»• cá»©ng SSD sáº½ liÃªn tá»¥c bá»‹ khÃ³a Ä‘á»“ng bá»™ (Synchronous Write Blocking), kÃ©o tá»¥t tá»‘c Ä‘á»™ tá»« $2.500$ vecs/s xuá»‘ng cÃ²n $150$ vecs/s.
   - HÃ m `append_batch` nháº­n cá» `flush=False`. ToÃ n bá»™ dá»¯ liá»‡u Ä‘Æ°á»£c gom vÃ o bá»™ Ä‘á»‡m cá»§a há»‡ Ä‘iá»u hÃ nh vÃ  chá»‰ xáº£ triá»‡t Ä‘á»ƒ má»™t láº§n duy nháº¥t khi káº¿t thÃºc má»—i shard thÃ´ng qua hÃ m `flush_buffers()`.
4. **Cáº¯t tá»‰a tá»‡p chÃ­nh xÃ¡c (Exact File Truncation):**
   - Khi káº¿t thÃºc quÃ¡ trÃ¬nh lÆ°á»£ng tá»­ hÃ³a (`storage.close()`), hÃ m tá»± Ä‘á»™ng cáº¯t bá» pháº§n dung lÆ°á»£ng Ä‘á»‡m dÆ° thá»«a báº±ng lá»‡nh `f.truncate(self.current_count * self.dim * 1)`, Ä‘áº£m báº£o kÃ­ch thÆ°á»›c tá»‡p trÃªn Ä‘Ä©a khá»›p chÃ­nh xÃ¡c tá»«ng byte theo sá»‘ lÆ°á»£ng vector thá»±c táº¿.

---

### 3.4. MÃ´ hÃ¬nh nhÃºng ngÃ´n ngá»¯ tÄƒng tá»‘c GPU: `src/ann_data/embedder.py`

#### Má»¥c Ä‘Ã­ch vÃ  vai trÃ²
Chuyá»ƒn hÃ³a vÄƒn báº£n tiáº¿ng Viá»‡t thÃ nh dense vector 384 chiá»u báº±ng mÃ´ hÃ¬nh Transformer sÃ¢u `paraphrase-multilingual-MiniLM-L12-v2`.

#### Tá»‘i Æ°u hÃ³a trÃªn pháº§n cá»©ng NVIDIA GeForce RTX 4060
1. **Tá»± Ä‘á»™ng nháº­n diá»‡n pháº§n cá»©ng (Auto Device Selection):**
   ```python
   device = "cuda" if torch.cuda.is_available() else "cpu"
   self._model = SentenceTransformer(self.model_name, device=device)
   ```
   Táº­n dá»¥ng nhÃ¢n Tensor Core trÃªn card Ä‘á»“ há»a rá»i RTX 4060, giÃºp tÄƒng tá»‘c Ä‘á»™ tÃ­nh toÃ¡n ma tráº­n lÃªn gáº¥p **$15 - 20$ láº§n** so vá»›i cháº¡y trÃªn CPU.
2. **KÃ­ch thÆ°á»›c lÃ´ tÃ­nh toÃ¡n lá»›n (`batch_size=512`):**
   - Vá»›i bá»™ nhá»› VRAM 8 GB cá»§a card RTX 4060, kÃ­ch thÆ°á»›c lÃ´ 512 máº«u vÄƒn báº£n táº­n dá»¥ng tá»‘i Ä‘a bÄƒng thÃ´ng bá»™ nhá»› GPU mÃ  chá»‰ tiÃªu tá»‘n khoáº£ng 2,1 GB VRAM.
   - Tá»‘c Ä‘á»™ xá»­ lÃ½ thá»±c nghiá»‡m Ä‘áº¡t **$2.673$ vÄƒn báº£n/giÃ¢y** (so vá»›i 1.450 vecs/s á»Ÿ batch 256 vÃ  650 vecs/s á»Ÿ batch 64).
3. **CÆ¡ cháº¿ an toÃ n (Fallback Mock Embedder):**
   - Náº¿u mÃ´i trÆ°á»ng mÃ¡y chá»§ cháº¡y kiá»ƒm thá»­ thiáº¿u thÆ° viá»‡n PyTorch hoáº·c khÃ´ng cÃ³ káº¿t ná»‘i máº¡ng táº£i model, class tá»± Ä‘á»™ng kÃ­ch hoáº¡t `MockEmbedder` Ä‘á»ƒ toÃ n bá»™ bÃ i test logic I/O váº«n cháº¡y bÃ¬nh thÆ°á»ng mÃ  khÃ´ng bá»‹ crash.

---

### 3.5. Bá»™ Ä‘iá»u phá»‘i lÆ°á»£ng tá»­ hÃ³a: `src/quantizer/pipeline.py`

#### Má»¥c Ä‘Ã­ch vÃ  vai trÃ²
Káº¿t ná»‘i táº¥t cáº£ cÃ¡c module Ä‘Æ¡n láº» thÃ nh má»™t chu trÃ¬nh khÃ©p kÃ­n: Ä‘á»c shard thÃ´ $\to$ chia Ä‘oáº¡n $\to$ nhÃºng GPU $\to$ nÃ©n SQ8 $\to$ ghi Ä‘Ä©a SSD $\to$ lÆ°u checkpoint.

#### CÆ¡ cháº¿ tá»± phá»¥c há»“i lá»—i (Resumable Checkpointing)
```python
def process(self, limit: Optional[int] = None, resume: bool = True) -> Dict[str, Any]:
```
- Khi báº¯t Ä‘áº§u, pipeline kiá»ƒm tra tá»‡p `data/quantized/checkpoint.json`:
  ```json
  {
    "completed_shards": ["shard_00000.jsonl", "shard_00001.jsonl", ...],
    "total_vectors": 15096676,
    "last_shard": "shard_00174.jsonl",
    "last_updated": "2026-09-05T17:46:24Z"
  }
  ```
- Náº¿u `resume=True`, pipeline sáº½ náº¡p láº¡i tham sá»‘ `quantization_params.json` Ä‘Ã£ fit tá»« trÆ°á»›c (khÃ´ng cáº§n trÃ­ch máº«u láº¡i) vÃ  lá»c danh sÃ¡ch `shards_to_process` Ä‘á»ƒ **bá» qua toÃ n bá»™ cÃ¡c shard Ä‘Ã£ hoÃ n thÃ nh**, má»Ÿ file á»Ÿ cháº¿ Ä‘á»™ ná»‘i tiáº¿p `mode="a"`.
- Nhá» cÆ¡ cháº¿ nÃ y, má»™t tÃ¡c vá»¥ xá»­ lÃ½ 10 triá»‡u báº£n ghi kÃ©o dÃ i vÃ i giá» cÃ³ thá»ƒ dá»«ng báº¥t ká»³ lÃºc nÃ o vÃ  cháº¡y tiáº¿p mÃ  khÃ´ng máº¥t mÃ¡t dá»¯ liá»‡u.

---

### 3.6. TÃ¬m kiáº¿m ngá»¯ nghÄ©a thá»i gian thá»±c: `src/ann_data/search/semantic_engine.py`

#### Má»¥c Ä‘Ã­ch vÃ  vai trÃ²
Cho phÃ©p truy váº¥n ngá»¯ nghÄ©a tá»± nhiÃªn trÃªn táº­p 16,5 triá»‡u vector int8 mÃ  khÃ´ng gÃ¢y trÃ n bá»™ nhá»› RAM cá»§a mÃ¡y tÃ­nh.

#### Ká»¹ thuáº­t giáº£i quyáº¿t bÃ i toÃ¡n quy mÃ´ lá»›n
1. **Truy xuáº¥t siÃªu dá»¯ liá»‡u theo luá»“ng (On-Demand Single-Pass Streaming):**
   - Tá»‡p `metadata.jsonl` cÃ³ dung lÆ°á»£ng lÃªn tá»›i 22,3 GB. Náº¿u Ä‘á»c toÃ n bá»™ vÃ o má»™t `list` trong Python, RAM sáº½ bá»‹ trÃ n ngay láº­p tá»©c.
   - `SemanticSearchEngine` chá»‰ táº£i siÃªu dá»¯ liá»‡u khi tá»‡p $< 50$ MB. Vá»›i tá»‡p lá»›n, sau khi tÃ¬m ra `top_k` chá»‰ sá»‘ vector (vÃ­ dá»¥ 5 chá»‰ sá»‘), hÃ m `get_metadata_for_indices` chá»‰ quÃ©t tuyáº¿n tÃ­nh 1 lÆ°á»£t duy nháº¥t qua tá»‡p Ä‘á»ƒ trÃ­ch xuáº¥t Ä‘Ãºng 5 dÃ²ng tÆ°Æ¡ng á»©ng vÃ  dá»«ng láº¡i, tiÃªu tá»‘n chÆ°a tá»›i 1 MB RAM.
2. **TÃ¬m kiáº¿m phÃ¢n khá»‘i (Chunked Scanning on Memmap):**
   - Thay vÃ¬ nhÃ¢n toÃ n bá»™ ma tráº­n 16,5 triá»‡u vector cÃ¹ng lÃºc, thuáº­t toÃ¡n chia máº£ng memmap thÃ nh tá»«ng khá»‘i 500.000 vector:
     ```python
     for start in range(0, self.num_records, chunk_size):
         chunk = self.raw_mmap[start:end].astype(np.float32)
         scores = np.dot(chunk, q_scaled)
         part = np.argpartition(scores, -k)[-k:]
     ```
   - Sá»­ dá»¥ng `np.argpartition` thay vÃ¬ `np.sort` Ä‘áº§y Ä‘á»§ giÃºp giáº£m Ä‘á»™ phá»©c táº¡p thuáº­t toÃ¡n tá»« $O(N \log N)$ xuá»‘ng $O(N)$, hoÃ n thÃ nh quÃ©t toÃ n bá»™ 16,5 triá»‡u vector trong thá»i gian dÆ°á»›i 1,5 giÃ¢y.

---

## 4. Báº£ng So sÃ¡nh Chá»‰ sá»‘ Hiá»‡u nÄƒng Thá»±c táº¿

| TiÃªu chÃ­ Ä‘o kiá»ƒm | Dáº¡ng gá»‘c (Float32) | LÆ°á»£ng tá»­ hÃ³a SQ8 (Int8) | Má»©c cáº£i thiá»‡n |
| :--- | :--- | :--- | :--- |
| **Dung lÆ°á»£ng 1 vector (384 chiá»u)** | 1.536 bytes | 384 bytes | **Giáº£m 75,0%** |
| **Dung lÆ°á»£ng 16.459.486 vector** | 24.110,58 MB (~24,11 GB) | 6.027,64 MB (~6,03 GB) | **Tiáº¿t kiá»‡m 18,08 GB Ä‘Ä©a** |
| **YÃªu cáº§u RAM Ä‘á»ƒ táº£i chá»‰ má»¥c** | $> 25$ GB RAM | $\approx 20$ MB (nhá» Memmap) | **KhÃ´ng phá»¥ thuá»™c RAM váº­t lÃ½** |
| **Tá»‘c Ä‘á»™ mÃ£ hÃ³a trÃªn RTX 4060** | ~1.400 vecs/s (batch 256) | **2.673 vecs/s (batch 512)** | **TÄƒng tá»‘c 91%** |
| **Thá»i gian quÃ©t tÃ¬m kiáº¿m Top-5** | ~4,8 giÃ¢y | **~1,45 giÃ¢y** | **Nhanh hÆ¡n 3,3 láº§n** |
| **Äá»™ tÆ°Æ¡ng Ä‘á»“ng ngá»¯ nghÄ©a (Cosine)** | 1,0000 | 0,9998 | **Äá»™ suy hao $< 0,02\%$** |

---

## 5. Quy Æ°á»›c Äáº·t tÃªn vÃ  HÆ°á»›ng dáº«n cho NhÃ¢n viÃªn Má»›i

1. **Quy táº¯c Ä‘áº·t tÃªn file vÃ  module:**
   - Táº¥t cáº£ tÃªn file mÃ£ nguá»“n dÃ¹ng chá»¯ thÆ°á»ng phÃ¢n cÃ¡ch báº±ng dáº¥u gáº¡ch dÆ°á»›i (`snake_case`): `chunker.py`, `storage.py`, `run_quantization.py`.
   - CÃ¡c class dÃ¹ng quy táº¯c viáº¿t hoa chá»¯ cÃ¡i Ä‘áº§u (`PascalCase`): `ScalarQuantizer8`, `TextChunker`, `QuantizedStorage`.
2. **Quy táº¯c tiá»n tá»‘ vÃ  háº­u tá»‘ biáº¿n:**
   - Biáº¿n káº¿t thÃºc báº±ng `_mmap`: Äá»‘i tÆ°á»£ng máº£ng Ã¡nh xáº¡ bá»™ nhá»› (`raw_mmap`).
   - Biáº¿n káº¿t thÃºc báº±ng `_int8` hoáº·c `_float`: Thá»ƒ hiá»‡n rÃµ kiá»ƒu dá»¯ liá»‡u sá»‘ há»c Ä‘á»ƒ trÃ¡nh nháº§m láº«n khi truyá»n vÃ o hÃ m nhÃ¢n ma tráº­n (`int8_vecs`, `float_vecs`).
   - Tiá»n tá»‘ `is_`: Biáº¿n kiá»ƒu boolean kiá»ƒm tra tráº¡ng thÃ¡i (`is_fitted`, `is_int8`).
3. **Quy táº¯c báº¥t biáº¿n khi má»Ÿ rá»™ng:**
   - KhÃ´ng Ä‘Æ°á»£c phÃ©p sá»­a mÃ£ nguá»“n cá»§a ká»‹ch báº£n crawl hay quantize cÅ© khi cÃ³ yÃªu cáº§u nguá»“n dá»¯ liá»‡u má»›i; luÃ´n táº¡o file Ä‘á»™c láº­p káº¿ thá»«a thÆ° viá»‡n lÃµi Ä‘á»ƒ phá»¥c vá»¥ viá»‡c Ä‘á»‘i soÃ¡t vÃ  bÃ¡o cÃ¡o Ä‘á»™c láº­p.

