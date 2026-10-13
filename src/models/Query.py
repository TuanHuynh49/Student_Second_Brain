from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
@dataclass
class Query:
    text: str
    top_k: int = 5
