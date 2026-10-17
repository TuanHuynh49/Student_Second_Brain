import asyncio

from mcp import Client, StdioServerParameters

from src.LLM.Client import reset_usage, print_usage, USAGE
from src.agent.Loop import run_agent
from src.agent.Memory import SlidingWindowMemory
from src.mcp.tool_adapter import discover_mcp_tools
from src.mcp.run_logger import RunLogger, set_logger, log_event
from src.mcp.logger import setup_logger
from src.multi_agent.coordinator_agent import CoordinatorAgent
from src.multi_agent.multi_agent import MultiAgentSystem

# ──────────────────────────────────────────────
BANNER = """
╔══════════════════════════════════════════════╗
║   🧠  S T U D E N T  S E C O N D  B R A I N  ║
║        AI-Powered Study Assistant v1.0       ║
╚══════════════════════════════════════════════╝
"""
DIVIDER  = "─" * 50
DIVIDER2 = "═" * 50


def _sep(char: str = "─", n: int = 50) -> str:
    return char * n


async def main():
    # Khởi tạo logger ghi log thông thường.
    app_logger = setup_logger()

    # Mỗi lần chạy ứng dụng tạo một file JSONL riêng.
    run_logger = RunLogger()
    set_logger(run_logger)

    status = "completed"

    try:
        app_logger.info("Student Second Brain đang khởi động...")
        log_event("application_started")

        print(BANNER)
        print("⚙️  Đang khởi tạo hệ thống...")

        # Khởi tạo Coordinator và Multi-Agent một lần.
        coordinator = CoordinatorAgent()
        multi_agent = MultiAgentSystem(max_attempts=3)

        # Bộ nhớ dành cho ReAct.
        memory = SlidingWindowMemory(max_messages=6)

        print("✅  Coordinator & Multi-Agent sẵn sàng.")

        # Cấu hình kết nối MCP.
        server = StdioServerParameters(
            command="uv",
            args=["run", "python", "-m", "src.mcp.server"],
        )

        print("🔌  Đang kết nối MCP Server...")

        async with Client(server) as client:
            # Khám phá tools một lần khi khởi động.
            tools = await discover_mcp_tools(client)

            log_event(
                "mcp_tools_discovered",
                tools=[
                    {
                        "name": tool.name,
                        "description": tool.description,
                    }
                    for tool in tools
                ],
                tool_count=len(tools),
            )

            print(f"🛠️  Đã khám phá {len(tools)} MCP tool(s):")
            for tool in tools:
                print(f"   ├─ 🔧 {tool.name}: {tool.description}")

            print()
            print(_sep("═"))
            print("💬  Hệ thống đã sẵn sàng! Bắt đầu hỏi đáp.")
            print(_sep("═"))

            while True:
                try:
                    query = input(
                        "\n❓ Nhập câu hỏi (gõ 'exit' để thoát): "
                    ).strip()
                except (EOFError, KeyboardInterrupt):
                    print("\n👋  Đang thoát Student Second Brain...")
                    log_event("application_exit_requested")
                    break

                if query.casefold() == "exit":
                    print("👋  Đã thoát Student Second Brain. Tạm biệt!")
                    log_event("application_exit_requested")
                    break

                if not query:
                    print("⚠️  Vui lòng nhập câu hỏi.")
                    continue

                # Reset thống kê cho câu hỏi hiện tại.
                reset_usage()

                log_event(
                    "question_started",
                    query=query,
                )

                print()
                print(_sep())

                try:
                    # ── Bước 1: Coordinator phân loại câu hỏi ──
                    print("🎯  [Bước 1/3] Coordinator đang phân loại câu hỏi...")
                    decision = coordinator.decide(query)

                    log_event(
                        "coordinator_decision",
                        intent=decision.get("intent"),
                        reason=decision.get("reason"),
                        decision=decision,
                    )

                    intent = decision.get("intent")
                    reason = decision.get("reason")

                    intent_icons = {
                        "search_documents": "📚",
                        "react_tools":      "🔧",
                        "general_question": "💬",
                    }
                    icon = intent_icons.get(intent, "❓")

                    print(f"   ├─ {icon} Intent : {intent}")
                    print(f"   └─ 💡 Reason : {reason}")

                    evidence_list = []

                    # ── Bước 2: Định tuyến theo intent ──
                    if intent == "search_documents":
                        print(
                            "\n📖  [Bước 2/3] 🧠 StudentSecondBrain đang trả lời:"
                            " đang tìm kiếm tài liệu & tổng hợp câu trả lời..."
                        )
                        result = await multi_agent.run(
                            user_query=query,
                            decision=decision,
                        )

                        answer = result.get(
                            "answer",
                            "Không tạo được câu trả lời.",
                        )

                        evidence_list = result.get(
                            "evidence",
                            [],
                        )

                        log_event(
                            "multi_agent_completed",
                            intent=intent,
                            history=result.get("history", []),
                            evidence_check=result.get(
                                "evidence_check"
                            ),
                            evidence_count=len(evidence_list),
                        )

                    elif intent == "react_tools":
                        print(
                            "\n⚙️  [Bước 2/3] 🧠 StudentSecondBrain đang trả lời:"
                            " đang thực thi công cụ (ReAct Agent)..."
                        )
                        answer = await run_agent(
                            user_task=query,
                            tools=tools,
                            memory=memory,
                        )

                        log_event(
                            "react_agent_completed",
                            intent=intent,
                        )

                    elif intent == "general_question":
                        print(
                            "\n💬  [Bước 2/3] 🧠 StudentSecondBrain đang trả lời..."
                        )
                        answer = (
                            "Tôi là Student Second Brain. "
                            "Bạn có thể hỏi về tài liệu đã nạp "
                            "hoặc yêu cầu tôi thực hiện thao tác "
                            "được hỗ trợ."
                        )

                    else:
                        answer = (
                            "Lỗi: Coordinator trả về intent "
                            f"không hợp lệ: {intent}"
                        )

                    # ── Bước 3: Trả lời người dùng ──
                    print(f"\n✅  [Bước 3/3] Câu trả lời:")
                    print(_sep())
                    print(f"🧠 StudentSecondBrain:\n{answer}")
                    print(_sep())

                    log_event(
                        "answer_completed",
                        intent=intent,
                        answer=answer,
                    )

                    # Hiển thị evidence khi tìm kiếm tài liệu.
                    if intent == "search_documents":
                        print(
                            f"\n📎  SOURCES & EVIDENCE  ({len(evidence_list)} nguồn)"
                        )
                        print(_sep("═"))

                        if not evidence_list:
                            print("   ⚠️  Không có evidence để hiển thị.")
                        else:
                            for index, item in enumerate(
                                evidence_list,
                                start=1,
                            ):
                                print(f"\n  📄 Evidence #{index}")
                                print(f"  ├─ ⭐ Score     : {item.get('score', 'N/A')}")
                                print(f"  ├─ 🆔 Doc ID    : {item.get('doc_id', 'N/A')}")
                                print(f"  ├─ 📁 Source    : {item.get('source', 'N/A')}")
                                print(f"  ├─ 📑 Section   : {item.get('section', 'N/A')}")
                                print(f"  └─ 📝 Content   :\n     {item.get('content', 'N/A')}")

                        print(_sep("═"))

                except Exception as exc:
                    log_event(
                        "question_error",
                        error_type=type(exc).__name__,
                        error=str(exc),
                    )

                    app_logger.exception(
                        "Không thể xử lý câu hỏi."
                    )

                    print(
                        f"\n❌  [LỖI] Không thể xử lý câu hỏi:\n"
                        f"   {type(exc).__name__}: {exc}"
                    )

                finally:
                    # Ghi usage riêng cho câu hỏi vừa xử lý.
                    usage = dict(USAGE)

                    prompt_tokens = usage.get(
                        "prompt_tokens",
                        0,
                    )
                    completion_tokens = usage.get(
                        "completion_tokens",
                        0,
                    )

                    log_event(
                        "usage",
                        calls=usage.get("calls", 0),
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        total_tokens=(
                            prompt_tokens + completion_tokens
                        ),
                        max_prompt=usage.get("max_prompt", 0),
                    )

                    print_usage()

    except Exception as exc:
        status = "failed"

        log_event(
            "application_error",
            error_type=type(exc).__name__,
            error=str(exc),
        )

        app_logger.exception(
            "Student Second Brain gặp lỗi khi chạy."
        )

        raise

    finally:
        # Luôn ghi sự kiện kết thúc khi ứng dụng dừng.
        try:
            run_logger.close(status=status)
        finally:
            set_logger(None)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋  Student Second Brain đã dừng. Tạm biệt!")
    except Exception as exc:
        print(
            "\n💥  Ứng dụng kết thúc do lỗi:\n"
            f"   {type(exc).__name__}: {exc}"
        )