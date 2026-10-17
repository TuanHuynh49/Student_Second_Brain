
import asyncio

from src.multi_agent.research_agent import ResearchAgent


async def main():
    agent = ResearchAgent()

    while True:
        query = input("\nNhập nội dung cần tìm (exit để thoát): ")

        if query.strip().lower() == "exit":
            break

        try:
            result = await agent.research(query)

            print("\n--- RESEARCH RESULT ---")
            print("Task:", result["task"])
            print("Query:", result["query"])
            print("Status:", result["status"])

            for i, item in enumerate(result["evidence"], start=1):
                print(f"\nEvidence {i}:")
                print(item)

        except Exception as error:
            print("Đã xảy ra lỗi:", error)


if __name__ == "__main__":
    asyncio.run(main())
