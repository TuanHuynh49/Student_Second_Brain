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