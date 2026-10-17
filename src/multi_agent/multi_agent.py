
import asyncio

from src.multi_agent.coordinator_agent import (
    CoordinatorAgent,
    client,
    model,
)
from src.multi_agent.research_agent import ResearchAgent
from src.multi_agent.answer_agent import AnswerAgent
from src.multi_agent.evidence_checker_agent import EvidenceCheckerAgent


class MultiAgentSystem:
    def __init__(self, max_attempts: int = 3):
        self.coordinator = CoordinatorAgent()
        self.researcher = ResearchAgent()
        self.answer_agent = AnswerAgent()
        self.evidence_checker = EvidenceCheckerAgent(client, model)

        # Tổng số lượt tìm kiếm tối đa, tính cả lượt đầu.
        self.max_attempts = max(1, max_attempts)

    async def run(self,user_query: str,decision: dict | None = None) -> dict:
        user_query = user_query.strip()

        if not user_query:
            raise ValueError("Câu hỏi không được để trống.")

        if decision is None:
            decision = self.coordinator.decide(user_query)
            print("\n[Coordinator] Intent:", decision["intent"])
            print("[Coordinator] Reason:", decision["reason"])

        research_result = None
        evidence_check = None
        final_answer = None
        history = []

        if decision["intent"] == "general_question":
            final_answer = (
                "Tôi là Student Second Brain. "
                "Bạn hãy đặt câu hỏi liên quan đến tài liệu "
                "đã được nạp để tôi tra cứu."
            )

        elif decision["intent"] == "search_documents":
            current_query = decision["query"]

            for attempt in range(1, self.max_attempts + 1):
                print(
                    f"\n[Research] Lượt tìm kiếm "
                    f"{attempt}/{self.max_attempts}"
                )
                print("[Research] Query:", current_query)

                # 1. Coordinator -> Research Agent
                research_result = await self.researcher.research(
                    current_query
                )

                status = research_result.get("status")
                evidence = research_result.get("evidence", [])

                print("[Research] Status:", status)
                print("[Research] Số evidence:", len(evidence))

                history.append({
                    "attempt": attempt,
                    "query": current_query,
                    "research_status": status,
                    "evidence_count": len(evidence),
                })

                # Lỗi công cụ không đồng nghĩa với thiếu bằng chứng.
                if status == "error":
                    final_answer = self.answer_agent.answer(
                        user_query,
                        research_result
                    )
                    break

                # 2. Research Agent -> Evidence Checker
                evidence_check = self.evidence_checker.check(
                    user_query,
                    evidence
                )

                check_status = evidence_check["status"]
                reason = evidence_check["reason"]

                print(
                    "[Evidence Checker] Status:",
                    check_status
                )
                print(
                    "[Evidence Checker] Reason:",
                    reason
                )

                history[-1]["evidence_status"] = check_status
                history[-1]["evidence_reason"] = reason

                # 3. Đủ bằng chứng -> Answer Agent
                if check_status == "sufficient":
                    final_answer = self.answer_agent.answer(
                        user_query,
                        research_result
                    )
                    break

                # 4. Hết lượt tìm kiếm
                if attempt >= self.max_attempts:
                    if check_status == "partial":
                        # Chỉ trả lời phần được bằng chứng hỗ trợ.
                        final_answer = self.answer_agent.answer(
                            user_query,
                            research_result
                        )
                    else:
                        final_answer = (
                            "Tôi không biết câu trả lời vì "
                            "không tìm thấy thông tin phù hợp "
                            "trong tài liệu."
                        )
                    break

                # 5. Coordinator quyết định query cho lượt tiếp theo
                print(
                    "[Coordinator] Bằng chứng chưa đủ. "
                    "Đang tạo query mới..."
                )

                try:
                    new_query = self.coordinator.revise_query(
                        user_query=user_query,
                        current_query=current_query,
                        evidence_reason=reason,
                        attempt=attempt + 1,
                    )
                except Exception as exc:
                    import traceback

                    print("[Coordinator] Không tạo được query mới.")
                    print(f"[ERROR] {type(exc).__name__}: {exc}")
                    traceback.print_exc()

                    if check_status == "partial":
                        final_answer = self.answer_agent.answer(
                            user_query,
                            research_result
                        )
                    else:
                        final_answer = (
                            "Tôi chưa tìm thấy đủ bằng chứng "
                            "trong tài liệu để trả lời câu hỏi."
                        )
                    break

                if new_query.casefold() == current_query.casefold():
                    print(
                        "[Coordinator] Query không thay đổi. "
                        "Dừng để tránh tìm kiếm lặp lại."
                    )

                    if check_status == "partial":
                        final_answer = self.answer_agent.answer(
                            user_query,
                            research_result
                        )
                    else:
                        final_answer = (
                            "Tôi chưa tìm thấy đủ bằng chứng "
                            "trong tài liệu để trả lời câu hỏi."
                        )
                    break

                current_query = new_query
                print("[Coordinator] Query mới:", current_query)

        else:
            raise ValueError(
                f"Intent không hợp lệ: {decision['intent']}"
            )

        return {
            "question": user_query,
            "intent": decision["intent"],
            "research_result": research_result,
            "evidence": (
                research_result.get("evidence", [])
                if research_result else []
            ),
            "evidence_check": evidence_check,
            "history": history,
            "answer": final_answer,
        }



async def main():
    system = MultiAgentSystem(max_attempts=3)

    while True:
        try:
            user_query = input(
                "\nNhập câu hỏi (gõ exit để thoát): "
            ).strip()

            if user_query.casefold() == "exit":
                print("Đã thoát Student Second Brain.")
                break

            if not user_query:
                print("Vui lòng nhập câu hỏi.")
                continue

            result = await system.run(user_query)

            print("\n" + "=" * 60)
            print("FINAL ANSWER")
            print("=" * 60)
            print(result["answer"])

        except KeyboardInterrupt:
            print("\nĐã dừng chương trình.")
            break

        except Exception as exc:
            print(
                f"\n[ERROR] Không thể xử lý câu hỏi: {exc}"
            )


if __name__ == "__main__":
    asyncio.run(main())
