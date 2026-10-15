from Document import Document
from DocumentChunk import ChildChunk,ParentChunk
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

class DocumentStore:
    documents:dict[str,Document]=field(default_factory=dict)
    parentChunks:dict[str,ParentChunk]=field(default_factory=dict)
    childChunk:dict[str,ChildChunk]=field(default_factory=dict)
    Parent_in_Doc:dict[str,list[str]]=field(default_factory=dict)
    Child_in_Parent:dict[str,list[str]]=field(default_factory=dict)

