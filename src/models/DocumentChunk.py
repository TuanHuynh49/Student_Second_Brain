from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
@dataclass
class ParentChunk:
    content: str=None
    parent_id: str=None
    doc_id: str=None
    source: str = None
    section: str = None
    parent_index: int = None
    metadata: dict = field(default_factory=dict)
@dataclass
class ChildChunk:
    content: str=None
    chunk_id: str=None
    parent_id: str=None
    doc_id: str=None
    chunk_index: int = None
    metadata: dict = field(default_factory=dict)
    embedding_matrix:Optional[list[float]]=None
@dataclass
class RetrievedChunk:
    parent: ParentChunk
    score: float                                 
    matched_children: list[str] = field(default_factory=list)
