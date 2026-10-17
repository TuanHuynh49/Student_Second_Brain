import os
from dotenv import load_dotenv
from rich import print
from rich.table import Table

from src.rag.pipeline.pipeline import StudentSecondBrainRAG
from src.rag.vectordb.VectorStore import VectorStore
from src.evaluation.evaluator import Evaluator, EvalExample

load_dotenv()

def main():
    print("[bold cyan]🚀 Bắt đầu chạy Batch Test Benchmark RAG Pipeline (12 Câu hỏi)...[/bold cyan]")
    
    # 1. Nạp VectorStore và khởi tạo RAG Pipeline
    store = VectorStore().load()
    rag = StudentSecondBrainRAG(store=store)

    # 2. Danh sách 12 câu hỏi kiểm thử hệ thống
    questions = [
        "Tiến trình (Process) và Luồng (Thread) trong hệ điều hành khác nhau như thế nào?",
        "Nêu các giải thuật lập lịch CPU phổ biến và giải thích hiệu ứng đoàn tàu (Convoy Effect)?",
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

    # 3. Thiết lập bảng hiển thị kết quả trực quan bằng Rich Table
    table = Table(title=" BẢNG KẾT QUẢ BENCHMARK & TOKEN TỪNG CÂU")
    table.add_column("Q#", justify="center", style="cyan")
    table.add_column("Câu hỏi", style="white", max_width=35)
    table.add_column("Faithfulness", justify="right", style="green")
    table.add_column("Relevance", justify="center", style="yellow")
    table.add_column("Precision", justify="right", style="magenta")
    table.add_column("Tokens", justify="right", style="blue")

    evaluator = Evaluator(rag_fn=lambda q: rag.run(query_text=q, mode="hybrid", top_k=3)[:2])

    total_tokens_all = 0

    for idx, q in enumerate(questions, 1):
        print(f"⏳ Đang xử lý câu {idx}/12...")
        
        answer, chunks, tokens = rag.run(query_text=q, mode="hybrid", top_k=3)
        total_tokens_all += tokens

        res = evaluator.evaluate_single(EvalExample(question=q))

        table.add_row(
            str(idx),
            q,
            f"{res['faithfulness']:.2f}",
            "✅ 1.0" if res["relevance"] >= 1.0 else "❌ 0.0",
            f"{res['context_precision']:.2f}",
            str(tokens)
        )

    print("\n")
    print(table)
    print(f"\n[bold green] Tổng số token tiêu thụ cho toàn bộ 12 câu hỏi: [cyan]{total_tokens_all}[/cyan][/bold green]")

if __name__ == "__main__":
    main()