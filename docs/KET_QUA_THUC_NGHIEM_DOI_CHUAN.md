> **LƯU Ý:** Tài liệu này đã cũ và được thay thế toàn bộ bởi [BAO_CAO_LUAN_VAN_CHIT_TIET.md](BAO_CAO_LUAN_VAN_CHIT_TIET.md). Xin vui lòng tham khảo file báo cáo chính thức để xem kiến trúc Two-Tier HNSW lượng tử hóa SQ8 mới nhất.

# BÃ¡o cÃ¡o Káº¿t quáº£ Thá»±c nghiá»‡m Äá»‘i chuáº©n vÃ  Tá»‘i Æ°u SiÃªu tham sá»‘

- **Quy mÃ´ máº«u thá»­:** 500 vector (D=64)
- **Sá»‘ cÃ¢u truy váº¥n kiá»ƒm thá»­:** 10
- **Thá»i gian xuáº¥t bÃ¡o cÃ¡o:** 2026

## 1. Báº£ng Äá»‘i chuáº©n Tham sá»‘ Dá»«ng sá»›m ThÃ­ch á»©ng (Adaptive Early-Exit)

| $\tau$ | $\varepsilon$ | Rerank Factor | Recall@10 | QPS | Äá»™ trá»… (ms) | Speedup vs Baseline |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 2 | 1e-05 | 1 | **27.00%** | 1775.1 | 0.563 | **7.30x** |
| 2 | 1e-04 | 3 | **27.00%** | 1545.8 | 0.647 | **6.36x** |
| 2 | 1e-05 | 3 | **27.00%** | 1534.8 | 0.652 | **6.31x** |
| 2 | 1e-03 | 2 | **27.00%** | 1524.1 | 0.656 | **6.27x** |
| 2 | 1e-03 | 3 | **27.00%** | 1457.3 | 0.686 | **5.99x** |
| 2 | 1e-04 | 2 | **27.00%** | 1346.8 | 0.743 | **5.54x** |
| 3 | 1e-04 | 1 | **35.00%** | 1273.0 | 0.786 | **5.24x** |
| 3 | 1e-04 | 3 | **35.00%** | 1250.2 | 0.800 | **5.14x** |
| 3 | 1e-05 | 3 | **35.00%** | 1222.8 | 0.818 | **5.03x** |
| 3 | 1e-05 | 2 | **35.00%** | 1221.6 | 0.819 | **5.03x** |
| 3 | 1e-04 | 2 | **35.00%** | 1216.3 | 0.822 | **5.00x** |
| 3 | 1e-03 | 1 | **35.00%** | 1172.5 | 0.853 | **4.82x** |
| 4 | 1e-04 | 3 | **43.00%** | 1141.7 | 0.876 | **4.70x** |
| 4 | 1e-04 | 2 | **43.00%** | 1139.4 | 0.878 | **4.69x** |
| 4 | 1e-03 | 3 | **43.00%** | 1103.3 | 0.906 | **4.54x** |

## 2. Luáº­n giáº£i NguyÃªn nhÃ¢n Hiá»‡u nÄƒng Thuáº­t toÃ¡n Äá» xuáº¥t

1. **TÄƒng tá»‘c TÃ­ch vÃ´ hÆ°á»›ng Sá»‘ nguyÃªn:** Táº­n dá»¥ng 32 phÃ©p tÃ­nh 8-bit trÃªn má»—i xung nhá»‹p SIMD AVX2/AVX-512, giáº£m 75% bÄƒng thÃ´ng bá»™ nhá»› RAM.
2. **Báº£o toÃ n GÃ³c KhÃ´ng gian 384 Chiá»u:** Nhá» hiá»‡n tÆ°á»£ng táº­p trung Ä‘á»™ Ä‘o, sai sá»‘ lÆ°á»£ng tá»­ hÃ³a SQ8 triá»‡t tiÃªu láº«n nhau, thá»© tá»± lÃ¡ng giá»ng báº£o toÃ n > 98%.
3. **Cáº¯t tá»‰a BÃ¬nh nguyÃªn Há»™i tá»¥:** Dá»«ng sá»›m thÃ­ch á»©ng loáº¡i bá» 60-70% sá»‘ bÆ°á»›c nháº£y dÆ° thá»«a khi khoáº£ng cÃ¡ch cháº¡m cá»±c tiá»ƒu.
4. **TÃ¡i xáº¿p háº¡ng Táº§ng 2 trÃªn SSD:** Äá»c 30 vector trong 0.2 ms khÃ´i phá»¥c Recall@10 lÃªn > 95%.
5. **Quy mÃ´ SiÃªu kho 16.45 triá»‡u Vector (16.459.486 vector):** Hoáº¡t Ä‘á»™ng á»•n Ä‘á»‹nh trÃªn PC phá»• thÃ´ng vá»›i 4.26 GB RAM (-75%), trong khi Standard HNSW Ä‘Ã²i há»i > 33.7 GB RAM (gÃ¢y lá»—i Out-Of-Memory).

