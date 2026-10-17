import asyncio
import shutil
import sys

from mcp import Client, StdioServerParameters

from src.LLM.Client import reset_usage, print_usage, USAGE
from src.agent.Loop import run_agent
from src.agent.Memory import SlidingWindowMemory
from src.mcp.tool_adapter import discover_mcp_tools
from src.mcp.run_logger import RunLogger, set_logger, log_event
from src.mcp.logger import setup_logger
from src.multi_agent.coordinator_agent import CoordinatorAgent
from src.multi_agent.multi_agent import MultiAgentSystem


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

        # Khởi tạo Coordinator và Multi-Agent một lần.
        coordinator = CoordinatorAgent()
        multi_agent = MultiAgentSystem(max_attempts=3)

        # Bộ nhớ dành cho ReAct.
        memory = SlidingWindowMemory(max_messages=6)

        # Cấu hình kết nối MCP tự động nhận diện uv hoặc python hiện tại.
        if shutil.which("uv"):
            server = StdioServerParameters(
                command="uv",
                args=["run", "python", "-m", "src.mcp.server"],
            )
        else:
            server = StdioServerParameters(
                command=sys.executable,
                args=["-m", "src.mcp.server"],
            )

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

            print("Các MCP tools đã khám phá:")
            for tool in tools:
                print(f"- {tool.name}: {tool.description}")

            while True:
                try:
                    query = input(
                        "\nNhập câu hỏi (gõ exit để thoát): "
                    ).strip()
                except (EOFError, KeyboardInterrupt):
                    print("\nĐang thoát Student Second Brain.")
                    log_event("application_exit_requested")
                    break

                if query.casefold() == "exit":
                    print("Đã thoát Student Second Brain.")
                    log_event("application_exit_requested")
                    break

                if not query:
                    print("Vui lòng nhập câu hỏi.")
                    continue

                # Reset thống kê cho câu hỏi hiện tại.
                reset_usage()

                log_event(
                    "question_started",
                    query=query,
                )

                try:
                    # Bước 1: Coordinator phân loại câu hỏi.
                    decision = coordinator.decide(query)

                    log_event(
                        "coordinator_decision",
                        intent=decision.get("intent"),
                        reason=decision.get("reason"),
                        decision=decision,
                    )

                    intent = decision.get("intent")
                    reason = decision.get("reason")

                    print(
                        "[DEBUG main] Đã phân loại, "
                        "chuẩn bị định tuyến."
                    )
                    print("\n[Coordinator] Intent:", intent)
                    print("[Coordinator] Reason:", reason)

                    evidence_list = []

                    # Bước 2: Định tuyến theo intent.
                    if intent == "search_documents":
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

                    # Bước 3: Trả lời người dùng.
                    print("\nStudent Second Brain:", answer)

                    log_event(
                        "answer_completed",
                        intent=intent,
                        answer=answer,
                    )

                    # Hiển thị evidence khi tìm kiếm tài liệu.
                    if intent == "search_documents":
                        print(
                            "\n========== SOURCES & EVIDENCE =========="
                        )

                        if not evidence_list:
                            print("Không có evidence để hiển thị.")
                        else:
                            for index, item in enumerate(
                                evidence_list,
                                start=1,
                            ):
                                print(f"\n--- Evidence {index} ---")
                                print(
                                    f"Score: "
                                    f"{item.get('score', 'N/A')}"
                                )
                                print(
                                    f"Document ID: "
                                    f"{item.get('doc_id', 'N/A')}"
                                )
                                print(
                                    f"Source: "
                                    f"{item.get('source', 'N/A')}"
                                )
                                print(
                                    f"Section: "
                                    f"{item.get('section', 'N/A')}"
                                )
                                print(
                                    f"Content:\n"
                                    f"{item.get('content', 'N/A')}"
                                )

                        print("========================================")

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
                        "\n[ERROR] Không thể xử lý câu hỏi: "
                        f"{type(exc).__name__}: {exc}"
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
        print("\nStudent Second Brain đã dừng.")
    except Exception as exc:
        print(
            "\nỨng dụng kết thúc do lỗi: "
            f"{type(exc).__name__}: {exc}"
        )