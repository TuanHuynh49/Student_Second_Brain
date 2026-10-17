# Student Second Brain: Agentic RAG Study Assistant System

> **Đồ án môn học**: AI Programming with Python (AIPR) - Học kỳ 1, Năm học 2026–2026  
> **Khoa**: Công nghệ Thông tin - Trường Đại học Sư phạm Kỹ thuật TP.HCM (HCMUTE)  
> **Giảng viên hướng dẫn**: ThS. Nguyễn Đăng Quang  
> **Nhóm sinh viên thực hiện**:
> - **Trần Lê Dũng** (MSSV: 24110084) — *Data, Ingestion, Parent-Child Chunking & VectorStore*
> - **Huỳnh Lê Anh Tuấn** (MSSV: 24110143) — *Agent ReAct Loop, Sliding Memory, CLI Gateway & Benchmark*
> - **Lê Khánh Duy** (MSSV: 24110082) — *MCP Server (stdio), Tool Contracts, Atomic Rollback & Multi-Agent*

---

## 1. Tổng quan hệ thống (System Overview)

**Student Second Brain** là hệ thống trợ lý học tập tự chủ được xây dựng bằng Python thuần kết hợp kiến trúc **Agentic RAG** và chuẩn giao thức **Model Context Protocol (MCP)**:
* **Hỏi đáp tri thức không ảo giác (Anti-Hallucination)**: Phân hệ đa tác tử (`Coordinator`, `Researcher`, `EvidenceChecker`, `AnswerAgent`) thẩm định chốt chặn bằng chứng 2 lớp trước khi sinh câu trả lời, kiên quyết từ chối nếu tài liệu không đề cập.
* **Thao tác có kiểm chứng (Verification Protocol)**: Vòng lặp tự chủ ReAct (`Loop.py`) thực thi chuỗi hành động an toàn; mọi lệnh sửa đổi (`update`) bắt buộc phải có lệnh đọc (`get`) đối soát đi liền sau.
* **Cơ chế khôi phục dữ liệu nguyên tử (Atomic Rollback)**: Máy chủ MCP Server độc lập tự động sao lưu và khôi phục tệp nguồn nếu quá trình tái lập chỉ mục VectorStore gặp sự cố.
* **Truy xuất kết hợp (Hybrid RAG)**: Phân đoạn Parent-Child Chunking kết hợp tìm kiếm ngữ nghĩa (Dense Cosine Similarity) và từ khóa chính xác (BM25) qua thuật toán Reciprocal Rank Fusion (RRF, $k=60$).

---

## 2. Hướng dẫn cài đặt và chạy thử (Cold Start Instructions)

Hệ thống yêu cầu môi trường **Python 3.11+**. Thực hiện tái lập môi trường theo các bước sau:

### Bước 1: Khởi tạo môi trường và cài đặt thư viện

```bash
# 1. Tạo môi trường ảo (Virtual Environment)
python -m venv .venv

# 2. Kích hoạt môi trường ảo:
# Trên Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Trên Linux / macOS:
source .venv/bin/activate

# 3. Cài đặt các gói phụ thuộc:
pip install -r requirements.txt
```

*(Hoặc sử dụng trình quản lý `uv` nếu máy đã cài sẵn)*:
```bash
uv pip install -r requirements.txt
```

---

### Bước 2: Thiết lập khóa cấu hình môi trường (`.env`)

Sao chép tệp mẫu cấu hình `.env.example` thành `.env` và điền khóa API của bạn:

```bash
# Trên Windows:
copy .env.example .env

# Trên Linux / macOS:
cp .env.example .env
```

Mở tệp `.env` vừa tạo và cập nhật các tham số tối thiểu:
```env
OPENAI_API_KEY=sk-...               # Điền khóa API của bạn
OPENAI_BASE_URL=https://...        # URL endpoint tương thích OpenAI
OPENAI_MODEL=gpt-4o-mini           # Hoặc mô hình tương đương
DOC_PATH=data/raw                  # Thư mục chứa bài giảng
```

