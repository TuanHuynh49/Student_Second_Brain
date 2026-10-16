import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from LLM.Client import call_llm
from models.Schemas import Tool
from agent.Memory import SlidingWindowMemory

def load_prompt(filename: str = "agent_react.txt") -> str:
    prompt_path = Path(__file__).resolve().parent.parent / "prompts" /filename
    return prompt_path.read_text(encoding="utf-8").strip()

def run_agent(user_task: str, system_prompt: str = None, memory: SlidingWindowMemory = None, tools=(), max_step: int = 5, name: str = "StudentSecondBrain"):
    if system_prompt is None:
        system_prompt = load_prompt("agent_react.txt")

    if memory is None:
        memory = SlidingWindowMemory(max_messages=6)

    if not memory.system_message:
        memory.set_system_prompt(system_prompt)

    memory.add_message("user", user_task)        

    registry = {t.name: t for t in tools}

    schemas = [t.schema() for t in tools] if tools else None

    messages = memory.get_messages()

    has_written = False
    has_verified = False

    for step in range(max_step):
        msg = call_llm(messages, tools=schemas)
        messages.append(msg)


        if not getattr(msg, "tool_calls", None):
            final_content = msg.content or "Nhiệm vụ đã hoàn thành."
            memory.add_message("assistant", final_content)
            return final_content

        for tc in msg.tool_calls:
            fn_name = tc.function.name
            args = json.loads(tc.function.arguments)
            print(f"[{name}] Bước {step + 1}: Gọi {fn_name} ({args})")
            try:
                if fn_name not in registry:
                    result = f"Error: Tool '{fn_name}' không tồn tại"
                else:
                    result = registry[fn_name].fn(**args)
                    if "save" in fn_name or "write" in fn_name:
                        has_written = True
                    if has_written and ("get" in fn_name or "read" in fn_name or "verify" in fn_name):
                        has_verified = True
            except Exception as e:
                result = f"Error: {e}"

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": str(result)
            })

    return "[Đã đạt giới hạn max_steps mà chưa hoàn thành nhiệm vụ]"

if __name__ == "__main__":
    # 1. Giả lập 2 công cụ (1 tool ghi + 1 tool đọc verify)
    FAKE_DB = {}

    def save_note(topic: str, content: str) -> str:
        """Lưu một ghi chú học tập vào cơ sở dữ liệu."""
        note_id = f"NOTE_{len(FAKE_DB) + 1}"
        FAKE_DB[note_id] = {"topic": topic, "content": content}
        return f"Đã lưu thành công với mã {note_id}"

    def get_note(note_id: str) -> str:
        """Đọc và kiểm chứng nội dung ghi chú theo mã ID."""
        if note_id in FAKE_DB:
            return f"Xác nhận ghi chú {note_id} tồn tại: {FAKE_DB[note_id]}"
        return f"Error: Không tìm thấy ghi chú {note_id}"

    # 2. Đóng gói vào class Tool chuẩn
    mock_tools = [
        Tool(
            name="save_note",
            description="Lưu một ghi chú học tập mới vào hệ thống.",
            parameters={
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "content": {"type": "string"}
                },
                "required": ["topic", "content"]
            },
            fn=save_note
        ),
        Tool(
            name="get_note",
            description="Đọc và xác minh ghi chú đã lưu theo mã ID.",
            parameters={
                "type": "object",
                "properties": {
                    "note_id": {"type": "string"}
                },
                "required": ["note_id"]
            },
            fn=get_note
        )
    ]

    # 3. Khởi tạo một phiên bộ nhớ cho sinh viên
    session_memory = SlidingWindowMemory(max_messages=6)

    print("🚀 === LƯỢT 1: YÊU CẦU LƯU GHI CHÚ ===")
    task1 = "Hãy lưu ghi chú về 'Thuật toán BM25' với nội dung 'BM25 dùng để xếp hạng từ khóa' vào hệ thống."
    answer1 = run_agent(user_task=task1, tools=mock_tools, memory=session_memory)
    print(f"\n🏁 Trả lời Lượt 1:\n{answer1}")

    print("\n" + "=" * 50 + "\n")

    print("🧠 === LƯỢT 2: KIỂM TRA TRÍ NHỚ (MULTI-TURN) ===")
    task2 = "Ghi chú tôi vừa lưu có mã ID là gì và nội dung là gì?"
    answer2 = run_agent(user_task=task2, tools=mock_tools, memory=session_memory)
    print(f"\n🏁 Trả lời Lượt 2:\n{answer2}")


        