import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

from src.models.Schemas import Tool
from src.agent.Memory import SlidingWindowMemory
from src.agent.Loop import run_agent
from src.LLM.Client import USAGE, reset_usage 

from src.mcp.server import search, get, update

TOOLS = [
    Tool(
        name="search",
        description="Tìm kiếm tài liệu học tập, bài giảng trong kho tri thức theo nội dung ngữ nghĩa.",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Nội dung cần tìm kiếm"
                },
                "top_k": {
                    "type": "integer",
                    "description": "Số lượng đoạn văn cần lấy (mặc định 3)"
                }
            },
            "required": ["query"]
        },
        fn=search
    ),
    Tool(
        name="get",
        description="Đọc toàn bộ nội dung chi tiết của một tài liệu dựa theo mã doc_id (ví dụ: DOC0001, test).",
        parameters={
            "type": "object",
            "properties": {
                "doc_id": {
                    "type": "string",
                    "description": "Mã định dah của tài liệu"
                }
            },
            "required": ["doc_id"]
        },
        fn=get
    ),
    Tool(
        name="update",
        description="Cập nhật tiêu đề và nội dung mới cho tài liệu đã có, đồng thời tự động lập lại chỉ mục tìm kiếm.",
        parameters={
            "type": "object",
            "properties": {
                "doc_id": {
                    "type": "string",
                    "description": "Mã tài liệu cần sửa"
                },
                "content": {
                    "type": "string",
                    "description": "Nội dung mới của tài liệu"
                }
            },
            "required": ["doc_id", "title", "content"]
        },
        fn=update
    )
]

def main():
    print("=" * 65)
    print("🎓 CHÀO MỪNG BẠN ĐẾN VỚI HỆ THỐNG STUDENT SECOND BRAIN 🎓")
    print("   (Hệ thống tích hợp: RAG Ingestion + MCP Tools + ReAct Agent)")
    print("=" * 65)
    print("💡 Mẹo thử nghiệm:")
    print("   - Tra cứu: 'RAG là gì và hoạt động như thế nào?'")
    print("   - Đọc tài liệu: 'Đọc chi tiết tài liệu DOC0001'")
    print("   - Sửa & Xác minh: 'Cập nhật tài liệu test với nội dung ôn thi AIPR'")
    print("   - Gõ 'exit' hoặc 'quit' để thoát chương trình.\n")


    session_memory = SlidingWindowMemory(max_messages=5)
    reset_usage()

    while True:
        try:
            user_input = input("👤 Sinh viên: ").strip()
            if not user_input:
                continue
            if user_input.lower() in {"exit", "quit"}:
                print("\n Bye Bye Bye 👋")
                print(f"📊 Token usage: {USAGE}")
                break

            print ("\n🤖 Second Brain đang suy nghĩ...")
            answer = run_agent(
                user_task=user_input,
                tools=TOOLS,
                memory=session_memory,
            )

            print(f"\n🧠 Phản hồi:\n{answer}\n")
            print("-" * 65)

        except KeyboardInterrupt:
            print("\n Đã dừng chương trình.")
            break
        except Exception as e:
            print(f"/n Ohnooooooooooooooooooooooooooooooo lỗi r: {e}\n")


if __name__ == "__main__":
    main()
         