---

## 3. Lệnh chạy thực thi (Execution Commands)

### 3.1. LỆNH CHẠY DEMO HỆ THỐNG CHÍNH (Single Command Demo)
Để khởi động hệ thống trợ lý học tập (bao gồm cổng điều phối Coordinator, ReAct Agent và Multi-Agent):

```bash
python main.py
```

* **Câu hỏi tra cứu tài liệu mẫu (Multi-Agent RAG)**:
  ```text
  Cơ chế bão hòa tần suất (saturation) và chuẩn hóa độ dài trong thuật toán BM25 có tác dụng gì?
  ```
* **Yêu cầu cập nhật ghi chép có đối soát (ReAct Side-effect + Verify)**:
  ```text
  Cập nhật ghi chú về MCP vào doc_DOC0001 và kiểm tra lại
  ```

---

### 3.2. LỆNH CHẠY ĐÁNH GIÁ TỰ ĐỘNG (Evaluation Benchmark)
Để chạy toàn bộ bộ kiểm thử 36 câu hỏi trên `tests/testset.jsonl` qua 3 lượt thử nghiệm và xuất log JSONL vào thư mục `logs/`:

```bash
python -m tests.run_tests
```

---

## 4. Cấu trúc thư mục dự án (Directory Structure)

```text
Student_Second_Brain/
├── data/
│   └── raw/                    # Kho dữ liệu bài giảng thô (DOC0001.txt -> DOC0008.md)
├── logs/                       # Nhật ký các phiên chạy thực nghiệm (.jsonl)
├── src/
│   ├── LLM/                    # Client kết nối API LLM và theo dõi Token USAGE
│   ├── agent/                  # Vòng lặp ReAct Loop, Bộ nhớ trượt (Sliding Memory), Parser
│   ├── mcp/                    # MCP Server (stdio), Tool Adapter (Dynamic Discovery)
│   ├── multi_agent/            # Phân hệ Đa tác tử (Coordinator, Researcher, Checker, Answer)
│   ├── prompts/                # Toàn văn System Prompts đã chuẩn hóa
│   └── rag/                    # Đường ống Hybrid RAG, Parent-Child Chunking, BM25 & VectorStore
├── tests/
│   ├── testset.jsonl           # Bộ câu hỏi kiểm thử (36 câu, bao gồm 12 câu no_answer)
│   └── run_tests.py            # Kịch bản tự động đo lường độ chính xác và chi phí Token
├── .env.example                # Tệp cấu hình mẫu (không chứa key bí mật)
├── .gitignore                  # Cấu hình bảo mật, chặn lộ key .env
├── ai-usage.md                 # Bản khai báo sử dụng AI của cả 3 thành viên
├── requirements.txt            # Danh sách thư viện phụ thuộc Python
├── main.py                     # Điểm khởi chạy chính của hệ thống
└── README.md                   # Tài liệu hướng dẫn cài đặt và vận hành
```

---

## 5. Danh mục các sản phẩm nộp bài (Deliverables Checklist)

* [x] **`report.docx`**: Báo cáo kỹ thuật chuẩn 8–9 trang kèm đầy đủ Phụ lục A, B, C.
* [x] **Repo Code (.git)**: Thư mục mã nguồn lưu trữ đầy đủ lịch sử commit của cả 3 thành viên (`401546a` Dũng, `3e9e5bf` Tuấn, `7ffd454` Duy).
* [x] **`logs/`**: Thư mục chứa $\ge 3$ phiên chạy thử nghiệm thực tế định dạng `.jsonl`.
* [x] **`tests/testset.jsonl`**: Bộ dữ liệu đánh giá gồm 36 câu hỏi (12 câu ngoài phạm vi `no_answer = true`).
* [x] **`ai-usage.md`**: Bản khai báo sử dụng trí tuệ nhân tạo minh bạch theo chuẩn liêm chính học thuật.
* [x] **`README.md`**: Hướng dẫn cài đặt và lệnh chạy duy nhất để tái lập kết quả.