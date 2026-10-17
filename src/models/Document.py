from dataclasses import dataclass,field
from datetime import datetime
from typing import Optional 

@dataclass
class Document:
    content:str=""
    doc_id: str=""
    title:str=None
    source:str=None
    metadata:dict=field(default_factory=dict)
    created_at:datetime=field(default_factory=datetime.now)
    