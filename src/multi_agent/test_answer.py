
from src.multi_agent.answer_agent import AnswerAgent


def main():
    agent = AnswerAgent()

    # Dữ liệu giả lập kết quả từ Research Agent
    research_result = {
        "task": "search_documents",
        "query": "MCP là gì?",
        "evidence": [
            """
            MCP (Model Context Protocol) là một giao thức
            cho phép ứng dụng AI kết nối với các công cụ
            và nguồn dữ liệu bên ngoài thông qua một
            giao diện thống nhất.
            """
        ],
        "status": "success"
    }

    question = "MCP là gì và nó có tác dụng gì?"

    try:
        answer = agent.answer(question, research_result)

        print("\n--- ANSWER AGENT RESULT ---")
        print(answer)

    except Exception as error:
        print("Đã xảy ra lỗi:", error)


if __name__ == "__main__":
    main()
