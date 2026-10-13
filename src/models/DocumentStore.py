from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import Document
import DocumentChunk
@dataclass 
class DocumentStore:
    documents:dict[str,Document]=field(default_factory=dict)
    chunks:dict[str,DocumentChunk]=field(default_factory=dict)

    def add(self,document:Document)->str:
        if not document.doc_id:
            document.doc_id=f"doc_{len(self.documents)+1:04d}"
        self.documents[document.doc_id]=document

        

