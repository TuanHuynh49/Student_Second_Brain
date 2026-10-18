# Bản khai báo sử dụng trí tuệ nhân tạo (Consolidated AI Usage Declaration)

> **Môn học**: AI Programming with Python (AIPR) - HCMUTE  
> **Đề tài**: Student Second Brain (Autonomous Agent + Hybrid RAG + MCP)  
> **Giảng viên phụ trách**: ThS. Nguyễn Đăng Quang  
> **Nhóm thực hiện**: 
> - **Trần Lê Dũng** (MSSV: 24110084) — Vai trò A: Dữ liệu, Ingestion, Chunking, Embedding, VectorStore & Retrieval
> - **Huỳnh Lê Anh Tuấn** (MSSV: 24110143) — Vai trò B: Agent ReAct Loop, Memory, CLI Gateway, Testset & Báo cáo
> - **Lê Khánh Duy** (MSSV: 24110082) — Vai trò C: Máy chủ MCP Server (stdio), Tool System & Phân hệ Multi-Agent

---

## 1. Tuyên bố về liêm chính học thuật (Academic Integrity Commitment)

Nhóm cam kết tuân thủ nghiêm ngặt các quy định về liêm chính học thuật của môn học AIPR:
* Trí tuệ nhân tạo (AI) được sử dụng với vai trò là công cụ hỗ trợ: trợ lý lập trình cặp (pair programming), gợi ý hướng đi khi gặp bế tắc kỹ thuật, cố vấn phản biện kiến trúc (advisory review), rà soát lỗi cú pháp và hỗ trợ định hình văn phong báo cáo.
* Toàn bộ mã nguồn, sơ đồ kiến trúc, dữ liệu đánh giá và nội dung báo cáo đều do các thành viên trong nhóm trực tiếp kiểm thử, hiểu rõ bản chất kỹ thuật, làm chủ 100% từng dòng mã và chịu trách nhiệm khi vấn đáp trực tiếp với giảng viên.

---

## 2. Danh mục công cụ AI được các thành viên sử dụng

| Thành viên | Công cụ / Nền tảng | Mô hình (Model) | Đơn vị cung cấp | Mục đích chính |
| :--- | :--- | :--- | :--- | :--- |
| **Trần Lê Dũng** (Vai trò A) | **Claude** (Web / Chat) | `claude-3-5-sonnet` | Anthropic | Tham khảo thiết kế schema dataclass, review logic chunking đệ quy, gợi ý cấu trúc lưu trữ `DocumentStore`/`VectorStore`. |
| **Huỳnh Lê Anh Tuấn** (Vai trò B) | **Google Antigravity IDE** | Gemini 2.5 Pro / Claude 3.5 Sonnet | Google DeepMind / Anthropic | Phân tích xung đột Git merge, sinh dữ liệu học tập mẫu (`DOC0004`–`DOC0008`), thiết lập bộ `testset.jsonl`, và tối ưu layout báo cáo. |
| **Lê Khánh Duy** (Vai trò C) | **AI Assistant** / OpenAI API | `gpt-4o` / `gpt-4o-mini` | OpenAI | Hỗ trợ cấu trúc giao thức truyền thông Stdio cho MCP Server, hoàn thiện bộ nạp file đa định dạng (`.md`, `.txt`) và điều phối Multi-Agent. |
| **Cả nhóm (Vận hành)** | **OpenAI API Client** | `gpt-4o-mini` / `gpt-oss-120b` | OpenAI | Đóng vai trò là LLM backend suy luận thực tế trong các vòng lặp ReAct, Coordinator, Evidence Checker và Answer Agent. |

---

## 3. Nhật ký và bảng kê chi tiết theo từng thành viên

### 3.1. Thành viên A: Trần Lê Dũng (Dữ liệu, RAG & VectorStore)

* **Phương châm sử dụng**: Ban đầu dùng AI tham khảo ý tưởng và code mẫu. Từ ngày 13/10 chuyển hẳn AI sang vai trò **cố vấn (mentor)**: chỉ chia bài toán thành bước, đặt câu hỏi gợi mở, không nhận code sẵn; tự tay code và gửi lại để AI review tìm lỗ hổng.
* **Chi tiết các hạng mục**:

