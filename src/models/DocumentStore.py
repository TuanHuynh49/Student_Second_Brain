from Document import Document
from DocumentChunk import ChildChunk,ParentChunk
from src.ingestion.chunking.Chunking_helper import ParentChunking,ChildChunking
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

class DocumentStore:
    documents:dict[str,Document]=field(default_factory=dict)
    parentChunks:dict[str,ParentChunk]=field(default_factory=dict)
    childChunk:dict[str,ChildChunk]=field(default_factory=dict)
    Parent_in_Doc:dict[str,list[str]]=field(default_factory=dict)
    Child_in_Parent:dict[str,list[str]]=field(default_factory=dict)

    def add(self,doc:Document)->str:
        if not doc.doc_id:
            doc.doc_id=f"doc_{len(self.documents)+1:04d}"
        self.documents[doc.doc_id]=doc
        parents=ParentChunking(doc)
        parents_ids=[]
        for parent in parents:
            parent_id=self.add_parent(parent)
            parents_ids.append(parent_id)
        self.Parent_in_Doc[doc.doc_id]=parents_ids
        for parent in parents:
            childs=ChildChunking(parent)


            

    def add_parent(self,parent:ParentChunk)->str:
        if not parent.parent_id:
            parent.parent_id=f"parent_{len(self.chunks) + 1:04d}"
        self.parentChunks[parent.parent_id]=parent
        return parent.parent_id
    def add_child(self,child:ChildChunking)->str:
        if not child.:
            parent.parent_id=f"parent_{len(self.chunks) + 1:04d}"
        self.parentChunks[parent.parent_id]=parent
        return parent.parent_id
