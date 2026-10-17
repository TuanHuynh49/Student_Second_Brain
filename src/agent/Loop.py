import json
import sys
from pathlib import Path
import inspect

sys.path.append(str(Path(__file__).resolve().parent.parent))

from LLM.Client import call_llm
from models.Schemas import Tool
from agent.Memory import SlidingWindowMemory

def load_prompt(filename: str = "agent_react.txt") -> str:
    prompt_path = Path(__file__).resolve().parent.parent / "prompts" /filename
    return prompt_path.read_text(encoding="utf-8").strip()

async def run_agent(
    user_task: str,
    system_prompt: str | None = None,
    memory: SlidingWindowMemory | None = None,
    tools=(),
    max_step: int = 5,
    name: str = "Student Second Brain",
) -> str:
    """Chạy ReAct loop, hỗ trợ cả tool đồng bộ và bất đồng bộ."""

    user_task = user_task.strip()
    if not user_task:
        return "Vui lòng nhập câu hỏi."

    if max_step < 1:
        raise ValueError("max_step phải lớn hơn hoặc bằng 1.")

    if system_prompt is None:
        system_prompt = load_prompt("agent_react.txt")

    if memory is None:
        memory = SlidingWindowMemory(max_messages=10)

    if not memory.system_message:
        memory.set_system_prompt(system_prompt)

    memory.add_message("user", user_task)

    registry = {tool.name: tool for tool in tools}
    schemas = [tool.schema() for tool in tools] if tools else None
    messages = memory.get_messages()

    for step in range(max_step):
        # call_llm hiện tại là hàm đồng bộ.
        msg = call_llm(messages, tools=schemas)
        messages.append(msg)

        tool_calls = getattr(msg, "tool_calls", None)

        if not tool_calls:
            final_content = (
                getattr(msg, "content", None)
                or "Tôi chưa tạo được câu trả lời."
            )
            memory.add_message("assistant", final_content)
            return final_content

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            raw_arguments = tool_call.function.arguments or "{}"

            try:
                arguments = json.loads(raw_arguments)

                if not isinstance(arguments, dict):
                    raise ValueError("Tool arguments phải là JSON object.")

                tool = registry.get(function_name)

                if tool is None:
                    result = f"Error: Không tìm thấy tool '{function_name}'."
                else:
                    result = tool.fn(**arguments)

                    if inspect.isawaitable(result):
                        result = await result

                    if result is None:
                        result = "Error: Tool không trả về kết quả."

                    result = str(result)

            except json.JSONDecodeError:
                result = "Error: LLM trả về tool arguments không phải JSON hợp lệ."
            except TypeError as exc:
                result = f"Error: Tham số tool không hợp lệ: {exc}"
            except Exception:
                result = "Error: Tool thực thi thất bại. Hãy kiểm tra log server."

            print(
                f"[{name}] Bước {step + 1}: "
                f"{function_name}({raw_arguments})"
            )
            print(f"[{name}] Kết quả: {result}")

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                }
            )

    message = (
        "Đã đạt giới hạn số bước. "
        "Tác vụ chưa được xác nhận hoàn thành."
    )
    memory.add_message("assistant", message)
    return message


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


        