| STT | Thời gian | Hạng mục công việc | Mô tả hỗ trợ từ AI | Can thiệp và kiểm chứng của sinh viên (Human-in-the-loop) |
| :---: | :---: | :--- | :--- | :--- |
| 1 | 12/10 | Phân chia công việc & lộ trình | AI đề xuất phân chia thư mục theo vai A-B-C và lộ trình 3 ngày. | Nhóm thảo luận, thống nhất điều chỉnh và Dũng nhận toàn bộ vai trò A. |
| 2 | 13/10 | Thiết kế Model & Dataclass | Tham khảo tài liệu thiết kế `Document`, AI chỉ ra lỗi thứ tự trường dataclass và đề xuất `ParentChunk`, `ChildChunk`. | Tự tay điều chỉnh lại các trường metadata (`doc_id`, `source`, `subject`) cho phù hợp bài toán RAG môn học. |
| 3 | 13/10 | Khởi tạo Chunking | AI viết mẫu loader và chunker 2 tầng tham khảo. | Tự lập trình lại hoàn toàn thành module chuẩn `Chunking_helper.py` (Structure Chunking cho `.md`, Recursive cho `.txt`). |
| 4 | 14/10–15/10 | Thiết kế Store & Retrieval | AI giải thích cơ chế truy xuất từ chunk con ánh xạ lên chunk cha; so sánh kế thừa vs composition giữa `VectorStore` và `DocumentStore`. | Tự thiết kế lại cấu trúc Dictionary trong RAM, giữ `VectorStore` kế thừa `DocumentStore` và hiện thực Cosine Similarity. |
| 5 | 15/10–16/10 | Review code & Reranker | Gửi `Chunking_helper.py`, `VectorStore.py`, module BM25 và Cross-Encoder nhờ AI rà soát lỗi tiềm ẩn. | Đọc danh sách cảnh báo của AI, tự debug và sửa lại các hàm tìm kiếm ngưỡng điểm (`score_threshold`). |
| 6 | 17/10 | Nghiên cứu đánh giá RAG | Nhờ AI giảng giải các chỉ số đánh giá RAG (Faithfulness, Answer Relevance, Context Precision). | Tự tiếp thu kiến thức và áp dụng vào bảng so sánh Dense vs Hybrid trong báo cáo. |

---

### 3.2. Thành viên B: Huỳnh Lê Anh Tuấn (Agent Core, CLI & Tích hợp)

* **Phương châm sử dụng**: Sử dụng môi trường agentic IDE để lập trình cặp (pair programming), hỗ trợ kiểm soát tính nhất quán giữa các branch Git, thiết lập dữ liệu kiểm thử chuẩn hóa và biên tập báo cáo học thuật.
* **Chi tiết các hạng mục**:

| STT | Thời gian | Hạng mục công việc | Mô tả hỗ trợ từ AI | Can thiệp và kiểm chứng của sinh viên (Human-in-the-loop) |
| :---: | :---: | :--- | :--- | :--- |
| 1 | 14/10 | Thiết kế ReAct Loop & Memory | Tham khảo cơ chế dừng an toàn `MAX_STEPS = 5` và cấu trúc bộ nhớ trượt Sliding Window ($K = 6$). | Trực tiếp lập trình `src/agent/Loop.py`, `Memory.py` và viết prompt `agent_react.txt` bằng tiếng Việt. |
| 2 | 14/10 | **Sinh mã module bóc tách cú pháp (`src/agent/Parser.py`)** | **AI sinh toàn bộ mã nguồn** cho file `Parser.py`, bao gồm hàm `safe_extract_json()` bóc tách Markdown JSON và tự động sửa dấu nháy đơn (`'`) thành nháy kép (`"`), cùng hàm `parse_react_response()` dùng regex bắt `Action:`, `Action Input:`, `Final Answer:`. | Sinh viên trực tiếp chạy 3 bộ unit test ở cuối file (`mock_llm_output_1`, `2`, `3`), kiểm thử các trường hợp thiếu dấu ngoặc hoặc chuỗi bọc Markdown để đảm bảo Agent Loop không bị crash khi LLM trả về định dạng sai. |
| 3 | 16/10 | Giải quyết xung đột Git Merge | AI phân tích đồ thị xung đột khi gộp branch `develop` (chứa multi-agent của Duy) vào branch `Tuan` (chứa main.py và ReAct). | Thực hiện an toàn lệnh Git, bảo toàn nguyên vẹn `main.py` và tiếp nhận thư mục `src/multi_agent/` sạch sẽ. |
| 4 | 16/10 | Xây dựng 5 tài liệu bài giảng mới | Hỗ trợ soạn thảo nội dung kỹ thuật cho `DOC0004.md` đến `DOC0008.md` (Hệ điều hành, Mạng máy tính, CSDL, Python nâng cao, MCP). | Rà soát kiến thức lý thuyết, bổ sung tiêu đề chuẩn và siêu dữ liệu (metadata) theo đúng yêu cầu đề tài. |
| 5 | 17/10 | Biên soạn bộ câu hỏi `testset.jsonl` | Gợi ý 36 câu hỏi bao phủ 8 tài liệu, phân bổ $\ge 4$ câu `no_answer = true` trên mỗi 12 câu để kiểm tra độ kháng ảo giác. | Đối chiếu từng câu hỏi với bài giảng, tinh chỉnh đáp án kỳ vọng (`expected_answer`) và chạy kiểm thử đo lường Token USAGE. |
| 6 | 17/10–18/10 | Soạn thảo và tối ưu Báo cáo | Hỗ trợ cấu trúc dàn ý Word, thiết kế sơ đồ Mermaid 3 ranh giới cân đối khối vuông và chuẩn hóa văn phong tiếng Anh. | Kiểm tra lại toàn bộ commit hash thực tế của 3 thành viên, số liệu đo lường thực nghiệm và đóng gói phụ lục. |
| 7 | 18/10 | **Xây dựng bộ công cụ xuất CSV và biểu đồ (`src/evaluation/export_benchmark.py`)** | Hỗ trợ thiết kế logic đọc động từ file log `.jsonl`, tính toán chi phí theo công thức `.env` (`$2/$10`), và dùng `matplotlib` vẽ biểu đồ cột chồng 300 DPI với nhãn số liệu và đường nét đứt mức trung bình. | Rà soát và tinh giản cấu trúc chỉ còn 3 hàm dễ hiểu, kiểm tra file CSV xuất ra khớp với dữ liệu chạy thực nghiệm và bảo đảm logic mạch lạc, tự tin giải thích khi vấn đáp với giảng viên. |

