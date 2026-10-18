import os
import sys
import json
import csv
from pathlib import Path
from dotenv import load_dotenv

# Đảm bảo in tiếng Việt không lỗi trên terminal Windows
if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Nạp cấu hình đơn giá token trực tiếp từ file .env
PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOGS_DIR = PROJECT_ROOT / "logs"
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(ENV_PATH, override=True)

# Đọc trực tiếp các giá input và output từ .env vào:
# INPUT_PRICE_PER_MILLION: giá cho 1 triệu input tokens (mặc định 2.0 USD)
# OUTPUT_PRICE_PER_MILLION: giá cho 1 triệu output tokens (mặc định 10.0 USD)
INPUT_PRICE = float(os.getenv("INPUT_PRICE_PER_MILLION", "2.0"))
OUTPUT_PRICE = float(os.getenv("OUTPUT_PRICE_PER_MILLION", "10.0"))


# ============================================================
# BƯỚC 1: ĐỌC DỮ LIỆU TỪ FILE LOG JSONL
# ============================================================
def load_log_data(log_file=None):
    """Đọc dữ liệu câu hỏi và token từ file log JSONL."""
    if log_file:
        file_path = LOGS_DIR / log_file
    else:
        candidates = list(LOGS_DIR.glob("run_*.jsonl"))
        if not candidates:
            print("❌ Không tìm thấy file log nào trong thư mục logs/")
            return None, []
        
        # Chọn file log có tổng token ghi nhận cao nhất
        def count_tokens(p):
            total = 0
            with p.open("r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    if '"event": "usage"' in line:
                        try:
                            total += json.loads(line).get("total_tokens", 0)
                        except Exception:
                            pass
            return total

        file_path = max(candidates, key=count_tokens)

    questions = {}
    with file_path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            idx = event.get("question_index")
            if idx is None:
                continue

            # Khởi tạo thông tin câu hỏi nếu chưa có
            if idx not in questions:
                questions[idx] = {
                    "index": idx,
                    "query": "",
                    "category": "In-domain",
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                    "cost": 0.0,
                }

            row = questions[idx]

            # Lấy nội dung câu hỏi
            if event.get("event") == "question_started":
                row["query"] = event.get("query", "")
                row["category"] = "No_answer" if event.get("no_answer") else "In-domain"

            # Lấy số token và tính chi phí
            elif event.get("event") == "usage":
                p = event.get("prompt_tokens", 0)
                c = event.get("completion_tokens", 0)
                row["prompt_tokens"] = p
                row["completion_tokens"] = c
                row["total_tokens"] = p + c
                row["cost"] = round((p / 1_000_000 * INPUT_PRICE) + (c / 1_000_000 * OUTPUT_PRICE), 6)

    # Trả về danh sách câu hỏi đã sắp xếp thứ tự Q1 -> Q12
    sorted_rows = [questions[k] for k in sorted(questions.keys())]
    return file_path.name, sorted_rows


# ============================================================
# BƯỚC 2: XUẤT RA FILE BẢNG CSV
# ============================================================
def export_csv(rows, output_file):
    """Xuất kết quả từng câu ra bảng CSV để mở bằng Excel."""
    headers = [
        "STT", "Câu hỏi", "Phân loại",
        "Prompt Tokens", "Completion Tokens", "Tổng Tokens", "Chi phí (USD)"
    ]

    with output_file.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)

        for r in rows:
            writer.writerow([
                r["index"], r["query"], r["category"],
                r["prompt_tokens"], r["completion_tokens"], r["total_tokens"],
                f"${r['cost']:.6f}"
            ])

        # Ghi thêm dòng trung bình (Average) ở cuối bảng
        n = len(rows)
        if n > 0:
            avg_p = round(sum(r["prompt_tokens"] for r in rows) / n, 2)
            avg_c = round(sum(r["completion_tokens"] for r in rows) / n, 2)
            avg_total = round(sum(r["total_tokens"] for r in rows) / n, 2)
            avg_cost = sum(r["cost"] for r in rows) / n
            writer.writerow([
                "Average", f"Trung bình {n} câu", "-",
                avg_p, avg_c, f"{avg_total:.2f}", f"${avg_cost:.6f}"
            ])

    print(f"✅ Đã xuất bảng CSV: {output_file.name}")


