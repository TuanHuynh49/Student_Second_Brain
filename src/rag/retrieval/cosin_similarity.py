import os 
from rich import print 
from dotenv import load_dotenv
import numpy as np 
import numpy as np


def cosine_similarity(vec1, vec2) -> float:
    """Tính độ tương đồng cosine giữa 2 vector hoặc ma trận."""
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    
    # Xử lý nếu là vector/ma trận
    if v1.ndim > 1 or v2.ndim > 1:
        dot_product = np.dot(v1, v2.T)
        norm_v1 = np.linalg.norm(v1, axis=-1, keepdims=True)
        norm_v2 = np.linalg.norm(v2, axis=-1, keepdims=True)
        return dot_product / (norm_v1 * norm_v2.T + 1e-10)
    
    # Trường hợp 2 vector 1D thông thường
    norm_1 = np.linalg.norm(v1)
    norm_2 = np.linalg.norm(v2)
    if norm_1 == 0 or norm_2 == 0:
        return 0.0
    return float(np.dot(v1, v2) / (norm_1 * norm_2))