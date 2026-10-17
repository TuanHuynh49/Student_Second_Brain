
import asyncio

from mcp import Client, StdioServerParameters

from src.agent.Loop import run_agent
from src.agent.Memory import SlidingWindowMemory
from src.mcp.tool_adapter import discover_mcp_tools

from src.multi_agent.coordinator_agent import CoordinatorAgent
from src.multi_agent.multi_agent import MultiAgentSystem


async def main():
    # Khởi tạo Coordinator và Multi-Agent một lần.
    coordinator = CoordinatorAgent()
    multi_agent = MultiAgentSystem(max_attempts=3)

    # Bộ nhớ dành cho ReAct.
    memory = SlidingWindowMemory(max_messages=6)

    # Kết nối MCP và khám phá tools một lần.
    server = StdioServerParameters(
        command="uv",
        args=["run", "python", "-m", "src.mcp.server"],
    )

    async with Client(server) as client:
        tools = await discover_mcp_tools(client)

        print("Các MCP tools đã khám phá:")
        for tool in tools:
            print(f"- {tool.name}: {tool.description}")

        while True:
            query = input(
                "\nNhập câu hỏi (gõ exit để thoát): "
            ).strip()

            if query.casefold() == "exit":
                print("Đã thoát Student Second Brain.")
                break

            if not query:
                print("Vui lòng nhập câu hỏi.")
                continue

            try:
                # Bước 1: Phân loại đúng một lần.
                decision = coordinator.decide(query)
                
                print("[DEBUG main] Đã phân loại, chuẩn bị định tuyến.")

                intent = decision["intent"]

                print("\n[Coordinator] Intent:", intent)
                print("[Coordinator] Reason:", decision["reason"])

                # Bước 2: Chuyển yêu cầu đến đúng hệ thống.
                if intent == "search_documents":
                    result = await multi_agent.run(
                        user_query=query,
                        decision=decision,
                    )
                    answer = result["answer"]

                elif intent == "react_tools":
                    answer = await run_agent(
                        user_task=query,
                        tools=tools,
                        memory=memory,
                    )

                elif intent == "general_question":
                    answer = (
                        "Tôi là Student Second Brain. "
                        "Bạn có thể hỏi về tài liệu đã nạp "
                        "hoặc yêu cầu tôi thực hiện thao tác "
                        "được hỗ trợ."
                    )

                else:
                    answer = (
                        "Lỗi: Coordinator trả về intent không hợp lệ: "
                        f"{intent}"
                    )

                print("\nStudent Second Brain:", answer)

            except Exception as exc:
                print(
                    f"\n[ERROR] Không thể xử lý câu hỏi: "
                    f"{type(exc).__name__}: {exc}"
                )


if __name__ == "__main__":
    asyncio.run(main())
