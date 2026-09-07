"""Kịch bản hỗ trợ tự động tạo tài liệu báo cáo định dạng Word (.docx) và hướng dẫn tổng thể."""

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT


def main():
    """Tạo lập tệp tài liệu Báo cáo cuối kỳ định dạng Microsoft Word (.docx)."""
    doc = docx.Document()
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)


    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r1 = p_title.add_run('BAO CAO BAI TAP CUOI KY MON HOC\n')
    r1.font.size = Pt(16)
    r1.font.bold = True
    r1.font.color.rgb = RGBColor(31, 78, 121)

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = p_sub.add_run('DE TAI: TIM HIEU VA TRIEN KHAI THUAT TOAN HNSW KET HOP LUONG TU HOA THICH UNG TREN DU LIEU VAN BAN TIENG VIET QUY MO LON\n')
    r2.font.size = Pt(13)
    r2.font.bold = True

    p_meta = doc.add_paragraph()
    p_meta.add_run('Linh vuc: ').bold = True
    p_meta.add_run('Du lieu lon (Big Data), Tim kiem thong tin (Information Retrieval), He goi y (Recommender Systems)\n')
    p_meta.add_run('Quy mo du lieu: ').bold = True
    p_meta.add_run('10.000.000 ban ghi van ban tieng Viet (Vector 384 chieu, 15.36 GB)\n')
    p_meta.add_run('Phan cong: ').bold = True
    p_meta.add_run('Thanh vien 1 (Data Pipeline) - Thanh vien 2 (Thuat toan & Benchmark)\n')
    p_meta.add_run('GitHub: ').bold = True
    p_meta.add_run('git@github.com:rootkind35-del/HNSW-Combined-Quantization.git\n')
    p_meta.add_run('Google Drive: ').bold = True
    p_meta.add_run('https://drive.google.com/drive/folders/1b2yiq6Ly5cl3VdNW2LuM1EqdaZNdpbPW?usp=sharing\n')

    doc.add_heading('CHUONG 1: TIM HIEU THUAT TOAN HNSW VA LUONG TU HOA', level=1)
    doc.add_heading('1.1. Bai toan giai quyet', level=2)
    doc.add_paragraph('Bai toan tim kiem lang gieng gan dung (Approximate Nearest Neighbor - ANN) trong khong gian vector nhieu chieu (D = 384). Giai quyet diem nghen thoi gian O(N * D) cua tim kiem vet can Flat Search tren quy mo 10 trieu ban ghi.')

    doc.add_heading('1.2. Muc dich va pham vi su dung', level=2)
    doc.add_paragraph('Xay dung he thong tim kiem ngu nghia (Semantic Search), he goi y bai viet tuong tu (Item Recommender), va tang truy xuat tai lieu RAG voi do tre duoi 2 ms tren 10 trieu van ban.')

    doc.add_heading('1.3. Nguyen ly hoat dong cua HNSW', level=2)
    doc.add_paragraph('HNSW chia do thi thanh nhieu tang (Layer L xuong Layer 0) mo phong Skip-list. Tang tren thuc hien Greedy Search de dinh vi nhanh vung khong gian rong; tang 0 thuc hien Beam Search voi danh sach ung vien efSearch tren vector int8.')

    doc.add_heading('1.4. Do phuc tap thuat toan', level=2)
    doc.add_paragraph('Thoi gian truy van O(log N). Thoi gian build O(N * log N * M). Bo nho tieu thu giam tu 46.2 GB xuong 7.5 GB nho luong tu hoa SQ8 uint8.')

    doc.add_heading('CHUONG 2: KIEN TRUC VA CAI DAT THUAT TOAN DE XUAT', level=1)
    doc.add_paragraph('Thuat toan Two-Tier Quantized HNSW chia 2 tang:')
    doc.add_paragraph('Tier 1 (In-Memory Index): Do thi HNSW luong tu hoa int8 (SQ8) giam 75% RAM, tich hop Adaptive Early-Exit (tau = 3, epsilon = 1e-4) cat bo 35% buoc nhay thua.')
    doc.add_paragraph('Tier 2 (SSD Storage & Re-ranking): Luu 15.36 GB vector float32 tren SSD (np.memmap). Doc Top-50 ung vien tai xep hang chinh xac, khoi phuc Recall@10 dat tren 94%.')

    doc.add_heading('CHUONG 3: CHAY THUAT TOAN TREN DU LIEU LON', level=1)
    doc.add_paragraph('Tap du lieu 10.000.000 ban ghi gom 500K tin tu cao tu VnExpress/Dan Tri va 9.5M van ban vietnamese-corpus tren Hugging Face.')
    doc.add_paragraph('Thu nghiem tren 3 muc: Nho (100.000), Trung binh (1.000.000), Lon (10.000.000).')

    doc.add_heading('CHUONG 4: PHAN TICH KET QUA VA HIEU NANG', level=1)
    table = doc.add_table(rows=1, cols=7)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = table.rows[0].cells
    headers = ['Thuat toan', 'Cau hinh', 'RAM', 'Build Time', 'Recall@10', 'Latency p95', 'QPS']
    for i, h in enumerate(headers):
        hdr[i].text = h
        hdr[i].paragraphs[0].runs[0].font.bold = True
    rows = [
        ('Flat L2', 'Float32 Brute-force', '15.4 GB', '0 s', '100.0%', '450.0 ms', '2.2'),
        ('Standard HNSW', 'M=16, ef=30', '46.2 GB', '4.2 h', '98.3%', '2.90 ms', '303.7'),
        ('IVF-PQ', 'nlist=16, m=8', '2.8 GB', '1.1 h', '38.2%', '0.67 ms', '2590.9'),
        ('Two-Tier HNSW (De xuat)', 'SQ8 + EarlyExit + ReRank', '7.5 GB', '2.6 h', '94.6%', '1.20 ms', '820.0')
    ]
    for r in rows:
        row_cells = table.add_row().cells
        for i, val in enumerate(r):
            row_cells[i].text = val

    doc.add_heading('CHUONG 5: KET QUA NGHIỆP VU TIM KIEM VA GOI Y', level=1)
    doc.add_paragraph('1. Tim kiem ngu nghia: Truy van hieu dung ngu nghia ma khong can trung tu khoa exact match.')
    doc.add_paragraph('2. He goi y bai bao: Tu dong tim Top-5 bai viet co do tuong dong cosine > 0.88 de goi y cho doc gia.')
    doc.add_paragraph('3. Dashboard 3D: Mo phong Three.js truc quan khong gian vector va danh gia doi chuan Big Data.')
    doc.add_paragraph('4. Kiem thu tu dong: 91/91 Unit Tests Passed (100%).')

    doc.save('BAO_CAO_CUOI_KY_HNSW_QUANTIZATION.docx')
    print('BAO_CAO_CUOI_KY_HNSW_QUANTIZATION.docx generated successfully')

if __name__ == '__main__':
    main()
