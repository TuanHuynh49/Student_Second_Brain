from src.models.Document import Document
from src.models.DocumentChunk import ChildChunk,ParentChunk
from src.ingestion.chunking.Chunking_helper import ParentChunking,ChildChunking
from dataclasses import dataclass, field,asdict
from typing import Optional
from src.ingestion.chunking.Chunking_helper import loaddoc
from datetime import datetime
import json
@dataclass
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
            childs_ids=[]
            childs=ChildChunking(parent)
            for child in childs:
                childid=self.add_child(child)
                childs_ids.append(child.chunk_id)
            self.Child_in_Parent[parent.parent_id]=childs_ids
        return doc.doc_id

    def add_parent(self,parent:ParentChunk)->str:
        if not parent.parent_id:
            parent.parent_id=f"parent_{len(self.parentChunks) + 1:04d}"
        self.parentChunks[parent.parent_id]=parent
        return parent.parent_id
    def add_child(self,child:ChildChunk)->str:
        if not child.chunk_id:
            child.chunk_id=f"child_{len(self.childChunk) + 1:04d}"
        self.childChunk[child.chunk_id]=child
        return child.chunk_id
    def list_all(self)->Optional[Document]:
        return list(self.documents.values())
    def get_id(self, doc_id: str) -> Optional[Document]:
        return self.documents.get(doc_id)
    def update(self, doc_id: str, title: str, content: str) -> bool:
        doc = self.get_id(doc_id)
        if doc is None:
            return False
        doc.title = title
        doc.content = content

        parent_ids = self.Parent_in_Doc.get(doc_id,[])
        for parent in parent_ids:
            child_id = self.Child_in_Parent.get(parent,[])
            for child in child_id:
                self.childChunk.pop(child, None)

            self.Child_in_Parent.pop(parent,None)
            self.parentChunks.pop(parent,None)

        self.Parent_in_Doc.pop(doc_id, None)

        new_doc = self.add(doc)
        return True       

if __name__=="__main__":
    myStore=DocumentStore()
    res= loaddoc("test.txt")
    id=myStore.add(res)
    print(myStore.childChunk)
    
