
from src.multi_agent.coordinator_agent import CoordinatorAgent


def main():
    coordinator = CoordinatorAgent()

    while True:
        question = input("\nNhập câu hỏi (gõ exit để thoát): ")

        if question.strip().lower() == "exit":
            break

        try:
            result = coordinator.decide(question)

            print("\n--- COORDINATOR RESULT ---")
            print("Intent:", result["intent"])
            print("Reason:", result["reason"])
            print("Query:", result["query"])

        except Exception as error:
            print("Đã xảy ra lỗi:", error)


if __name__ == "__main__":
    main()
