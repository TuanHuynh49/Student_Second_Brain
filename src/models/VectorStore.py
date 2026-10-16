from dataclasses import dataclass, field,asdict
import json 
from typing import List, Optional
from src.models.DocumentStore import DocumentStore
from src.models.DocumentChunk import ChildChunk,ParentChunk
from src.models.Document import Document
from datetime import datetime

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
    def save(self, path: str) -> None:
        """Lưu toàn bộ trạng thái ra JSON mà không cần hàm phụ trợ nào."""
        data = {
            "documents": {doc_id: asdict(doc) for doc_id, doc in self.documents.items()},
            "parent_chunks": {pid: asdict(p) for pid, p in self.parent_chunks.items()},
            "child_chunks": {cid: asdict(c) for cid, c in self.child_chunks.items()},
            "parents_in_doc": self.parents_in_doc,
            "children_in_parent": self.children_in_parent
        }
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4,default=str)
        print(f"Saved successfully to: {path}")

    @classmethod
    def load(cls, path: str) -> "DocumentStore":
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        store = cls()
        store.documents = {k: Document(**v) for k, v in data.get("documents", {}).items()}
        store.parent_chunks = {k: ParentChunk(**v) for k, v in data.get("parent_chunks", {}).items()}
        store.child_chunks = {k: ChildChunk(**v) for k, v in data.get("child_chunks", {}).items()}
        store.parents_in_doc = data.get("parents_in_doc", {})
        store.children_in_parent = data.get("children_in_parent", {})
        
        print(f"Đã tải thành công từ: {path}")
        return store

if __name__ == "__main__":
    store = VectorStore()
    res = loaddoc("test.txt")
    if res:
        store.add(res)
        
        # 1. Lưu ra file
        store.save("document_store_cache.json")
        
        # 2. Tải lại từ file vào một Store mới
        loaded_store = VectorStore.load("document_store_cache.json")
        print(f"Số lượng Document đã tải: {len(loaded_store.documents)}")
        print(f"Số lượng Child Chunks đã tải: {len(loaded_store.child_chunks)}")
    