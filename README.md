# Student Second Brain: Agentic RAG Study Assistant System

> **Đồ án môn học**: AI Programming with Python (AIPR) - Học kỳ 1, Năm học 2026–2026  
> **Khoa**: Công nghệ Thông tin - Trường Đại học Sư phạm Kỹ thuật TP.HCM (HCMUTE)  
> **Giảng viên hướng dẫn**: ThS. Nguyễn Đăng Quang  
> **Nhóm sinh viên thực hiện**:
> - **Trần Lê Dũng** (MSSV: 24110084) — *Data Ingestion, Parent-Child Chunking & VectorStore*
> - **Huỳnh Lê Anh Tuấn** (MSSV: 24110143) — *Agent ReAct Loop, Sliding Memory, CLI Gateway & Benchmark*
> - **Lê Khánh Duy** (MSSV: 24110082) — *MCP Server (stdio), Tool Contracts, Atomic Rollback & Multi-Agent*

---

## ⚡ HƯỚNG DẪN CHẠY DEMO NHANH (QUICK START)

Chỉ với **3 bước đơn giản** để khởi động và trải nghiệm toàn bộ hệ thống trên máy tính:

### Bước 1: Kích hoạt môi trường và cài đặt thư viện
Mở Terminal tại thư mục gốc `Student_Second_Brain`:

* **Cách 1: Dùng công cụ `uv` (Khuyến nghị - Nhanh nhất)**:
  ```bash
  uv venv
  uv pip install -r requirements.txt
  ```

* **Cách 2: Dùng Python chuẩn (Virtual Environment)**:
  ```bash
  # 1. Tạo môi trường ảo
  python -m venv .venv

  # 2. Kích hoạt môi trường:
  # Trên Windows PowerShell:
  .\.venv\Scripts\Activate.ps1
  # Trên Windows CMD:
  .\.venv\Scripts\activate.bat
  # Trên Linux / macOS:
  source .venv/bin/activate

  # 3. Cài đặt các thư viện phụ thuộc:
  pip install -r requirements.txt
  ```

---

### Bước 2: Thiết lập cấu hình biến môi trường (`.env`)

Sao chép tệp mẫu [.env.example](.env.example) thành `.env`:
```bash
# Trên Windows:
copy .env.example .env

# Trên Linux / macOS:
cp .env.example .env
```

Mở tệp `.env` vừa tạo và điền các khóa API của bạn:
```env
# 1. Cấu hình mô hình ngôn ngữ (OpenAI API hoặc Proxy tương thích)
OPENAI_API_KEY=sk-...                        # Điền khóa API của bạn
OPENAI_BASE_URL=https://api.openai.com/v1     # Hoặc proxy trường: https://nttcodex.com/v1
OPENAI_MODEL=gpt-4o-mini                    # Hoặc: gpt-6.1-sol
MODEL=gpt-4o-mini                           # Đồng bộ mô hình cho Client

# 2. Cấu hình kho tài liệu học tập
DOC_PATH=data/raw                           # Thư mục chứa bài giảng DOC0001 -> DOC0008

# 3. Cấu hình Dense Embedding
MODEL_EMBEDING=jina-embeddings-v3
JINA_API_KEY=jina_...                       # Điền khóa Jina API của bạn

# 4. Cấu hình Reranker & Đánh giá RAG
MODEL_RERANK=cross-encoder/ms-marco-MiniLM-L-6-v2
GROQ_API_KEY=gsk_...                        # Khóa Groq API (dùng cho run_tests)
```

---

### Bước 3: Khởi động chương trình chính

Chạy lệnh duy nhất để vào giao diện trợ lý học tập:
```bash
python main.py
```
*(Hoặc `uv run python main.py`)*

---

## 🎯 KỊCH BẢN DEMO THỰC TẾ (DEMO SHOWCASE)

Khi màn hình hiển thị dấu nhắc `Nhập câu hỏi (gõ exit để thoát):`, bạn có thể thử ngay 3 tình huống tiêu biểu tương ứng với 3 tầng năng lực của hệ thống:

### 1. Tình huống 1: Tra cứu RAG kết hợp đa tác tử (Multi-Agent Hybrid RAG)
* **Câu hỏi mẫu**:
  ```text
  Cơ chế bão hòa tần suất (saturation) và chuẩn hóa độ dài trong thuật toán BM25 có tác dụng gì?
  ```
* **Hiện tượng quan sát**:
  1. `Coordinator` phân loại intent `search_documents`.
  2. `Researcher` gọi công cụ MCP `search` (kết hợp Dense Cosine Similarity và BM25 từ khóa).
  3. `EvidenceChecker` thẩm định bằng chứng đạt yêu cầu (`sufficient`).
  4. `AnswerAgent` sinh câu trả lời kèm bảng trích dẫn nguồn (**SOURCES & EVIDENCE**) có Score, Doc ID (`DOC0001`).
  5. Bảng thống kê chi phí **Token USAGE & COST** được in rõ ràng.

