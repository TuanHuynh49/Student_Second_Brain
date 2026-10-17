
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
        """Phân tích câu hỏi và quyết định cách tra cứu tài liệu."""

        if not user_query or not user_query.strip():
            raise ValueError("Câu hỏi không được để trống.")

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": """
Bạn là Coordinator Agent của Student Second Brain.

Nhiệm vụ:
Phân loại yêu cầu của người dùng thành chính xác một intent để quyết định hệ thống nào sẽ xử lý yêu cầu đó.

Các intent:

1. `search_documents`
   Sử dụng khi câu hỏi cần tìm kiếm tài liệu học tập, tra cứu thông tin trong tài liệu, giải thích khái niệm dựa trên tài liệu hoặc tóm tắt các phần tài liệu liên quan.

2. `react_tools`
   Sử dụng khi yêu cầu cần thực hiện thao tác thông qua công cụ, chẳng hạn như đọc toàn bộ tài liệu theo ID, cập nhật nội dung tài liệu hoặc thực hiện một tác vụ gồm nhiều bước sử dụng công cụ.

3. `general_question`
   Sử dụng cho lời chào, lời cảm ơn và các cuộc hội thoại đơn giản không cần tìm kiếm tài liệu hoặc sử dụng công cụ.

Quy tắc:
- Chỉ chọn đúng một intent trong ba intent trên.
- Dựa vào mục đích thực sự của yêu cầu để phân loại.
- Không tự ý trả lời câu hỏi của người dùng.
- Không thực hiện công cụ trong bước phân loại.
- Trường `query` phải chứa câu truy vấn phù hợp để xử lý yêu cầu. Với `search_documents`, tạo query phục vụ tìm kiếm tài liệu. Với hai intent còn lại, giữ nội dung yêu cầu gốc hoặc tạo query phù hợp với yêu cầu.
- Chỉ trả về JSON hợp lệ theo cấu trúc:

{"intent": "search_documents", 
"reason": "Giải thích ngắn gọn lý do phân loại", 
"query": "Nội dung truy vấn"}
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

        allowed_intents = {
            "search_documents",
            "react_tools",
            "general_question",
        }

        if result.get("intent") not in allowed_intents:
            raise ValueError("Coordinator trả về intent không hợp lệ.")

        if not isinstance(result.get("reason"), str):
            raise ValueError("Trường reason không hợp lệ.")

        if not isinstance(result.get("query"), str):
            raise ValueError("Trường query không hợp lệ.")

        # Nếu cần tra cứu mà query rỗng, dùng câu hỏi ban đầu.
        if result["intent"] == "search_documents":
            if not result["query"].strip():
                result["query"] = user_query.strip()

        return result
    
    def revise_query(
        self,
        user_query: str,
        current_query: str,
        evidence_reason: str,
        attempt: int
    ) -> str:
        """Tạo query tìm kiếm mới dựa trên bằng chứng chưa đủ."""

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": """
Bạn là Coordinator Agent của Student Second Brain.

Nhiệm vụ:
Tạo một query mới để Research Agent tìm tài liệu tốt hơn
khi Evidence Checker đánh giá bằng chứng chưa đủ.

Quy tắc:
- Giữ nguyên ý nghĩa câu hỏi gốc.
- Dựa vào lý do Evidence Checker đưa ra.
- Thử cách diễn đạt hoặc từ khóa khác.
- Không trả lời câu hỏi.
- Không sử dụng kiến thức bên ngoài để tự bổ sung thông tin.
- Chỉ trả về JSON hợp lệ theo cấu trúc:
{"query": "query tìm kiếm mới"}
"""
                },
                {
                    "role": "user",
                    "content": (
                        f"Câu hỏi gốc: {user_query}\n"
                        f"Query hiện tại: {current_query}\n"
                        f"Lý do bằng chứng chưa đủ: {evidence_reason}\n"
                        f"Lượt tìm kiếm tiếp theo: {attempt}"
                    )
                }
            ],
            response_format={"type": "json_object"},
            temperature=0
        )

        content = response.choices[0].message.content

        if not content:
            raise ValueError(
                "Coordinator không tạo được query mới."
            )

        import json

        result = json.loads(content)
        new_query = result.get("query")

        if not isinstance(new_query, str) or not new_query.strip():
            raise ValueError("Query mới không hợp lệ.")

        # Tránh lặp lại query cũ.
        if new_query.strip().casefold() == current_query.strip().casefold():
            return user_query.strip()

        return new_query.strip()

