from dataclasses import dataclass, field, asdict
from typing import Optional, List
from pathlib import Path
from datetime import datetime
import json

from src.models.Document import Document
from src.models.DocumentChunk import ChildChunk, ParentChunk, RetrievedChunk
from src.ingestion.chunking.Chunking_helper import ParentChunking, ChildChunking, loaddoc
from src.rag.embeddings.embedding_helper import embed_tex
from src.rag.retrieval.cosin_similarity import cosine_similarity
from dotenv import load_dotenv
import os 
load_dotenv()

@dataclass
class DocumentStore:
    documents: dict[str, Document] = field(default_factory=dict)
    parent_chunks: dict[str, ParentChunk] = field(default_factory=dict)
    child_chunks: dict[str, ChildChunk] = field(default_factory=dict)
    parents_in_doc: dict[str, list[str]] = field(default_factory=dict)
    children_in_parent: dict[str, list[str]] = field(default_factory=dict)

    def validate(self, doc: Document, parents: list[ParentChunk], children: list[ChildChunk]) -> None:
        """Kiểm tra dữ liệu trước khi ghi."""
        if not doc.doc_id:
            raise ValueError("doc_id chưa được gán cho Document")
 
        parent_ids: set[str] = set()
        for p in parents:
            if not p.parent_id:
                raise ValueError(f"ParentChunk thiếu parent_id (section={p.section!r})")
            if p.parent_id in parent_ids:
                raise ValueError(f"parent_id bị trùng trong tài liệu: {p.parent_id}")
            if p.doc_id != doc.doc_id:
                raise ValueError(f"{p.parent_id}: doc_id={p.doc_id!r} khác tài liệu {doc.doc_id!r}")
            parent_ids.add(p.parent_id)
 
        child_ids: set[str] = set()
        for c in children:
            if not c.chunk_id:
                raise ValueError(f"ChildChunk thiếu chunk_id")
            if c.chunk_id in child_ids:
                raise ValueError(f"chunk_id bị trùng trong tài liệu: {c.chunk_id}")
            if c.parent_id not in parent_ids:
                raise ValueError(f"{c.chunk_id}: parent_id {c.parent_id!r} không có trong danh sách cha")
            if c.doc_id != doc.doc_id:
                raise ValueError(f"{c.chunk_id}: doc_id={c.doc_id!r} khác tài liệu {doc.doc_id!r}")
            child_ids.add(c.chunk_id)

    def add(self, doc: Document, child_max: int = 600, child_overlap: int = 80) -> str:
        self._assign_document_id(doc)

        if doc.doc_id in self.documents:
            self.delete_document(doc.doc_id)

        parents, children = self._generate_chunks(doc, child_max=child_max, child_overlap=child_overlap)

        self.validate(doc, parents, children)
        self._persist(doc, parents, children)

        return doc.doc_id

    def _assign_document_id(self, doc: Document) -> None:
        if not doc.doc_id:
            doc.title = doc.title or "unnamed"
            doc.doc_id = f"doc_{doc.title}"
            
        if "course" not in doc.metadata or not doc.metadata["course"]:
            doc.metadata["subject"] = "General"
        
    def _generate_chunks(self, doc: Document, child_max: int = 600, child_overlap: int = 80) -> tuple[list[ParentChunk], list[ChildChunk]]:
        # Giữ nguyên cấu trúc structural chunking cũ bên dưới phần header
        raw_parents = ParentChunking(doc) or []
        parents = []
        for idx, p in enumerate(raw_parents, 1):
            p.doc_id = doc.doc_id
            p.metadata["course"] = doc.metadata.get("course", "General")
            p.metadata["week"] = doc.metadata.get("week", "")
            p.parent_id = f"parent_{doc.title}_{idx:03d}"
            parents.append(p)

        children = []
        child_counter = 1
        for p in parents:
            raw_children = ChildChunking(p, child_max=child_max, child_overlap=child_overlap) or []
            for c in raw_children:
                c.doc_id = doc.doc_id
                c.parent_id = p.parent_id
                c.metadata["course"] = doc.metadata.get("course", "Genral")
                c.metadata["week"] = doc.metadata.get("week", "")
                c.chunk_id = f"child_{doc.title}_{child_counter:04d}"
                children.append(c)
                child_counter += 1
                
        return parents, children

    def _persist(self, doc: Document, parents: list[ParentChunk], children: list[ChildChunk]) -> None:
        self.documents[doc.doc_id] = doc
        self.parents_in_doc[doc.doc_id] = [p.parent_id for p in parents]
        
        for p in parents:
            self.parent_chunks[p.parent_id] = p
            self.children_in_parent[p.parent_id] = []
            
        for c in children:
            self.child_chunks[c.chunk_id] = c
            self.children_in_parent[c.parent_id].append(c.chunk_id)
    
    def list_all(self) -> list[Document]:
        return list(self.documents.values())

    def delete_document(self, doc_id: str) -> list[str]:
        if doc_id not in self.documents:
            return []
        removed_children: list[str] = []
        for parent_id in self.parents_in_doc.pop(doc_id, []):
            for chunk_id in self.children_in_parent.pop(parent_id, []):
                self.child_chunks.pop(chunk_id, None)
                removed_children.append(chunk_id)
            self.parent_chunks.pop(parent_id, None)
        del self.documents[doc_id]
        return removed_children
    def get_document(self, doc_id: str) -> Optional[Document]:
        return self.documents.get(doc_id)

    def get_parent(self, parent_id: str) -> Optional[ParentChunk]:
        return self.parent_chunks.get(parent_id)

    def get_child(self, child_id: str) -> Optional[ChildChunk]:
        return self.child_chunks.get(child_id)

    def get_parents_by_document(self, doc_id: str) -> list[ParentChunk]:
        parent_ids = self.parents_in_doc.get(doc_id, [])
        return [self.parent_chunks[pid] for pid in parent_ids if pid in self.parent_chunks]

    def get_children_by_parent(self, parent_id: str) -> list[ChildChunk]:
        child_ids = self.children_in_parent.get(parent_id, [])
        return [self.child_chunks[cid] for cid in child_ids if cid in self.child_chunks]

    def get_children_by_document(self, doc_id: str) -> list[ChildChunk]:
        all_children = []
        parent_ids = self.parents_in_doc.get(doc_id, [])
        for pid in parent_ids:
            child_ids = self.children_in_parent.get(pid, [])
            for cid in child_ids:
                if cid in self.child_chunks:
                    all_children.append(self.child_chunks[cid])
        return all_children
    
