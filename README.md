# Student Second Brain: Agentic RAG Study Assistant System

> **Đồ án môn học**: AI Programming with Python (AIPR) - Học kỳ 1, Năm học 2026–2026  
> **Khoa**: Công nghệ Thông tin - Trường Đại học Sư phạm Kỹ thuật TP.HCM (HCMUTE)  
> **Giảng viên hướng dẫn**: ThS. Nguyễn Đăng Quang  
> **Nhóm sinh viên thực hiện**:
> - **Trần Lê Dũng** (MSSV: 24110084) — *Data, Ingestion, Parent-Child Chunking & VectorStore*
> - **Huỳnh Lê Anh Tuấn** (MSSV: 24110143) — *Agent ReAct Loop, Sliding Memory, CLI Gateway & Benchmark*
> - **Lê Khánh Duy** (MSSV: 24110082) — *MCP Server (stdio), Tool Contracts, Atomic Rollback & Multi-Agent*

---

## 🛠️ 1. CÀI ĐẶT & THIẾT LẬP MÔI TRƯỜNG (COLD-START SETUP)

Khi tải hoặc clone repository về máy tính mới, thực hiện 2 bước thiết lập sau:

### Bước 1: Khởi tạo môi trường ảo và cài đặt thư viện

```bash
# 1. Tạo môi trường ảo Python 3.11+
python -m venv .venv

# 2. Kích hoạt môi trường ảo:
# Trên Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Trên Windows (Command Prompt - CMD):
.venv\Scripts\activate.bat
# Trên Linux / macOS:
source .venv/bin/activate

# 3. Cài đặt các thư viện cần thiết:
pip install -r requirements.txt
```

*(Hoặc dùng lệnh Makefile ngắn gọn)*:
```bash
make setup
```

### Bước 2: Khởi tạo file cấu hình môi trường (.env)

```bash
# Copy file template mẫu sang .env
copy .env.example .env    # Trên Windows
cp .env.example .env      # Trên Linux/macOS
```

> **Lưu ý**: Mở file `.env` vừa tạo và điền các API key của bạn (`OPENAI_API_KEY`, `OPENAI_BASE_URL`, `JINA_API_KEY`, `GROQ_API_KEY`).

---

## ⚡ 2. KHỞI ĐỘNG HỆ THỐNG (QUICK START DEMO)

Sau khi cài đặt xong, có thể khởi động hệ thống ngay lập tức bằng **1 trong các cách sau**:

### Cách 1: Chạy lệnh trực tiếp qua Terminal (Khuyến nghị)

```bash
python main.py
```
*(Nếu máy đã cài `uv`: `uv run python main.py`)*

### Cách 2: Chạy qua Makefile (Chuẩn quy định của môn học)

```bash
make demo
```
> Hoặc chạy trọn gói cả cài đặt và demo trong 1 dòng lệnh duy nhất:
> ```bash
> make setup && make demo
> ```

### Cách 3: Nhấp đúp chuột trên Windows
Nhấp đúp chuột vào tệp **`run.bat`** ở thư mục gốc của dự án để khởi động ngay.

---

## 🎯 3. KỊCH BẢN CÂU HỎI THỬ NGHIỆM TẠI CHỖ (TEST PROMPTS)

Khi giao diện chat `❓ Nhập câu hỏi (gõ 'exit' để thoát):` xuất hiện, copy các câu mẫu sau để kiểm tra toàn bộ 3 trụ cột của hệ thống:

### Kịch bản 1: Hỏi đáp tài liệu có bằng chứng (Multi-Agent RAG)
Hệ thống kích hoạt Coordinator $\rightarrow$ Researcher $\rightarrow$ EvidenceChecker $\rightarrow$ AnswerAgent để trích xuất và hiển thị nguồn minh chứng:
```text
Cơ chế bão hòa tần suất (saturation) và chuẩn hóa độ dài trong thuật toán BM25 có tác dụng gì?
```
* **Kết quả quan sát**: Bảng **SOURCES & EVIDENCE** hiển thị Score, Doc ID (`DOC0001`), Section và bảng thống kê chi phí Token USAGE.

