import os
import time
from dotenv import load_dotenv
from rich import print
from rich.table import Table
from groq import RateLimitError

from src.rag.pipeline.pipeline import StudentSecondBrainRAG
from src.rag.vectordb.VectorStore import VectorStore
from src.evaluation.evaluator import Evaluator, EvalExample

load_dotenv()

def main():
    print("[bold cyan]🚀 Bắt đầu chạy Batch Test Benchmark RAG Pipeline (12 Câu hỏi - Dense Mode)...[/bold cyan]")
    
    store = VectorStore().load()
    rag = StudentSecondBrainRAG(store=store)

    questions = [
        "Tiến trình (Process) và Luồng (Thread) trong hệ điều hành khác nhau như thế nào?",
        "Nêu các giải thuật lập lịch CPU phổ biến và hiệu ứng đoàn tàu (Convoy Effect)?",
        "So sánh sự khác nhau giữa hai giao thức TCP và UDP ở tầng giao vận?",
        "Giao thức HTTPS bảo mật hơn HTTP như thế nào và hoạt động trên cổng mặc định nào?",
        "Trình bày 4 tính chất trong nguyên lý ACID của cơ sở dữ liệu quan hệ?",
        "Cấu trúc B-Tree Index giúp tối ưu hóa tốc độ truy vấn SQL như thế nào?",
        "Khóa GIL (Global Interpreter Lock) trong Python ảnh hưởng gì đến các tác vụ tính toán CPU-bound?",
        "Giao thức MCP (Model Context Protocol) gồm có 3 trụ cột cốt lõi nào?",
        "Đội tuyển bóng đá nào đã giành chức vô địch World Cup 2022 tại Qatar?",
        "Giá cổ phiếu của tập đoàn Apple chốt phiên hôm qua là bao nhiêu USD?",
        "Hướng dẫn công thức nấu món phở bò truyền thống của Hà Nội?",
        "Mã hóa kháng lượng tử Kyber hoạt động dựa trên bài toán mạng lưới nào?"
    ]

    # Thiết lập bảng hiển thị kết quả trực quan bằng Rich Table
    table = Table(title="📊 BẢNG KẾT QUẢ BENCHMARK & TOKEN TỪNG CÂU (DENSE)")
    table.add_column("Q#", justify="center", style="cyan")
    table.add_column("Câu hỏi", style="white", max_width=35)
    table.add_column("Faithfulness", justify="right", style="green")
    table.add_column("Relevance", justify="center", style="yellow")
    table.add_column("Precision", justify="right", style="magenta")
    table.add_column("Tokens", justify="right", style="blue")

    # Đồng bộ mode="dense" cho evaluator rag_fn
    evaluator = Evaluator(rag_fn=lambda q: rag.run(query_text=q, mode="dense", top_k=3)[:2])

    total_tokens_all = 0

    for idx, q in enumerate(questions, 1):
        print(f"⏳ Đang xử lý câu {idx}/12...")
        
        if idx > 1:
            time.sleep(2.0) # Giãn cách để tránh chạm ngưỡng TPM

        success = False
        tokens = 0
        res = {"faithfulness": 0.0, "relevance": 0.0, "context_precision": 0.0}

        while not success:
            try:
                # Bóc tách an toàn (hỗ trợ cả 2 hoặc 3 giá trị trả về)
                run_result = rag.run(query_text=q, mode="dense", top_k=3)
                if len(run_result) == 3:
                    answer, chunks, tokens = run_result
                else:
                    answer, chunks = run_result
                    tokens = 0
                    
                total_tokens_all += tokens

                # Đánh giá đơn lẻ qua Evaluator
                res = evaluator.evaluate_single(EvalExample(question=q))
                success = True
                
            except RateLimitError:
                print("[bold yellow]⚠️ Chạm giới hạn Groq Rate Limit. Đang chờ 60 giây để thử lại...[/bold yellow]")
                time.sleep(60)
            except Exception as e:
                print(f"[bold red]❌ Lỗi ở câu {idx}: {e}[/bold red]")
                break

        table.add_row(
            str(idx),
            q,
            f"{res.get('faithfulness', 0.0):.2f}",
            "✅ 1.0" if res.get('relevance', 0.0) >= 1.0 else "❌ 0.0",
            f"{res.get('context_precision', 0.0):.2f}",
            str(tokens)
        )

    print("\n")
    print(table)
    print(f"\n[bold green]🔢 Tổng số token tiêu thụ cho toàn bộ 12 câu hỏi: [cyan]{total_tokens_all}[/cyan][/bold green]")

if __name__ == "__main__":
    main()