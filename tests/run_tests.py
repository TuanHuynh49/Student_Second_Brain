
import asyncio
import logging
import json
from pathlib import Path

from mcp import Client, StdioServerParameters

from src.LLM.Client import reset_usage, USAGE
from src.agent.Loop import run_agent
from src.agent.Memory import SlidingWindowMemory
from src.mcp.tool_adapter import discover_mcp_tools
from src.mcp.run_logger import RunLogger, set_logger, log_event
from src.mcp.logger import setup_logger
from src.multi_agent.coordinator_agent import CoordinatorAgent
from src.multi_agent.multi_agent import MultiAgentSystem


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
TEST_FILE = BASE_DIR / "test.jsonl"

BATCH_SIZE = 12
TOTAL_RUNS = 3

logging.basicConfig(level=logging.INFO)
logger = setup_logger()


# ============================================================
# LOAD TESTSET
# ============================================================

def load_testset():
    if not TEST_FILE.exists():
        raise FileNotFoundError(
            f"Không tìm thấy file: {TEST_FILE}"
        )

    questions = []

    with TEST_FILE.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Lỗi JSON dòng {line_number}: {exc}"
                ) from exc

            if not isinstance(item, dict) or "question" not in item:
                raise ValueError(
                    f"Dòng {line_number} thiếu trường question."
                )

            questions.append(item)

    expected = BATCH_SIZE * TOTAL_RUNS

    if len(questions) != expected:
        raise ValueError(
            f"Cần {expected} câu hỏi, "
            f"nhưng test.jsonl hiện có {len(questions)} câu."
        )

    return questions


# ============================================================
# USAGE
# ============================================================

def get_usage_snapshot():
    prompt = int(USAGE.get("prompt_tokens", 0) or 0)
    completion = int(USAGE.get("completion_tokens", 0) or 0)

    return {
        "calls": int(USAGE.get("calls", 0) or 0),
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": prompt + completion,
        "max_prompt": int(USAGE.get("max_prompt", 0) or 0),
    }


# ============================================================
# RUN ONE QUESTION
# ============================================================

async def process_question(
    item,
    index,
    coordinator,
    multi_agent,
    tools,
    memory,
):
    query = item["question"].strip()

    reset_usage()

    log_event(
        "question_started",
        question_index=index,
        query=query,
        expected_answer=item.get("expected_answer"),
        no_answer=item.get("no_answer"),
    )

    status = "completed"
    answer = ""
    intent = None

    try:
        # 1. Coordinator
        decision = coordinator.decide(query)
        intent = decision.get("intent")

        log_event(
            "coordinator_decision",
            question_index=index,
            decision=decision,
        )

        # 2. Route
        if intent == "search_documents":
            result = await multi_agent.run(
                user_query=query,
                decision=decision,
            )

            answer = result.get(
                "answer",
                "Không tạo được câu trả lời.",
            )

            log_event(
                "multi_agent_completed",
                question_index=index,
                history=result.get("history", []),
                evidence_count=len(result.get("evidence", [])),
                evidence_check=result.get("evidence_check"),
            )

        elif intent == "react_tools":
            answer = await run_agent(
                user_task=query,
                tools=tools,
                memory=memory,
            )

            log_event(
                "react_agent_completed",
                question_index=index,
            )

        elif intent == "general_question":
            answer = (
                "Tôi là Student Second Brain. "
                "Bạn có thể hỏi về tài liệu đã nạp "
                "hoặc yêu cầu tôi thực hiện thao tác được hỗ trợ."
            )

        else:
            answer = f"Intent không hợp lệ: {intent}"
            status = "failed"

        log_event(
            "answer_completed",
            question_index=index,
            intent=intent,
            answer=answer,
        )

    except Exception as exc:
        status = "failed"
        answer = f"{type(exc).__name__}: {exc}"

        log_event(
            "question_error",
            question_index=index,
            error_type=type(exc).__name__,
            error=str(exc),
        )

        logger.exception(
            "Lỗi khi xử lý câu hỏi số %s", index
        )

    finally:
        # Usage riêng cho từng câu.
        usage = get_usage_snapshot()

        log_event(
            "usage",
            question_index=index,
            calls=usage["calls"],
            prompt_tokens=usage["prompt_tokens"],
            completion_tokens=usage["completion_tokens"],
            total_tokens=usage["total_tokens"],
            max_prompt=usage["max_prompt"],
        )

        log_event(
            "question_finished",
            question_index=index,
            query=query,
            intent=intent,
            status=status,
            answer=answer,
        )

        print(
            f"\n[{index}/12] {query}\n"
            f"Status: {status}\n"
            f"Usage: {usage}\n"
            f"Answer: {answer}\n"
        )


# ============================================================
# RUN ONE PASS = ONE JSONL LOG
# ============================================================

async def run_one_pass(run_number, questions):
    run_logger = RunLogger()
    set_logger(run_logger)

    status = "completed"

    try:
        log_event(
            "test_run_started",
            run_number=run_number,
            question_count=len(questions),
            test_file=TEST_FILE.name,
        )

        coordinator = CoordinatorAgent()
        multi_agent = MultiAgentSystem(max_attempts=3)
        memory = SlidingWindowMemory(max_messages=6)

        server = StdioServerParameters(
            command="uv",
            args=["run", "python", "-m", "src.mcp.server"],
        )

        async with Client(server) as client:
            tools = await discover_mcp_tools(client)

            log_event(
                "mcp_tools_discovered",
                tool_count=len(tools),
                tools=[
                    {
                        "name": tool.name,
                        "description": tool.description,
                    }
                    for tool in tools
                ],
            )

            for index, item in enumerate(questions, start=1):
                await process_question(
                    item=item,
                    index=index,
                    coordinator=coordinator,
                    multi_agent=multi_agent,
                    tools=tools,
                    memory=memory,
                )

        log_event(
            "test_run_finished",
            run_number=run_number,
            question_count=len(questions),
            status=status,
        )

    except Exception as exc:
        status = "failed"

        log_event(
            "test_run_error",
            run_number=run_number,
            error_type=type(exc).__name__,
            error=str(exc),
        )

        logger.exception("Lượt test %s thất bại", run_number)
        raise

    finally:
        log_path = run_logger.path

        try:
            run_logger.close(status=status)
        finally:
            set_logger(None)

        print(f"\nLog lượt {run_number}: {log_path}")


# ============================================================
# MAIN
# ============================================================

async def main():
    questions = load_testset()

    print(f"Đã nạp {len(questions)} câu hỏi.")
    print(f"Sẽ chạy {TOTAL_RUNS} lượt, mỗi lượt {BATCH_SIZE} câu.")

    for run_number in range(1, TOTAL_RUNS + 1):
        start = (run_number - 1) * BATCH_SIZE
        batch = questions[start:start + BATCH_SIZE]

        print(
            f"\n{'=' * 60}\n"
            f"BẮT ĐẦU RUN {run_number}/{TOTAL_RUNS}\n"
            f"Câu {start + 1} đến {start + BATCH_SIZE}\n"
            f"{'=' * 60}"
        )

        await run_one_pass(run_number, batch)

    print("\nĐÃ HOÀN THÀNH 3 LƯỢT KIỂM THỬ.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nĐã dừng kiểm thử.")
