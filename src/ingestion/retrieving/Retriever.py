from src.ingestion.embedding.jina_embeddings import jina_embeddings
import os 
from rich import print 
from dotenv import load_dotenv
import numpy as np 
from src.models.VectorStore import VectorStore
from src.models.DocumentChunk import RetrievedChunk
from collections import defaultdict
from src.models.DocumentChunk import RetrievedChunk
from src.ingestion.chunking.Chunking_helper import loaddoc

def retrieve(query: str, store: VectorStore, oversample: int = 4, top_k: int = 3) -> list[RetrievedChunk]:
    hits = store.search(query, top_k=top_k * oversample)
    
    parent_scores = defaultdict(list)
    parent_matched_children = defaultdict(list)
    
    for child, score in hits:
        parent_id = child.parent_id
        if not parent_id:
        # Trường hợp chunk không có parent_id thì bỏ qua
            continue
            
        parent_scores[parent_id].append(score)
        parent_matched_children[parent_id].append(child.content) # Hoặc dùng child.chunk_id tùy nhu cầu
        
    retrieved_results = []
    
    # 2. Tổng hợp lại thành các RetrievedChunk chứa Parent
    for parent_id, scores in parent_scores.items():
        parent_obj = store.parentChunks.get(parent_id)
        if parent_obj:
            # Lấy điểm số cao nhất trong các child thuộc parent này làm điểm đại diện
            best_score = max(scores)
            
            retrieved_results.append(
                RetrievedChunk(
                    parent=parent_obj,
                    score=best_score,
                    matched_children=parent_matched_children[parent_id]
                )
            )
            
    retrieved_results.sort(key=lambda x: x.score, reverse=True)
    return retrieved_results[:top_k]

if __name__ == "__main__":
    myStore = VectorStore()
    res = loaddoc("test.txt")
    
    if res is not None:
        doc_id = myStore.add(res)
        print(f"Đã thêm Document thành công! ID: {doc_id}")
        print(f"Tổng số Child Chunks: {len(myStore.childChunk)}")
        print(f"Tổng số Parent Chunks: {len(myStore.parentChunks)}\n")
        
        print("--- TEST RETRIEVE (PARENT-CHILD) ---")
        query_str = "Tell me about trinh la gi"
        results = retrieve(query_str, myStore, top_k=2)
        
        for idx, res_chunk in enumerate(results, 1):
            print(f"\n[Kết quả {idx}] Score: {res_chunk.score:.4f}")
            print(f"Parent Section: {res_chunk.parent.section}")
            print(f"Parent Content (rút gọn): {res_chunk.parent.content[:150]}...")
            print(f"Số lượng matched children: {len(res_chunk.matched_children)}")
    else:
        print("Không tìm thấy file test.txt trong thư mục data/raw/")