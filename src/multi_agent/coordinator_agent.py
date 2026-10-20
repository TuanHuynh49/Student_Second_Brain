
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from src.LLM.Client import call_llm

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


class CoordinatorAgent:
    def __init__(self):
        self.name = "Coordinator Agent"

    def decide(self, user_query: str) -> dict:
        """Phân tích câu hỏi và quyết định cách tra cứu tài liệu."""

        if not user_query or not user_query.strip():
            raise ValueError("Câu hỏi không được để trống.")

        message = call_llm([
                {
                    "role": "system",
                    "content": """
Bạn là Coordinator Agent của Student Second Brain.

Nhiệm vụ:
Phân loại yêu cầu của người dùng thành chính xác một intent để quyết định hệ thống nào sẽ xử lý yêu cầu đó.

Các intent:

1. `search_documents`
   Sử dụng cho MỌI câu hỏi tìm kiếm tài liệu, giải thích khái niệm học thuật, kỹ thuật, lý thuyết hay kiến thức chuyên môn (Python, AI, LLM, RAG, Chunking, Prompt, Tokens, Streaming, Embeddings, Agents, Database, Mạng máy tính, v.v.) hoặc các câu hỏi cần kiểm tra đối chiếu kiến thức. Khi người dùng hỏi bất kỳ câu hỏi nào về kiến thức, luôn ưu tiên chọn `search_documents`.

2. `react_tools`
   Sử dụng khi yêu cầu cần thực hiện thao tác tác động thông qua công cụ, chẳng hạn như đọc toàn bộ tài liệu theo ID cụ thể (ví dụ doc_DOC0001), cập nhật nội dung ghi chú/tài liệu, hoặc thực hiện một quy trình thao tác nhiều bước sử dụng công cụ.

3. `general_question`
   CHỈ sử dụng cho các tương tác chào hỏi xã giao thuần túy (ví dụ: 'xin chào', 'hello', 'bạn là ai', 'bạn có thể làm gì'), lời cảm ơn hoặc tạm biệt. TUYỆT ĐỐI KHÔNG chọn `general_question` cho các câu hỏi chứa nội dung học thuật, kiến thức hoặc câu hỏi thực chất.

Quy tắc:
- Chỉ chọn đúng một intent trong ba intent đã định nghĩa.
- Dựa vào mục đích thực sự của yêu cầu để phân loại.
- Không tự ý trả lời câu hỏi của người dùng.
- Không thực hiện công cụ trong bước phân loại.
- Trường `query` phải chứa câu truy vấn phù hợp để xử lý yêu cầu. Với `search_documents`, tạo query phục vụ tìm kiếm tài liệu. Với hai intent còn lại, giữ nội dung yêu cầu gốc hoặc tạo query phù hợp với yêu cầu.
- Với intent `search_documents`, trích xuất các điều kiện metadata mà người dùng nêu rõ trong câu hỏi.
- Các trường metadata được hỗ trợ gồm `course`, `doc_id` và `source`.
- Chỉ trích xuất giá trị được người dùng nêu rõ. Không tự suy đoán hoặc tự đặt giá trị metadata.
- Chỉ đưa vào `metadata_filter` những trường metadata có điều kiện cụ thể. Nếu người dùng không nêu điều kiện metadata nào, trả về `{}`.
- `metadata_filter` phải là JSON object hợp lệ.
- Với intent `react_tools` hoặc `general_question`, đặt `metadata_filter` là `{}`.
- Chỉ trả về JSON hợp lệ, không thêm Markdown, lời giải thích hoặc văn bản bên ngoài JSON.

Cấu trúc JSON đầu ra:

{
  "intent": "search_documents",
  "reason": "Giải thích ngắn gọn lý do phân loại",
  "query": "Nội dung truy vấn",
  "metadata_filter": {
    "course": "Tên course nếu người dùng nêu rõ",
    "doc_id": "ID tài liệu nếu người dùng nêu rõ",
    "source": "Nguồn tài liệu nếu người dùng nêu rõ"
  }
vô systemprompt của decide
"""
                },
                {
                    "role": "user",
                    "content": user_query
                }
            ],
        )

        content = message.content

        if not content:
            raise ValueError("Coordinator không trả về kết quả.")

        result = json.loads(content)

        metadata_filter = result.get("metadata_filter", {})

        if not isinstance(metadata_filter, dict):
            raise ValueError("Trường metadata_filter không hợp lệ.")

        result["metadata_filter"] = metadata_filter

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

        message = call_llm([
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
        )

        content = message.content

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

