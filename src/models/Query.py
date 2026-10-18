from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class Query:
    text: str=""
    top_k: int = 5
    score_threshold:float=0.0
    metadata:dict=field(default_factory=dict)
    # course
    # doc_id