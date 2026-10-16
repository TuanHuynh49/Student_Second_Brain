from dataclasses import dataclass
from typing import Callable, Dict, Any


@dataclass
class Tool:
    name: str
    description: str
    parameters: Dict[str, Any]
    fn: Callable

    def schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }
