from dataclasses import dataclass, field
from typing import List, Optional
from DocumentStore import DocumentStore
@dataclass
class VectorStore(DocumentStore):
    Child_embedding:dict[str,Optional[list[float]]]