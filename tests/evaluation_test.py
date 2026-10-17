import os
from dotenv import load_dotenv
from rich import print

# Import hệ thống RAG và các công cụ đánh giá (Faithfulness, Relevance, Precision)
from src.rag.pipeline.pipeline import StudentSecondBrainRAG
from src.evaluation.faithfulness import check_faithfulness
from src.evaluation.relevance_precision import check_answer_relevance, check_context_precision
from src.rag.vectordb.VectorStore import VectorStore

load_dotenv()

def main():
    print("[bold cyan]🚀 Bắt đầu kiểm thử RAG Pipeline với 4 Test Cases & Đầy đủ 3 Thang đo...[/bold cyan]")
    
    # 1. Khởi tạo VectorStore từ kho đã lưu index
    store = VectorStore().load()
    
    # 2. Khởi tạo RAG Engine trung tâm
    rag_engine = StudentSecondBrainRAG(store=store)

    # 3. Danh sách 4 câu hỏi kiểm thử
    test_cases = [
        {
            "query": "Các triều đại lịch sử của Việt Nam",
            "metadata": {"subject": ["history"]}
        },
        {
            "query": "Việt nam là quốc gia như thế nào ",
            "metadata": {"subject": ["history"]}
        },
        {
            "query": "Lũy thừa là gì",
            "metadata": {"subject": ["math"]}
        },
        {
            "query": "Quy định đăng ký học phần và tín chỉ tại trường",
            "metadata": {"subject": ["regulations"]}
        }
    ]

    # 4. Vòng lặp chạy qua từng Test Case
    for idx, test in enumerate(test_cases, 1):
        query_text = test["query"]
        metadata = test["metadata"]
        
        print(f"\n[bold magenta]════════════════════════════════════════════════════════[/bold magenta]")
        print(f"[bold magenta]📌 TEST CASE {idx} / {len(test_cases)}[/bold magenta]")
        print(f"[bold yellow]❓ Câu hỏi truy vấn:[/bold yellow] {query_text}")

        # Chạy RAG Pipeline
        print("[bold blue]🔍 Đang thực hiện truy xuất và sinh câu trả lời...[/bold blue]")
        answer, retrieved_chunks = rag_engine.run(
            query_text=query_text,
            mode="hybrid",
            top_k=3,
            metadata=metadata
        )

        # In kết quả trả về từ LLM
        print(f"\n[bold green]=== CÂU TRẢ LỜI TỪ GROQ LLM ===[/bold green]\n{answer}")
        
        # In chi tiết các nguồn tài liệu (chunks) liên quan
        print(f"\n[bold blue]📊 Chi tiết các Nguồn tài liệu liên quan ({len(retrieved_chunks)} chunks):[/bold blue]")
        if not retrieved_chunks:
            print("  [red]⚠️ Không tìm thấy chunk nào phù hợp với truy vấn![/red]")
        else:
            for c_idx, rc in enumerate(retrieved_chunks, 1):
                parent = rc.parent
                source = parent.metadata.get("source", "unknown_source")
                subject = parent.metadata.get("subject", "general")
                score = rc.score
                
                content_snippet = parent.content[:250].replace("\n", " ") + "..." if len(parent.content) > 250 else parent.content
                
                print(f"  [cyan]• [Chunk {c_idx}][/cyan] Môn: [yellow]{subject}[/yellow] | Nguồn: [green]{source}[/green] | Score: [magenta]{score:.4f}[/magenta]")
                print(f"    [italic grey]Nội dung: {content_snippet}[/italic grey]")

        # 5. Chạy đánh giá đồng thời cả 3 Thang Đo
        print("\n[bold magenta]⚖️ Đang gọi các công cụ đánh giá (Faithfulness, Relevance, Precision)...[/bold magenta]")
        
        # Thang đo 1: Faithfulness (Độ trung thực)
        faith_score = check_faithfulness(
            answer=answer,
            context_chunks=retrieved_chunks,
            client=rag_engine.client
        )
        
        # Thang đo 2: Answer Relevance (Độ liên quan của câu trả lời so với câu hỏi)
        is_relevant = check_answer_relevance(
            question=query_text,
            answer=answer,
            client=rag_engine.client
        )
        
        # Thang đo 3: Context Precision (Độ chính xác của các retrieved chunks)
        precision_score = check_context_precision(
            question=query_text,
            chunks=retrieved_chunks,
            client=rag_engine.client
        )

        # 6. Báo cáo kết quả tổng hợp cho từng câu
        print(f"[bold cyan]────────────────────────────────────────────────────────[/bold cyan]")
        print(f"[bold green]🎯 Faithfulness Score      : {faith_score:.2f} / 1.0[/bold green]")
        print(f"[bold yellow]🎯 Answer Relevance        : {'✅ YES (Relevant)' if is_relevant else '❌ NO (Irrelevant)'}[/bold yellow]")
        print(f"[bold magenta]🎯 Context Precision Score : {precision_score:.2f} / 1.0[/bold magenta]")
        
        if faith_score >= 0.8 and is_relevant and precision_score >= 0.5:
            print("[green]✨ Đánh giá chung: Pipeline hoạt động hoàn hảo trên test case này![/green]")
        else:
            print("[yellow]⚠️ Đánh giá chung: Có chỉ số cảnh báo, cần xem lại retrieval hoặc prompt.[/yellow]")
        print(f"[bold cyan]────────────────────────────────────────────────────────[/bold cyan]")

    print("\n[bold cyan]🎉 Hoàn thành kiểm thử toàn diện với đầy đủ 3 thang đo![/bold cyan]")

if __name__ == "__main__":
    main()