### Kịch bản 2: Thao tác ghi có kiểm chứng (ReAct Side-Effect + Verify)
Hệ thống tự động kích hoạt chu trình ReAct Loop: `get_document` $\rightarrow$ `update_document` $\rightarrow$ `get_document` đối soát lại:
```text
Cập nhật ghi chú về MCP vào doc_DOC0001 và kiểm tra lại
```
* **Kết quả quan sát**: Agent đọc tài liệu trước khi sửa, thực hiện ghi đè nội dung và bắt buộc gọi lại lệnh đọc lần 2 để kiểm chứng trạng thái trước khi kết luận `Final Answer`.

### Kịch bản 3: Chống ảo giác & Từ chối khi không có dữ liệu (Anti-Hallucination Calibration)
Thử nghiệm với câu hỏi không tồn tại trong giáo trình:
```text
Chính sách hoàn tiền học phí khi bảo lưu kết quả học tập tại trường là gì?
```
* **Kết quả quan sát**: Hệ thống từ chối trả lời, kiên quyết không bịa đặt thông tin.

*(Nhập `exit` để thoát chương trình).*

---

## 📊 4. ĐÁNH GIÁ BENCHMARK & TÍNH NĂNG ĐIỂM CỘNG

### 4.1. Chạy đánh giá tự động (Eval Benchmark)

Chạy tự động bộ kiểm thử 36 câu hỏi (`tests/testset.jsonl`), đo lường độ chính xác và xuất nhật ký chạy vào thư mục `logs/`:

```bash
python -m tests.run_tests
# hoặc dùng lệnh Makefile
make eval
```

---

### 4.2. Xuất bảng tính CSV & Đồ thị Token Usage 300 DPI

Script tự động đọc file log `.jsonl` trong `logs/`, tính toán chi phí theo cấu hình `.env` (`$2` cho 1M input, `$10` cho 1M output) và xuất bảng chi tiết cùng biểu đồ cột chồng:

```bash
# Cách 1: Tự động chọn file log đầy đủ nhất
python -m src.evaluation.export_benchmark
# hoặc
make plot

# Cách 2: Chỉ định một file log cụ thể
python -m src.evaluation.export_benchmark run_20261017_222106_5e6c6a.jsonl
```

* **Kết quả sinh ra trong `logs/`**:
  - `logs/eval_benchmark_detail.csv`: Bảng chi tiết từng câu (STT, Câu hỏi, Phân loại In-domain/No-answer, Prompt Tokens, Completion Tokens, Tổng Tokens, Chi phí USD, và dòng tổng kết `Average`).
  - `logs/chart_token_usage.png`: Biểu đồ cột chồng (Stacked Bar) độ nét cao 300 DPI, hiển thị số token trên đỉnh mỗi cột và đường nét đứt mức trung bình để chèn trực tiếp vào Mục 6.3 Báo cáo.

---

### 4.3. Ứng dụng MCP Client thứ 2 độc lập — Interoperability

Chứng minh khả năng tương tác độc lập (Interoperability) của máy chủ MCP Server theo đúng chuẩn giao thức Model Context Protocol: một ứng dụng Python Client thứ 2 kết nối trực tiếp tới MCP Server qua kênh Stdio, tự động khám phá công cụ và cung cấp menu tương tác cho người dùng:

```bash
# Chạy trực tiếp từ thư mục gốc dự án:
python src/mcp/mcp_client.py
# hoặc qua uv:
uv run python src/mcp/mcp_client.py
```

