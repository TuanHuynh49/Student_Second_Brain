from dataclasses import dataclass, field
from typing import List, Optional
from src.models.DocumentStore import DocumentStore
from src.models.DocumentChunk import ChildChunk,ParentChunk
from src.ingestion.embedding.embedding_helper import embed_tex,cosine_similarity
from src.ingestion.chunking.Chunking_helper import loaddoc

@dataclass
class VectorStore(DocumentStore):
    def add_child(self, child):
        if child.embedding_matrix is None:
            child.embedding_matrix=embed_tex(child.content)
        return super().add_child(child)
    def search(self, query: str, top_k: int = 3) -> list[tuple[ChildChunk, float]]:
        query_embedding = embed_tex(query)
        results=[]
        for chunk in self.childChunk.values():
            if chunk.embedding_matrix is not None:
                score=cosine_similarity(query_embedding,chunk.embedding_matrix)
                results.append((chunk,score))
        results.sort(key=lambda x:x[1],reverse=True)
        return results[:top_k]

if __name__=="__main__":
    myStore = VectorStore()
    res = loaddoc("test.txt")
    
    if res is not None:
        doc_id = myStore.add(res)
        print(f"Đã thêm Document thành công! ID: {doc_id}")
        print(f"Tổng số Child Chunks được tạo và nhúng vector: {len(myStore.childChunk)}\n")
        
        print("--- THÔNG TIN CHUNK 0001 ---")
        print(myStore.childChunk.get("child_0001"))
        
        print("\n--- TEST TÌM KIẾM ---")
        for chunk, score in myStore.search("Tell me about trinh la gi"):
            print(f"Score: {score:.4f} | Content: {chunk.content[:100]}...")
    else:
        print("Không tìm thấy file test.txt trong thư mục data/raw/")
    