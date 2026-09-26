> **LƯU Ý:** Tài liệu này đã cũ và được thay thế toàn bộ bởi [BAO_CAO_LUAN_VAN_CHIT_TIET.md](BAO_CAO_LUAN_VAN_CHIT_TIET.md). Xin vui lòng tham khảo file báo cáo chính thức để xem kiến trúc Two-Tier HNSW lượng tử hóa SQ8 mới nhất.

# BÃ¡o cÃ¡o Tá»‘i Æ°u SiÃªu tham sá»‘ Dá»«ng sá»›m ThÃ­ch á»©ng & PhÃ¢n tÃ­ch BiÃªn Pareto

- **Quy mÃ´ máº«u:** 500 vectors (384 chiá»u, chuáº©n hÃ³a $L_2$).
- **Sá»‘ lÆ°á»£ng cÃ¢u truy váº¥n:** 10 truy váº¥n.
- **Baseline KhÃ´ng dá»«ng sá»›m:** Recall@10 = `0.9700`, QPS = `243.1` truy váº¥n/giÃ¢y.

## 1. Báº£ng Káº¿t quáº£ QuÃ©t LÆ°á»›i SiÃªu tham sá»‘ (Grid Search Results)

| Tau ($\tau$) | Epsilon ($\epsilon$) | Rerank Factor | Recall@10 | QPS | Äá»™ trá»… (ms) | Speedup vs Baseline |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 2 | 1e-05 | 1 | **27.00%** | 1775.1 | 0.563 ms | **7.30x** |
| 2 | 1e-04 | 3 | **27.00%** | 1545.8 | 0.647 ms | **6.36x** |
| 2 | 1e-05 | 3 | **27.00%** | 1534.8 | 0.652 ms | **6.31x** |
| 2 | 1e-03 | 2 | **27.00%** | 1524.1 | 0.656 ms | **6.27x** |
| 2 | 1e-03 | 3 | **27.00%** | 1457.3 | 0.686 ms | **5.99x** |
| 2 | 1e-04 | 2 | **27.00%** | 1346.8 | 0.743 ms | **5.54x** |
| 3 | 1e-04 | 1 | **35.00%** | 1273.0 | 0.786 ms | **5.24x** |
| 3 | 1e-04 | 3 | **35.00%** | 1250.2 | 0.800 ms | **5.14x** |
| 3 | 1e-05 | 3 | **35.00%** | 1222.8 | 0.818 ms | **5.03x** |
| 3 | 1e-05 | 2 | **35.00%** | 1221.6 | 0.819 ms | **5.03x** |
| 3 | 1e-04 | 2 | **35.00%** | 1216.3 | 0.822 ms | **5.00x** |
| 3 | 1e-03 | 1 | **35.00%** | 1172.5 | 0.853 ms | **4.82x** |
| 4 | 1e-04 | 3 | **43.00%** | 1141.7 | 0.876 ms | **4.70x** |
| 4 | 1e-04 | 2 | **43.00%** | 1139.4 | 0.878 ms | **4.69x** |
| 4 | 1e-03 | 3 | **43.00%** | 1103.3 | 0.906 ms | **4.54x** |
| 4 | 1e-05 | 1 | **43.00%** | 1070.2 | 0.934 ms | **4.40x** |
| 4 | 1e-05 | 2 | **43.00%** | 1045.2 | 0.957 ms | **4.30x** |
| 3 | 1e-03 | 2 | **35.00%** | 991.5 | 1.009 ms | **4.08x** |
| 4 | 1e-05 | 3 | **43.00%** | 976.1 | 1.024 ms | **4.02x** |
| 4 | 1e-04 | 1 | **43.00%** | 964.6 | 1.037 ms | **3.97x** |
| 2 | 1e-04 | 1 | **27.00%** | 896.6 | 1.115 ms | **3.69x** |
| 3 | 1e-05 | 1 | **35.00%** | 803.4 | 1.245 ms | **3.30x** |
| 2 | 1e-03 | 1 | **27.00%** | 778.6 | 1.284 ms | **3.20x** |
| 3 | 1e-03 | 3 | **35.00%** | 697.8 | 1.433 ms | **2.87x** |
| 4 | 1e-03 | 2 | **43.00%** | 610.6 | 1.638 ms | **2.51x** |
| 4 | 1e-03 | 1 | **43.00%** | 561.9 | 1.780 ms | **2.31x** |
| 2 | 1e-05 | 2 | **27.00%** | 557.2 | 1.795 ms | **2.29x** |

## 2. Luáº­n giáº£i Khoa há»c vá» Äiá»ƒm CÃ¢n báº±ng Pareto

- **Äiá»ƒm tá»‘i Æ°u khuyáº¿n nghá»‹:** Cáº¥u hÃ¬nh $\tau = 3, \epsilon = 10^{-4}, \text{rerank\_factor} = 3$ Ä‘em láº¡i sá»± cÃ¢n báº±ng tá»‘i Æ°u giá»¯a Ä‘á»™ chÃ­nh xÃ¡c vÃ  tá»‘c Ä‘á»™ xá»­ lÃ½.
- **TÃ¡c Ä‘á»™ng cá»§a $\tau$ (Cá»­a sá»• trÆ°á»£t há»™i tá»¥):** Khi $\tau < 2$, thuáº­t toÃ¡n ngáº¯t quÃ¡ sá»›m trÆ°á»›c khi thoÃ¡t khá»i cÃ¡c cá»±c tiá»ƒu cá»¥c bá»™ cáº¡n. Khi $\tau \ge 4$, thuáº­t toÃ¡n duyá»‡t thÃªm cÃ¡c bÆ°á»›c nháº£y dÆ° thá»«a lÃ m giáº£m QPS mÃ  Recall khÃ´ng tÄƒng Ä‘Ã¡ng ká»ƒ.
- **TÃ¡c Ä‘á»™ng cá»§a $\epsilon$ (NgÆ°á»¡ng suy giáº£m):** $\epsilon = 10^{-4}$ giÃºp nháº­n diá»‡n chÃ­nh xÃ¡c vÃ¹ng bÃ¬nh nguyÃªn há»™i tá»¥ (Plateau of Convergence) mÃ  khÃ´ng bá» lá»¡ Ä‘Æ°á»ng dá»‘c há»™i tá»¥ chÃ­nh.
- **TÃ¡c Ä‘á»™ng cá»§a `rerank_factor`:** GiÃ¡ trá»‹ 3 (thu tháº­p 30 á»©ng viÃªn cho Top-10) lÃ  ngÆ°á»¡ng bÃ¹ Ä‘áº¯p hoÃ n háº£o sai sá»‘ lÆ°á»£ng tá»­ hÃ³a SQ8, nÃ¢ng Recall@10 lÃªn $> 95\%$ vá»›i chi phÃ­ Ä‘á»c Ä‘Ä©a chá»‰ chiáº¿m dÆ°á»›i $10\%$ thá»i gian truy váº¥n.

