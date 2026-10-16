
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


# 1. Đọc cấu hình từ file .env
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

# Hỗ trợ cả hai cách đặt tên biến API key
api_key = (
    os.getenv("OPENAI_API_KEY")
)

model = os.getenv("OPENAI_MODEL", "gpt-oss-120b-medium")

if not api_key:
    raise ValueError(
        "Không tìm thấy OPENAI_API_KEY hoặc OPEN_API_KEY trong file .env"
    )

client = OpenAI(api_key=api_key)


class CoordinatorAgent:
    def __init__(self):
        self.name = "Coordinator Agent"

    def decide(self, user_query: str) -> dict:
        """
        Phân tích câu hỏi và quyết định bước xử lý tiếp theo.
        """

        if not user_query.strip():
            raise ValueError("Câu hỏi không được để trống.")

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": """
Bạn là Coordinator Agent của hệ thống Student Second Brain.

Nhiệm vụ:
1. Phân tích yêu cầu của người dùng.
2. Quyết định yêu cầu có cần tìm tài liệu trong hệ thống hay không.
3. Trả kết quả dưới dạng JSON.

Chỉ được chọn một trong hai intent:
- search_documents: cần tìm kiếm tài liệu trong hệ thống.
- general_question: câu hỏi thông thường, không cần tìm tài liệu.

Quy tắc phân loại:
- search_documents: Khi câu hỏi có thể được trả lời bằng tài liệu
  nội bộ, bao gồm câu hỏi về danh sách, thông tin, tóm tắt,
  địa điểm, thành phố hoặc nội dung có thể có trong tài liệu.
- general_question: Chỉ dùng khi câu hỏi rõ ràng không cần
  tra cứu tài liệu nội bộ.

Ví dụ:
- "danh sách các hãng hàng không" -> search_documents

JSON phải có đúng ba trường:
{
  "intent": "search_documents hoặc general_question",
  "reason": "Lý do quyết định",
  "query": "Nội dung truy vấn"
}
"""
                },
                {
                    "role": "user",
                    "content": user_query
                }
            ],
            response_format={"type": "json_object"},
            temperature=0
        )

        content = response.choices[0].message.content

        if not content:
            raise ValueError("Coordinator không trả về kết quả.")

        result = json.loads(content)

        # Kiểm tra kết quả trước khi chuyển cho agent khác
        allowed_intents = {
            "search_documents",
            "general_question"
        }

        if result.get("intent") not in allowed_intents:
            raise ValueError("Coordinator trả về intent không hợp lệ.")

        if not isinstance(result.get("reason"), str):
            raise ValueError("Trường reason không hợp lệ.")

        if not isinstance(result.get("query"), str):
            raise ValueError("Trường query không hợp lệ.")

        return result
