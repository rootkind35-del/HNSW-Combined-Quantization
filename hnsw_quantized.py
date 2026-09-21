import numpy as np

def quantize_adc(vectors: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Lượng tử hóa vector và trích xuất hệ số mỏ neo (Scale, Offset) phục vụ ADC.
    """
    # 1. Tìm cực tiểu (Offset) và cực đại
    min_val = np.min(vectors, axis=1, keepdims=True)
    max_val = np.max(vectors, axis=1, keepdims=True)
    
    range_val = max_val - min_val
    range_val[range_val == 0] = 1e-8
    
    # 2. Ép kiểu hệ số mỏ neo xuống float16 (Chỉ 2 bytes thay vì 4 bytes)
    # Công thức Scale = Range / 255
    scale = (range_val / 255.0).astype(np.float16)
    offset = min_val.astype(np.float16)
    
    # 3. Nén dữ liệu lõi xuống uint8
    normalized = (vectors - min_val) / range_val
    quantized_vectors = np.round(normalized * 255).astype(np.uint8)
    
    return quantized_vectors, scale, offset

def distance_adc(query_float32: np.ndarray, q_vector_uint8: np.ndarray, scale: np.float16, offset: np.float16) -> float:
    """
    Tính khoảng cách L2 (Euclid) bất đối xứng (Asymmetric Distance Computation).
    Bỏ qua khâu giải nén toàn cục, tính trực tiếp Query trên dữ liệu nén.
    """
    # Khôi phục nội suy ngay trong lúc tính khoảng cách: V_x = V_uint8 * Scale + Offset
    approx_vector = (q_vector_uint8.astype(np.float32) * scale) + offset
    
    # Tính Euclid Distance (L2)
    distance = np.linalg.norm(query_float32 - approx_vector)
    return float(distance)

def exact_distance_l2(query: np.ndarray, vector: np.ndarray) -> float:
    """Khoảng cách Euclid gốc để đối chiếu sai số."""
    return float(np.linalg.norm(query - vector))

if __name__ == "__main__":
    # Giả lập 1 vector Query (Người dùng nhập) và 1 Vector trong Database (Tier 1)
    np.random.seed(99)
    query = np.random.randn(384).astype(np.float32)
    db_vector = np.random.randn(384).astype(np.float32)
    
    # Tier 1 thực hiện nén dữ liệu khi nạp vào (Add Node)
    q_vec, scale, offset = quantize_adc(db_vector.reshape(1, -1))
    
    # Trích xuất dạng 1 chiều để tính toán
    q_vec_1d = q_vec[0]
    scale_1d = scale[0][0]
    offset_1d = offset[0][0]
    
    print("--- KIỂM THỬ THUẬT TOÁN ADC ---")
    print(f"Lưu trữ tại Tier 1: Vector {q_vec_1d.dtype} | Scale: {scale_1d.dtype} | Offset: {offset_1d.dtype}")
    
    # Tính toán đối chiếu
    dist_exact = exact_distance_l2(query, db_vector)
    dist_adc = distance_adc(query, q_vec_1d, scale_1d, offset_1d)
    
    print("\nSo sánh Khoảng cách L2 (Euclid):")
    print(f"- Khoảng cách thật (Float32): {dist_exact:.6f}")
    print(f"- Khoảng cách ADC  (Uint8)  : {dist_adc:.6f}")
    print(f"=> Độ lệch nội suy (Sai số) : {abs(dist_exact - dist_adc):.6f}")
