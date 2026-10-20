from typing import List, Dict, Any

class SlidingWindowMemory:
    def __init__(self, max_messages: int = 6):
        self.max_messages = max_messages
        self.system_message: Dict[str, Any] = None
        self.history: List[Dict[str, Any]] = []

    def set_system_prompt(self, content: str):
        self.system_message = {
            "role": "system",
            "content": content
        }

    def add_message(self, role: str, content: str = None, **kwargs):
        msg = {
            "role": role
        }

        if content is not None:
            msg["content"] = content
        
        msg.update(kwargs)
        self.history.append(msg)

    def get_messages(self) -> List[Dict[str, Any]]:
        if len(self.history) > self.max_messages:
            recent_history = self.history[-self.max_messages:]
        else:
            recent_history = self.history

        result = []
        if self.system_message:
            result.append(self.system_message)

        result.extend(recent_history)
        return result

    def clear(self):
        self.history = []

