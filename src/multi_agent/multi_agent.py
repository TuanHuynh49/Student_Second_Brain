
import asyncio

from src.multi_agent.coordinator_agent import CoordinatorAgent
from src.multi_agent.research_agent import ResearchAgent
from src.multi_agent.answer_agent import AnswerAgent


class MultiAgentSystem:
    def __init__(self):
        self.coordinator = CoordinatorAgent()
        self.researcher = ResearchAgent()
        self.answer_agent = AnswerAgent()

    async def run(self, user_query: str) -> dict:
        if not user_query.strip():
            raise ValueError("Câu hỏi không được để trống.")

        # Bước 1: Coordinator quyết định hướng xử lý
        decision = self.coordinator.decide(user_query)

        print("\n[Coordinator] Intent:", decision["intent"])
        print("[Coordinator] Reason:", decision["reason"])

        # Bước 2: Chọn nhánh xử lý bằng code
        if decision["intent"] == "search_documents":
            print("\n[Research] Đang tìm tài liệu...")

            research_result = await self.researcher.research(
                decision["query"]
            )
            print("\n========== DEBUG RESEARCH ==========")
            print("Query:", research_result.get("query"))
            print("Status:", research_result.get("status"))
            print("Số lượng evidence:", len(research_result.get("evidence", [])))

            for i, item in enumerate(research_result.get("evidence", []), start=1):
                print(f"\n--- Evidence {i} ---")
                print(item)

            print("====================================\n")

            print("[Research] Status:", research_result["status"])

            # Bước 3: Answer dựa trên kết quả nghiên cứu
            final_answer = self.answer_agent.answer(
                user_query,
                research_result
            )

        elif decision["intent"] == "general_question":
            print("\n[Pipeline] Không cần tìm tài liệu.")

            research_result = None

            final_answer = self.answer_agent.answer(user_query)

        else:
            raise ValueError(
                f"Intent không được hỗ trợ: {decision['intent']}"
            )

        return {
            "question": user_query,
            "intent": decision["intent"],
            "research_result": research_result,
            "answer": final_answer
        }


async def main():
    system = MultiAgentSystem()

    while True:
        question = input(
            "\nNhập câu hỏi (gõ exit để thoát): "
        )

        if question.strip().lower() == "exit":
            break

        try:
            result = await system.run(question)

            print("\n" + "=" * 60)
            print("FINAL ANSWER")
            print("=" * 60)
            print(result["answer"])

        except Exception as error:
            print("\nĐã xảy ra lỗi:", error)


if __name__ == "__main__":
    asyncio.run(main())