### 2. Tình huống 2: Chống ảo giác - Từ chối khi ngoài tài liệu (Calibration / Anti-Hallucination)
* **Câu hỏi mẫu**:
  ```text
  Trình bày chi tiết công thức tính toán độ phức tạp của giải thuật Dijkstra trong không gian 4 chiều?
  ```
* **Hiện tượng quan sát**:
  1. Hệ thống tìm kiếm trong kho tài liệu nhưng không có bằng chứng liên quan.
  2. `EvidenceChecker` phát hiện bằng chứng không đầy đủ (`insufficient`).
  3. Hệ thống kiên quyết từ chối bịa đặt: *"Tôi không biết câu trả lời vì không tìm thấy thông tin phù hợp trong tài liệu."*

### 3. Tình huống 3: Hành động ReAct có đối soát (Side-Effect + Verification Protocol)
* **Câu lệnh mẫu**:
  ```text
  Cập nhật ghi chú về MCP vào doc_DOC0001 và kiểm tra lại
  ```
* **Hiện tượng quan sát**:
  1. `Coordinator` phân loại intent `react_tools`.
  2. ReAct Loop tự kích hoạt chuỗi hành động:
     - `Thought` $\rightarrow$ `Action: get[doc_DOC0001]` (đọc nội dung hiện tại).
     - `Thought` $\rightarrow$ `Action: update[doc_DOC0001, ...]` (cập nhật nội dung mới).
     - `Thought` $\rightarrow$ `Action: get[doc_DOC0001]` (**Bắt buộc gọi lại lệnh đọc để đối soát**).
  3. In thông báo xác nhận trạng thái tài liệu đã được sửa đổi an toàn.

*(Gõ `exit` để thoát khỏi hệ thống).*

---

## 📊 LỆNH CHẠY ĐÁNH GIÁ TỰ ĐỘNG (EVALUATION BENCHMARK)

Để kiểm thử độ chính xác trên toàn bộ **36 câu hỏi** trong [tests/testset.jsonl](tests/testset.jsonl) (gồm 12 câu ngoài phạm vi `no_answer = true`) và tự động xuất nhật ký JSONL:

```bash
python -m tests.run_tests
```

* **Kết quả đo lường**: Tỷ lệ trả lời chính xác, độ trung thực (Faithfulness), tỷ lệ nhận diện đúng câu hỏi không có đáp án, và tổng chi phí Token USAGE theo từng câu hỏi.
* **Tệp đầu ra**: Được lưu tự động vào thư mục `logs/run_*.jsonl`.

---

## 📁 CẤU TRÚC THƯ MỤC HỆ THỐNG

```text
Student_Second_Brain/
├── data/
│   └── raw/                    # 8 bài học gốc (DOC0001.txt -> DOC0008.md)
├── logs/                       # Nhật ký các phiên chạy thực nghiệm (.jsonl)
├── src/
│   ├── LLM/                    # Kết nối mô hình ngôn ngữ & đo lường Token USAGE
│   ├── agent/                  # Vòng lặp tự chủ ReAct Loop, Bộ nhớ trượt (Sliding Memory), Parser
│   ├── mcp/                    # MCP Server (stdio), Tool Adapter (Dynamic Discovery)
│   ├── multi_agent/            # Hệ thống đa tác tử (Coordinator, Researcher, Checker, Answer)
│   ├── prompts/                # Toàn văn System Prompts đã chuẩn hóa tiếng Việt
│   └── rag/                    # Đường ống Hybrid RAG, Parent-Child Chunking, BM25 & VectorStore
├── tests/
│   ├── testset.jsonl           # Bộ dữ liệu đánh giá 36 câu hỏi benchmark
│   └── run_tests.py            # Kịch bản tự động đo lường độ chính xác và chi phí
├── .env.example                # Bản mẫu cấu hình an toàn (không chứa key)
├── .gitignore                  # Cấu hình bảo mật, chặn tuyệt đối lộ file .env
├── ai-usage.md                 # Bản khai báo sử dụng AI của cả 3 thành viên
├── requirements.txt            # Danh sách thư viện phụ thuộc Python 3.11+
├── main.py                     # Điểm khởi chạy chính của hệ thống
└── README.md                   # Hướng dẫn cài đặt và vận hành
```

---

## 📋 DANH MỤC SẢN PHẨM NỘP BÀI (DELIVERABLES)

* [x] **`report.docx`**: Báo cáo kỹ thuật 8–9 trang kèm Phụ lục A (Prompt), Phụ lục B (Trace), Phụ lục C (`ai-usage.md`).
* [x] **Repo Code (.git)**: Thư mục mã nguồn lưu trữ đầy đủ commit history của cả 3 thành viên (`401546a` Dũng, `3e9e5bf` Tuấn, `7ffd454` Duy).
* [x] **`logs/`**: Thư mục chứa $\ge 3$ phiên chạy thực tế có timestamp và bảng USAGE token.
* [x] **`tests/testset.jsonl`**: Bộ kiểm thử gồm 36 câu hỏi (với 12 câu `no_answer = true`).
* [x] **`ai-usage.md`**: Bản tuyên bố liêm chính học thuật hợp nhất.
* [x] **`README.md`**: Hướng dẫn 1 lệnh khởi chạy và tái lập toàn bộ đồ án.