* **Quy trình tương tác**:
  1. Client kết nối ngầm tới `src.mcp.server` qua Stdio và gọi `tools/list` để khám phá danh sách công cụ động.
  2. Menu lựa chọn thao tác:
     * **1. Tìm kiếm (search)**: Nhập từ khóa truy vấn ngữ nghĩa trên cơ sở tri thức (vd: `RAG`).
     * **2. Đọc tài liệu (get)**: Nhập Document ID (vd: `doc_DOC0001`) để đọc toàn bộ nội dung văn bản.
     * **3. Cập nhật tài liệu (update)**: Nhập Document ID và nội dung mới (hỗ trợ nhập văn bản nhiều dòng, gõ `END` ở dòng cuối để gửi). Sau khi cập nhật, hệ thống tự động gọi lệnh `get` để xác minh (verify) dữ liệu đã lưu thành công.
     * **0. Thoát**.

---

## 📂 5. CẤU TRÚC THƯ MỤC DỰ ÁN (PROJECT DIRECTORY)

```text
Student_Second_Brain/
├── data/
│   └── raw/                    # Dữ liệu bài giảng gốc (DOC0001.txt -> DOC0008.md)
├── logs/                       # Nhật ký các phiên chạy thực tế (.jsonl)
├── src/
│   ├── LLM/                    # Kết nối mô hình ngôn ngữ và bảng đếm token USAGE
│   ├── agent/                  # Vòng lặp ReAct Loop, Bộ nhớ trượt Sliding Memory, Parser
│   ├── mcp/                    # MCP Server (stdio), Tool Adapter khám phá tool động
│   ├── multi_agent/            # Hệ đa tác tử (Coordinator, Researcher, Checker, Answer)
│   ├── prompts/                # Toàn văn System Prompts tiếng Việt
│   └── rag/                    # Hybrid RAG, Parent-Child Chunking, BM25 & VectorStore
├── tests/
│   ├── testset.jsonl           # Bộ 36 câu hỏi đánh giá (12 câu no_answer)
│   └── run_tests.py            # Kịch bản chạy tự động đo đạc độ chính xác và token
├── .env.example                # Bản mẫu cấu hình an toàn (không chứa key bí mật)
├── .gitignore                  # Cấu hình bảo mật, chặn lộ key .env
├── ai-usage.md                 # Bản khai báo sử dụng AI theo chuẩn liêm chính học thuật
├── Makefile                    # Lệnh make setup, make demo, make eval
├── run.bat                     # File kích hoạt chạy nhanh 1-click trên Windows
├── main.py                     # Điểm khởi chạy chính thức của hệ thống
└── README.md                   # Hướng dẫn chi tiết sử dụng và vận hành
```

---

## 📋 6. BẢNG PHÂN CÔNG ĐÓNG GÓP & COMMIT HASH

| Thành viên | Trách nhiệm chuyên môn chính | Tỷ lệ đóng góp | Commit Hash tiêu biểu |
| :--- | :--- | :---: | :--- |
| **Trần Lê Dũng**<br>(Role A) | Thiết kế pipeline Ingestion, Parent-Child Chunking, thuật toán Hybrid Search (Dense + BM25) kết hợp RRF ($k=60$), VectorStore cache. | **33.3%** | `401546a`, `2d5a78c`, `f4b5ee6` |
| **Huỳnh Lê Anh Tuấn**<br>(Role B) | Vòng lặp tự chủ ReAct `Loop.py`, Bộ nhớ cửa sổ trượt `Memory.py`, bắt lỗi cú pháp `Parser.py`, bộ testset 36 câu, gateway `main.py` và công cụ phân tích benchmark `export_benchmark.py`. | **33.4%** | `3e9e5bf`, `426157b`, `d4ce1de` |
| **Lê Khánh Duy**<br>(Role C) | Xây dựng MCP Server chuẩn stdio, các tool `search`, `get`, `update`, ứng dụng MCP Client thứ 2 độc lập `mcp_client.py`, cơ chế Atomic Rollback, hệ thống Đa tác tử `MultiAgentSystem`. | **33.3%** | `7ffd454`, `a6094ba`, `01ae85b` |