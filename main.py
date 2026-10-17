
import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

from mcp import Client, StdioServerParameters

from src.agent.Loop import run_agent
from src.agent.Memory import SlidingWindowMemory
from src.LLM.Client import USAGE, reset_usage
from src.models.Schemas import Tool


def extract_tool_text(result) -> str:
    """Lấy phần text từ kết quả MCP."""
    parts = []

    for block in result.content or []:
        text = getattr(block, "text", None)
        if text:
            parts.append(text)

    content = "\n\n".join(parts)

    if getattr(result, "is_error", False):
        return f"Error: {content or 'MCP tool thất bại.'}"

    return content or "Tool không trả về nội dung."


def build_tools(client, server_tools) -> list[Tool]:
    """Chuyển schema MCP thành schema tool dùng bởi ReAct."""
    tools = []

    for server_tool in server_tools:

        async def call_mcp_tool(
            _tool_name=server_tool.name,
            **arguments
        ):
            result = await client.call_tool(
                _tool_name,
                arguments
            )
            return extract_tool_text(result)

        tools.append(
            Tool(
                name=server_tool.name,
                description=server_tool.description or "",
                parameters=server_tool.input_schema,
                fn=call_mcp_tool,
            )
        )

    return tools


async def main():
    print("=" * 65)
    print("STUDENT SECOND BRAIN")
    print("RAG + ReAct + MCP")
    print("=" * 65)

    server = StdioServerParameters(
        command="uv",
        args=["run", "python", "-m", "src.mcp.server"],
    )

    session_memory = SlidingWindowMemory(max_messages=10)
    reset_usage()

    async with Client(server) as client:
        # Lấy schema trực tiếp từ MCP Server.
        server_tools = (await client.list_tools()).tools
        tools = build_tools(client, server_tools)

        print("\nCác MCP tools đã khám phá:")
        for tool in tools:
            print(f"- {tool.name}: {tool.description}")

        if not tools:
            raise RuntimeError("MCP Server không cung cấp tool nào.")

        while True:
            try:
                user_input = input("\nSinh viên: ").strip()

                if not user_input:
                    continue

                if user_input.casefold() in {"exit", "quit"}:
                    print("\nĐã thoát Student Second Brain.")
                    print(f"Token usage: {USAGE}")
                    break

                print("\nSecond Brain đang xử lý...")

                answer = await run_agent(
                    user_task=user_input,
                    tools=tools,
                    memory=session_memory,
                    max_step=5,
                )

                print(f"\nPhản hồi:\n{answer}")
                print("-" * 65)

            except KeyboardInterrupt:
                print("\nĐã dừng chương trình.")
                break
            except Exception as exc:
                print(
                    f"\nLỗi xử lý câu hỏi: "
                    f"{type(exc).__name__}: {exc}"
                )


if __name__ == "__main__":
    asyncio.run(main())