# ============================================================
# BƯỚC 3: VẼ BIỂU ĐỒ BẰNG MATPLOTLIB
# ============================================================
def draw_chart(rows, output_file):
    """Vẽ biểu đồ cột thống kê token từng câu (Stacked Bar Chart)."""
    try:
        import matplotlib.pyplot as plt

        labels = [f"Q{r['index']}" for r in rows]
        prompts = [r["prompt_tokens"] for r in rows]
        completions = [r["completion_tokens"] for r in rows]
        totals = [r["total_tokens"] for r in rows]
        avg_val = sum(totals) / len(totals) if totals else 0

        fig, ax = plt.subplots(figsize=(10, 5))

        # Vẽ 2 lớp cột chồng: Prompt Tokens (xanh) ở dưới, Completion Tokens (cam) ở trên
        ax.bar(labels, prompts, label="Prompt Tokens", color="#2b5c8f", width=0.6)
        ax.bar(labels, completions, bottom=prompts, label="Completion Tokens", color="#e27c3e", width=0.6)

        # Hiển thị số token trên đầu mỗi cột
        for i, t in enumerate(totals):
            if t > 0:
                ax.text(
                    i, t + 20, str(t), ha="center", va="bottom", fontsize=9, fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.85)
                )

        # Vẽ đường trung bình
        if avg_val > 0:
            ax.axhline(avg_val, color="#d9534f", linestyle="--", linewidth=1.5, label=f"Trung bình: {avg_val:.2f}")

        ax.set_title("Thống kê Token tiêu thụ theo từng câu hỏi (Mục 6.3 Báo cáo)", fontsize=13, fontweight="bold", pad=12)
        ax.set_xlabel("Câu hỏi (Q1-Q8: In-domain | Q9-Q12: No-answer)", fontsize=11, fontweight="bold")
        ax.set_ylabel("Số lượng Tokens", fontsize=11, fontweight="bold")
        ax.set_ylim(0, max(totals) * 1.18 if totals else 1000)
        ax.legend(loc="upper right", frameon=True)
        ax.grid(axis="y", linestyle="--", alpha=0.4)

        plt.tight_layout()
        plt.savefig(output_file, dpi=300)
        plt.close()

        print(f"✅ Đã vẽ biểu đồ PNG: {output_file.name}")

    except ImportError:
        print("ℹ️  Gợi ý: Cài matplotlib (`pip install matplotlib`) để lưu biểu đồ ảnh.")


# ============================================================
# HÀM CHÍNH (MAIN)
# ============================================================
def main():
    print("\n--- XUẤT CSV VÀ VẼ ĐỒ THỊ BENCHMARK ---")

    # Cho phép truyền tên file log cụ thể qua dòng lệnh:
    # python -m src.evaluation.export_benchmark [ten_file_log.jsonl]
    target_log = sys.argv[1] if len(sys.argv) > 1 else None

    log_name, rows = load_log_data(target_log)
    if not rows:
        return

    print(f"📁 Đọc dữ liệu từ log: {log_name} ({len(rows)} câu hỏi)")

    # 1. Xuất file CSV
    export_csv(rows, LOGS_DIR / "eval_benchmark_detail.csv")

    # 2. Vẽ biểu đồ PNG
    draw_chart(rows, LOGS_DIR / "chart_token_usage.png")

    # 3. In tóm tắt kết quả
    total_tokens = sum(r["total_tokens"] for r in rows)
    total_cost = sum(r["cost"] for r in rows)
    print(f"\n📊 TỔNG KẾT:")
    print(f"- Số câu hỏi        : {len(rows)}")
    print(f"- Tổng số Tokens    : {total_tokens:,} tokens")
    print(f"- Đơn giá từ .env   : Input = ${INPUT_PRICE}/1M tokens | Output = ${OUTPUT_PRICE}/1M tokens")
    print(f"- Chi phí ước tính  : ${total_cost:.6f} USD")
    print("---------------------------------------\n")


if __name__ == "__main__":
    main()
