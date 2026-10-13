from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
@dataclass
class ParentChunk:
    content: str
    parent_id: str
    doc_id: str
    source: str = ""
    page: Optional[int] = None
    section: str = ""
    parent_index: int = 0
    metadata: dict = field(default_factory=dict)
@dataclass
class ChildChunk:
    content: str
    chunk_id: str
    parent_id: str
    doc_id: str
    chunk_index: int = 0
    language: str = "vi"
    metadata: dict = field(default_factory=dict)
    embedding: Optional[list[float]] = None
@dataclass
class RetrievedChunk:
    parent: ParentChunk
    score: float                                 
    matched_children: list[str] = field(default_factory=list)