---

### 3.3. Thành viên C: Lê Khánh Duy (MCP Server & Multi-Agent System)

* **Phương châm sử dụng**: Sử dụng AI để hỗ trợ tra cứu tài liệu đặc tả của giao thức Model Context Protocol (MCP), chuẩn hóa schema giao tiếp Stdio IPC và phối hợp luồng tác tử cộng tác.
* **Chi tiết các hạng mục**:

| STT | Thời gian | Hạng mục công việc | Mô tả hỗ trợ từ AI | Can thiệp và kiểm chứng của sinh viên (Human-in-the-loop) |
| :---: | :---: | :--- | :--- | :--- |
| 1 | 13/10–14/10 | Khởi tạo MCP Server (`server.py`) | Hỗ trợ tra cứu tài liệu SDK `mcp`, cấu hình kênh truyền `stdio` và tách biệt luồng stdout (dành riêng cho JSON-RPC) và stderr (dành cho log). | Lập trình máy chủ MCP độc lập, hiện thực hóa các tool chuẩn: `search`, `get`, `update`. |
| 2 | 15/10 | Cơ chế an toàn Atomic Rollback | Tham khảo phương án sao lưu dữ liệu nguyên tử khi thao tác ghi đè file gặp sự cố. | Tự viết khối `try...except` sao lưu `old_content`, tự động khôi phục nội dung file gốc nếu bước tái lập VectorStore thất bại. |
| 3 | 16/10 | Mô-đun Tool Adapter | Hỗ trợ thuật toán chuyển đổi JSON Schema của MCP sang định dạng Function Calling của OpenAI API. | Hiện thực module `src/mcp/tool_adapter.py`, viết hàm `discover_mcp_tools()` tự động khám phá tool động qua `client.list_tools()`. |
| 4 | 16/10–17/10 | Phân hệ Multi-Agent | Hỗ trợ thiết kế cấu trúc phân vai 4 tác tử: `Coordinator`, `Researcher`, `EvidenceChecker`, `AnswerAgent`. | Trực tiếp hiện thực hóa chu trình tự sửa sai (Query Reformulation Loop) với `max_attempts = 3` trong `multi_agent.py`. |
| 5 | 18/10 | **Phát triển MCP Client thứ 2 độc lập (`src/mcp/mcp_client.py`)** | Hỗ trợ cấu hình StdioServerParameters kết nối subprocess tới `src.mcp.server`, xử lý truyền `PYTHONPATH` tránh lỗi `ModuleNotFoundError`, và hiện thực cơ chế nhập văn bản nhiều dòng (kết thúc bằng `END`) kèm tự động verify lại bằng lệnh `get`. | Trực tiếp chạy interactive test bằng tay trên terminal, kiểm thử cả 3 thao tác (`search`, `get`, `update`), phục hồi file an toàn khi test và xác minh tính tương thích độc lập giữa Client thứ 2 và Server theo chuẩn MCP. |

---

## 4. Các câu lệnh nhắc tiêu biểu (Key Sample Prompts)

