import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from rich import print
from rich.table import Table
from groq import RateLimitError

from src.models.Document import Document
from src.rag.pipeline.pipeline import StudentSecondBrainRAG
from src.rag.vectordb.VectorStore import VectorStore
from src.evaluation.evaluator import Evaluator, EvalExample

load_dotenv()

def run_benchmark_13_questions():
    """Chạy Batch Test Benchmark 13 câu hỏi với Hybrid Search (Đã sửa lỗi Unpack Evaluator)."""
    print("[bold cyan]🚀 Bắt đầu chạy Batch Test Benchmark RAG Pipeline (Hybrid Search - 13 Câu hỏi)...[/bold cyan]")
    
    log_dir = Path("rag_log")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    store = VectorStore().load()
    rag = StudentSecondBrainRAG(store=store)

    # Danh sách 13 câu hỏi kiểm thử
    questions = [
        "Python Data Structures nào phù hợp nhất để lưu trữ một embedding vector cố định không thay đổi?",
        "Cấu trúc của một response object trong OpenAI Chat Completions API gồm những thành phần chính nào?",
        "Giải thích cơ chế hoạt động và vai trò của lớp @dataclass trong lập trình AI với Python.",
        "Sự khác biệt cốt lõi giữa Parent Chunking và Child Chunking trong chiến lược RAG là gì?",
        "Khoảng cách Cosine Similarity trong tìm kiếm vector dùng để đo lường điều gì giữa câu hỏi và đoạn văn bản?",
        "Tại sao trong prompt của hệ thống RAG thường có chỉ dẫn: 'Answer based ONLY on the following context'?",
        "Một pipeline RAG cơ bản gồm những giai đoạn xử lý tuần tự nào từ khi nhận câu hỏi đến khi trả lời?",
        "Khi xây dựng prompt cho RAG, việc gắn nguồn trích dẫn (citations) kèm theo mỗi đoạn chunk mang lại lợi ích gì?",
        "Trong đánh giá hệ thống RAG, chỉ số Faithfulness (độ trung thực) đo lường điều gì?",
        "Tại sao khi sử dụng LLM làm giám khảo (LLM-as-a-judge) để chấm điểm Faithfulness, ta cần thiết lập temperature=0.0?",
        "Giá cổ phiếu hiện tại của tập đoàn Microsoft trên sàn NASDAQ là bao nhiêu USD?",
        "Đội tuyển bóng đá quốc gia nào sẽ đăng cai tổ chức kỳ World Cup gần nhất sau năm 2026?",
        "Hướng dẫn chi tiết công thức nấu món phở bò truyền thống chuẩn vị Hà Nội?"
    ]

    table = Table(title="📊 BẢNG KẾT QUẢ BENCHMARK HYBRID SEARCH (13 CÂU)")
    table.add_column("Q#", justify="center", style="cyan")
    table.add_column("Câu hỏi", style="white", max_width=35)
    table.add_column("Faithfulness", justify="right", style="green")
    table.add_column("Relevance", justify="center", style="yellow")
    table.add_column("Precision", justify="right", style="magenta")
    table.add_column("Tokens", justify="right", style="blue")

    # 🛠 SỬA LỖI: Thêm [:2] để Evaluator chỉ nhận 2 giá trị (answer, chunks)
    evaluator = Evaluator(rag_fn=lambda q: rag.run(query_text=q, mode="hybrid", top_k=3)[:2])

    total_tokens_all = 0
    results_data = []

    for idx, q in enumerate(questions, 1):
        print(f"⏳ Đang xử lý câu {idx}/13 (Hybrid Search)...")
        
        # rag.run trả về đúng 3 giá trị: answer, chunks, tokens
        answer, chunks, tokens = rag.run(query_text=q, mode="hybrid", top_k=3)
        total_tokens_all += tokens

        # Chấm điểm với cơ chế retry tự động khi gặp RateLimitError (429) của Groq
        res = None
        max_retries = 3
        for attempt in range(max_retries):
            try:
                res = evaluator.evaluate_single(EvalExample(question=q))
                break
            except RateLimitError as e:
                if attempt < max_retries - 1:
                    sleep_time = 5 * (attempt + 1)
                    print(f"[yellow]⚠️ Gặp giới hạn token của Groq ở câu {idx}. Đang chờ {sleep_time}s để thử lại...[/yellow]")
                    time.sleep(sleep_time)
                else:
                    print(f"[red]❌ Lỗi Rate Limit sau {max_retries} lần thử.[/red]")
                    raise e

        time.sleep(2.0)  # Tạo độ trễ nhỏ giữa các câu để tránh dồn token

        record = {
            "question": q,
            "answer": answer,
            "tokens": tokens,
            "faithfulness": res.get("faithfulness", 0.0) if res else 0.0,
            "relevance": res.get("relevance", 0.0) if res else 0.0,
            "context_precision": res.get("context_precision", 0.0) if res else 0.0
        }
        results_data.append(record)

        table.add_row(
            str(idx),
            q,
            f"{record['faithfulness']:.2f}",
            "✅ 1.0" if record["relevance"] >= 1.0 else "❌ 0.0",
            f"{record['context_precision']:.2f}",
            str(tokens)
        )

    # Lưu kết quả vào thư mục rag_log dưới dạng JSON
    log_file = log_dir / "hybrid_search_benchmark_13q.json"
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump({
            "total_questions": len(questions),
            "search_mode": "hybrid",
            "total_tokens": total_tokens_all,
            "results": results_data
        }, f, ensure_ascii=False, indent=2)

    print("\n")
    print(table)
    print(f"\n[bold green]✅ Tổng số token tiêu thụ cho 13 câu hỏi (Hybrid Search): [cyan]{total_tokens_all}[/cyan][/bold green]")
    print(f"[bold green]📁 Đã lưu kết quả benchmark vào: [cyan]{log_file}[/cyan][/bold green]")


if __name__ == "__main__":
    run_benchmark_13_questions()