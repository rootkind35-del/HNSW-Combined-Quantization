import re
import os
import numpy as np
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

def clean_text(raw_text: str) -> str:
    """
    Làm sạch và chuẩn hóa văn bản thô để đưa vào mô hình Embedding.
    """
    if not isinstance(raw_text, str):
        return ""
        
    text = re.sub(r'<[^>]+>', ' ', raw_text)
    text = re.sub(r'http\S+|www\.\S+', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def chunk_text(text: str, max_words: int = 200, overlap: int = 20) -> list[str]:
    """
    Cắt văn bản thành các đoạn nhỏ để đáp ứng giới hạn token của mô hình.
    Có đoạn gối đầu (overlap) để không làm đứt đoạn ngữ nghĩa.
    """
    words = text.split()
    
    # Nếu văn bản ngắn hơn giới hạn, trả về nguyên bản
    if len(words) <= max_words:
        return [text]
        
    chunks = []
    step = max_words - overlap
    
    for i in range(0, len(words), step):
        chunk_words = words[i:i + max_words]
        chunks.append(" ".join(chunk_words))
        
    return chunks

embedding_model = None

def get_model():
    """
    Sử dụng mẫu thiết kế Singleton để load mô hình một lần duy nhất, 
    tránh tốn RAM và thời gian tải đi tải lại trên Big Data.
    """
    global embedding_model
    if embedding_model is None:
        if SentenceTransformer is None:
            raise ImportError("Lỗi: Bạn chưa cài đặt thư viện. Hãy chạy: pip install sentence-transformers")
        print("Đang khởi tạo mô hình MiniLM-L12-v2 lên bộ nhớ...")
        # Load mô hình tạo vector 384 chiều (hỗ trợ Tiếng Việt)
        embedding_model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
    return embedding_model

def generate_embeddings(texts: list[str], batch_size: int = 32) -> np.ndarray:
    """
    Biến đổi danh sách văn bản thành ma trận vector toán học.
    Đầu vào: list gồm N đoạn văn (chunks).
    Đầu ra: Ma trận numpy kích thước (N, 384) kiểu float32.
    """
    if not texts:
        return np.array([], dtype=np.float32)
        
    model = get_model()
    # model.encode tự động chạy xử lý song song theo batch
    embeddings = model.encode(texts, batch_size=batch_size, show_progress_bar=False, convert_to_numpy=True)
    return embeddings.astype(np.float32)

def append_vectors_to_disk(filepath: str, vectors: np.ndarray):
    """
    Ghi trực tiếp ma trận vector vào cuối file nhị phân trên SSD.
    Hỗ trợ xử lý dữ liệu dạng luồng (streaming/crawling).
    """
    if vectors.size == 0:
        return
    # Ghi nhị phân cực nhanh
    with open(filepath, 'ab') as f:
        vectors.tofile(f)

if __name__ == "__main__":
    test_string = """
    <p>Xin chào mọi người! <br> 
    Đây là bài kiểm tra tiền xử lý cho bài toán Big Data. 
    Xem thêm chi tiết tại https://example.com/tin-tuc/bai-viet-123 </p>
    
    Hy vọng   nó hoạt động  tốt.
    """
    
    print("--- DỮ LIỆU ĐÃ LÀM SẠCH ---")
    cleaned = clean_text(test_string)
    print(repr(cleaned))

    print("\n--- TEST CHUNKING ---")
    long_text = " ".join([f"từ_vựng_{i}" for i in range(1, 51)])
    print("Văn bản gốc (50 từ):", long_text[:50] + "...")
    
    chunks = chunk_text(long_text, max_words=20, overlap=5)
    for idx, c in enumerate(chunks):
        print(f"Đoạn {idx + 1} ({len(c.split())} từ): {c}")
        
    print("\n--- TEST EMBEDDING ---")
    try:
        # Lấy 2 đoạn cắt ở trên để sinh vector
        vectors = generate_embeddings(chunks[:2])
        print(f"Kích thước ma trận sinh ra: {vectors.shape} (N_đoạn, Số_chiều)")
        print(f"Kiểu dữ liệu: {vectors.dtype}")
        print(f"Giá trị 5 chiều đầu tiên của đoạn 1:\n{vectors[0][:5]}")
    except ImportError as e:
        print(e)
        vectors = None
        
    if vectors is not None:
        print("\n--- TEST LƯU TRỮ (TIER 2) ---")
        db_file = "vector_db.bin"
        if os.path.exists(db_file):
            os.remove(db_file) # Dọn dẹp file cũ để test
            
        append_vectors_to_disk(db_file, vectors)
        print(f"Đã ghi ma trận nhị phân trực tiếp xuống ổ cứng: {db_file}")

