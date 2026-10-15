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

if __name__ == "__main__":
    # Test thử bộ nhớ với cửa sổ trượt max_messages = 3
    mem = SlidingWindowMemory(max_messages=3)
    mem.set_system_prompt("Bạn là trợ lý học tập Student Second Brain.")

    print("--- Thêm 5 tin nhắn vào bộ nhớ ---")
    mem.add_message("user", "Chào bạn, tôi là Tuấn")
    mem.add_message("assistant", "Chào Tuấn, tôi có thể giúp gì?")
    mem.add_message("user", "BM25 là gì?")
    mem.add_message("assistant", "BM25 là thuật toán xếp hạng văn bản.")
    mem.add_message("user", "Nó dùng trong trường hợp nào?")

    current_msgs = mem.get_messages()
    print(f"\nSố lượng tin nhắn sau khi trượt (System + max 3 tin nhắn cuối): {len(current_msgs)}")
    for i, m in enumerate(current_msgs):
        print(f"{i+1}. [{m['role']}]: {m.get('content')}")
