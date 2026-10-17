from __future__ import annotations
from dataclasses import dataclass, field,asdict
import json 
from typing import List, Optional,Dict,Any
from src.rag.vectordb.DocumentStore import DocumentStore
from src.models.DocumentChunk import ChildChunk,ParentChunk
from src.models.Document import Document
from datetime import datetime
from src.rag.retrieval.cosin_similarity import cosine_similarity
from src.rag.retrieval.bm25 import build_bm25_index,normalise_scores
from src.rag.embeddings.embedding_helper import embed_tex,batch_embed_text
from src.ingestion.chunking.Chunking_helper import loaddoc
import os 
from dotenv import load_dotenv
load_dotenv()
@dataclass
class VectorStore(DocumentStore):
    def add(self, doc: Document, subject: str = None, child_max: int = 600, child_overlap: int = 80) -> str:
        doc_id = super().add(doc, subject, child_max=child_max, child_overlap=child_overlap)
        chunks_to_embed = []
        chunk_ids = []
        for parent_id in self.parents_in_doc.get(doc_id, []):
            for chunk_id in self.children_in_parent.get(parent_id, []):
                child = self.child_chunks.get(chunk_id)
                if child and child.embedding_matrix is None:
                    chunks_to_embed.append(child.content)
                    chunk_ids.append(chunk_id)
                    
        if chunks_to_embed:
            embeddings = batch_embed_text(chunks_to_embed)
            for chunk_id, embedding in zip(chunk_ids, embeddings):
                self.child_chunks[chunk_id].embedding_matrix = embedding
            
        return doc_id
    def dense_search(
        self, 
        query: str, 
        top_k: int = 10, 
        score_threshold: float = 0.0, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> list[tuple[ChildChunk, float]]:
        if not self.child_chunks:
            return []

        query_embedding = embed_tex(query)
        results = []

        for chunk in self.child_chunks.values():
            subject_filter = metadata.get('subject') if metadata else None
            doc_id_filter = metadata.get('doc_id') if metadata else None

            if subject_filter:
                if isinstance(subject_filter, list):
                    if chunk.metadata.get('subject') not in subject_filter:
                      continue
                else:
                    if chunk.metadata.get('subject') != subject_filter:
                      continue

            if doc_id_filter:
                if isinstance(doc_id_filter, list):
                   if chunk.doc_id not in doc_id_filter:
                     continue
                else:
                   if chunk.doc_id != doc_id_filter:
                      continue

           
            if chunk.embedding_matrix is not None:
                score = cosine_similarity(query_embedding, chunk.embedding_matrix)
                
                if score >= score_threshold:
                    results.append((chunk, score))
                
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    def hybrid_search(self, query: str, top_k: int = 10, alpha: float = 0.6, score_threshold: float = 0.0, metadata: Optional[Dict[str, Any]] = None) -> list[tuple[ChildChunk, float]]:
        if not self.child_chunks:
            return []

        chunk_list = list(self.child_chunks.values())
        bm25_index = build_bm25_index(chunk_list)

        query_embedding = embed_tex(query)
        dense_scores = []

        subject_filter = metadata.get('subject') if metadata else None
        doc_id_filter = metadata.get('doc_id') if metadata else None

        for chunk in chunk_list:
            filtered_out = False
            if subject_filter:
                if isinstance(subject_filter, list):
                    if chunk.metadata.get('subject') not in subject_filter:
                        filtered_out = True
                else:
                    if chunk.metadata.get('subject') != subject_filter:
                        filtered_out = True

            if doc_id_filter and not filtered_out:
                if isinstance(doc_id_filter, list):
                    if chunk.doc_id not in doc_id_filter:
                        filtered_out = True
                else:
                    if chunk.doc_id != doc_id_filter:
                        filtered_out = True

            # BẮT BUỘC phải append để giữ đúng độ dài bằng với chunk_list
            if filtered_out:
                dense_scores.append(float('-inf'))
                continue
            
            if chunk.embedding_matrix is not None:
                score = cosine_similarity(query_embedding, chunk.embedding_matrix)
                dense_scores.append(score)
            else:
                dense_scores.append(0.0)

        tokenized_query = query.lower().split()
        raw_bm25_scores = bm25_index.get_scores(tokenized_query)
        norm_bm25 = normalise_scores(raw_bm25_scores)

        hybrid_results = []
        for i, chunk in enumerate(chunk_list):
            if dense_scores[i] == float('-inf'):
                continue
            
            vec_score = dense_scores[i]
            bm25_score = norm_bm25[i]
            
            final_score = alpha * vec_score + (1 - alpha) * bm25_score
            
            if final_score >= score_threshold:
                hybrid_results.append((chunk, final_score))

        hybrid_results.sort(key=lambda x: x[1], reverse=True)
        return hybrid_results[:top_k]
    def save(self, path: Optional[str] = None) -> None:
        path = path or os.getenv("INDEX_SOURCE")
        data = {
            "documents": {doc_id: asdict(doc) for doc_id, doc in self.documents.items()},
            "parent_chunks": {pid: asdict(p) for pid, p in self.parent_chunks.items()},
            "child_chunks": {cid: asdict(c) for cid, c in self.child_chunks.items()},
            "parents_in_doc": self.parents_in_doc,
            "children_in_parent": self.children_in_parent
        }
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4,default=str)
        return True
    @classmethod
    def load(cls, path: Optional[str] = None) -> VectorStore:
        path = path or os.getenv("INDEX_SOURCE")
        with open(path, "r", encoding="utf-8") as f:
           data = json.load(f)

        store = cls()

        store.documents = {
          k: Document(**v)
          for k, v in data.get("documents", {}).items()
        }

        store.parent_chunks = {
            k: ParentChunk(**v)
            for k, v in data.get("parent_chunks", {}).items()
        }

        store.child_chunks = {
            k: ChildChunk(**v)
            for k, v in data.get("child_chunks", {}).items()
        }

        store.parents_in_doc = data.get("parents_in_doc", {})
        store.children_in_parent = data.get("children_in_parent", {})
        return store

    