### 4.1. Prompt tham khảo thiết kế Parent-Child Chunking (Thành viên A - Trần Lê Dũng)
```text
"Tôi đang thiết kế hệ thống RAG cho slide bài giảng IT. Bạn hãy đóng vai trò cố vấn kiến trúc, 
so sánh ưu nhược điểm của việc dùng 2 dataclass phẳng (ParentChunk và ChildChunk) so với 1 class đệ quy. 
Chỉ giải thích bản chất và đặt câu hỏi gợi mở, không viết sẵn code hoàn chỉnh vì tôi muốn tự lập trình."
```

### 4.2. Prompt của Thành viên B (Huỳnh Lê Anh Tuấn)
* **Prompt sinh mã `src/agent/Parser.py`**:
```text
"Hãy viết giúp tôi module src/agent/Parser.py bằng Python sử dụng thư viện re (regex) và json. 
Hàm 1: safe_extract_json(text) bóc tách chuỗi JSON nằm trong block markdown ```json...``` hoặc chuỗi thô {...}, 
nếu lỗi JSONDecodeError thì tự động thay thế nháy đơn thành nháy kép để sửa lỗi. 
Hàm 2: parse_react_response(text) dùng regex bắt các thành phần Final answer:, Action:, Action Input: 
để trả về tuple (action_name, action_args, final_answer). Kèm theo 3 hàm mock test ở cuối file để kiểm thử."
```

* **Prompt thiết kế bộ câu hỏi testset**:
```text
"Tạo giúp tôi khung file tests/testset.jsonl gồm 36 câu hỏi JSON Lines bao phủ kiến thức DOC0001 đến DOC0008. 
Quy tắc bắt buộc: cứ mỗi 12 câu thì phải có ít nhất 4 câu no_answer=True (hỏi về những chủ đề hoàn toàn 
không có trong tài liệu môn học) để chúng tôi kiểm tra tính nghiêm ngặt của prompt chống ảo giác."
```

* **Prompt xây dựng công cụ xuất CSV và biểu đồ Token Usage (`src/evaluation/export_benchmark.py`)**:
```text
"Hãy viết giúp tôi một script Python đơn giản (src/evaluation/export_benchmark.py) để:
1. Đọc động file log .jsonl từ thư mục logs/, trích xuất câu hỏi và token tiêu thụ từng câu.
2. Xuất bảng chi tiết ra logs/eval_benchmark_detail.csv kèm theo tính chi phí dựa trên đơn giá .env ($2/$10 mỗi triệu tokens) và dòng Average ở cuối.
3. Dùng matplotlib vẽ biểu đồ cột chồng (Prompt Tokens và Completion Tokens) 300 DPI lưu vào logs/chart_token_usage.png có hiển thị số token trên đầu mỗi cột và đường nét đứt mức trung bình."
```

### 4.3. Prompt của Thành viên C (Lê Khánh Duy)
* **Prompt hỗ trợ giao thức MCP Stdio**:
```text
"Trong Python MCP SDK, làm thế nào để cấu hình server chạy qua stdio transport mà đảm bảo stdout hoàn toàn 
sạch (chỉ chứa bản tin JSON-RPC hợp lệ), còn toàn bộ thông tin log/debug phải chuyển hướng sang stderr 
để không làm gãy kết nối với client?"
```

* **Prompt phát triển ứng dụng MCP Client thứ 2 độc lập (`src/mcp/mcp_client.py`)**:
```text
"Hãy viết một ứng dụng Python Client độc lập (src/mcp/mcp_client.py) kết nối tới MCP Server qua stdio transport. 
Yêu cầu: 
1. Tự động khám phá công cụ động qua list_tools(). 
2. Cung cấp menu console trực quan cho người dùng chọn gọi search, get, hoặc update. 
3. Ở chức năng update, cho phép nhập văn bản nhiều dòng và kết thúc bằng từ khóa END trên một dòng mới. Sau khi update xong, tự động gọi get để kiểm chứng lại nội dung đã lưu trên đĩa."
```

---

## 5. Tự đánh giá tác động và bài học kinh nghiệm của nhóm

1. **Hiệu quả tích cực**: AI giúp nhóm tăng tốc quá trình học các công nghệ mới (giao thức MCP, chuẩn parent-child RRF), hỗ trợ giải quyết nhanh các lỗi xung đột branch Git phức tạp, và nâng cao độ chuyên nghiệp của báo cáo kỹ thuật.
2. **Kiểm soát rủi ro**: Nhóm luôn duy trì nguyên tắc **Human-in-the-loop**:
   - Không sao chép mù quáng: Mọi gợi ý đều được đọc hiểu, thử nghiệm cục bộ và chỉnh sửa phù hợp với kiến trúc dự án.
   - Kiểm tra chéo (Cross-verification): Các thành viên thường xuyên review code của nhau để đảm bảo từng người đều hiểu tường tận luồng chạy của toàn hệ thống trước khi bước vào buổi bảo vệ vấn đáp.
