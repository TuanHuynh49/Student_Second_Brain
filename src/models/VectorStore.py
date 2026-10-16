from dataclasses import dataclass, field
from typing import List, Optional
from src.models.DocumentStore import DocumentStore
from src.models.DocumentChunk import ChildChunk,ParentChunk
from src.models.Document import Document

from src.ingestion.embedding.embedding_helper import embed_tex,cosine_similarity
from src.ingestion.chunking.Chunking_helper import loaddoc
@dataclass
class VectorStore(DocumentStore):
    def add(self, doc: Document) -> str:
        doc_id = super().add(doc)
        for parent_id in self.parents_in_doc.get(doc_id, []):
            for chunk_id in self.children_in_parent.get(parent_id, []):
                child = self.child_chunks[chunk_id]
                if child.embedding_matrix is None:
                    child.embedding_matrix = embed_tex(child.content)
        return doc_id
    def search(self, query: str, top_k: int = 3) -> list[tuple[ChildChunk, float]]:
        query_embedding = embed_tex(query)
        results=[]
        for chunk in self.child_chunks.values():
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
        print(f"Đã thêm thành công Document ID: {doc_id}")
        print(f"Số lượng Parent Chunks: {len(myStore.parent_chunks)}")
        print(f"Số lượng Child Chunks: {len(myStore.child_chunks)}")
        
        # Test kiểm tra ID theo file của một child chunk bất kỳ
        first_child_id = list(myStore.child_chunks.keys())[0]
        print(f"Ví dụ ID của Child Chunk: {first_child_id}")
        
        print("\n--- TEST TÌM KIẾM VECTOR ---")
        for chunk, score in myStore.search("Tell me about trinh la gi"):
            print(f"Score: {score:.4f} | Chunk ID: {chunk.chunk_id} | Content: {chunk.content[:80]}...")
    else:
        print("Không tìm thấy file test.txt trong thư mục data/raw/")
    