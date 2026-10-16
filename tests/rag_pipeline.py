import os
from typing import Optional, Tuple, List
from dotenv import load_dotenv
from groq import Groq
from rich import print

from src.rag.vectordb.VectorStore import VectorStore
from src.models.Query import Query
from src.models.DocumentChunk import RetrievedChunk
from src.rag.retrieval.Retriever import retrieve

RAG_SYSTEM_PROMPT = """You are an intelligent academic assistant for a Student Second Brain system. 
Answer the user's question based ONLY on the following context retrieved from study materials.
If the context does not contain enough information, say: "I cannot find enough information in the provided documents."

Context:
{context}

Question: {question}"""


def format_retrieved_chunk(retrieved_chunk: RetrievedChunk, index: int) -> str:
    """Format đối tượng RetrievedChunk (chứa Parent Chunk và các Child khớp) thành văn bản ngữ cảnh."""
    parent = retrieved_chunk.parent
    # Trích xuất metadata an toàn từ parent chunk
    source = parent.metadata.get("source", "unknown_source")
    title = parent.metadata.get("title", "study_document")
    subject = parent.metadata.get("subject", "general")
    
    return f"[{index + 1}] (Môn: {subject} | Nguồn: {title} - {source})\nScore: {retrieved_chunk.score:.4f}\n{parent.content}"


def build_rag_prompt(question: str, retrieved_chunks: list[RetrievedChunk], top_k: int = 3) -> list[dict]:
    """Xây dựng cấu trúc messages gửi cho LLM từ danh sách Parent Chunks."""
    context_text = "\n\n---\n\n".join(
        format_retrieved_chunk(rc, i) for i, rc in enumerate(retrieved_chunks[:top_k])
    )
    
    system_prompt = RAG_SYSTEM_PROMPT.format(
        context=context_text,
        question=question
    )
    
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ]


def rag_pipeline(
    query_text: str, 
    store: VectorStore, 
    client: Groq, 
    mode: str = "hybrid", 
    top_k: int = 3, 
    score_threshold: float = 0.0,
    metadata: Optional[dict] = None
) -> Tuple[str, List[RetrievedChunk]]:
    """
    Thực thi toàn bộ luồng RAG Pipeline:
    1. Đóng gói Query object (hỗ trợ text, top_k, threshold, metadata).
    2. Truy xuất thông qua Retriever (Dense/Hybrid -> Rerank -> Parent-Child Aggregation).
    3. Xây dựng Prompt và gọi LLM (Groq API).
    """
    # 1. Khởi tạo đối tượng Query theo kiến trúc mới
    query = Query(
        text=query_text,
        top_k=top_k,
        score_threshold=score_threshold,
        metadata=metadata or {}
    )
    
    # 2. Gọi Retriever điều phối tìm kiếm
    results = retrieve(query, store, mode=mode, alpha=0.6, oversample=4)
    
    if not results:
        return "I cannot find enough information in the provided documents.", []

    # 3. Tạo messages cho LLM
    messages = build_rag_prompt(query_text, results, top_k=top_k)
    
    # 4. Gọi LLM qua Groq client
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",  
            messages=messages,
            temperature=0.1,         
            max_tokens=1024
        )
        
        answer = response.choices[0].message.content
        return answer, results
        
    except Exception as e:
        return f"Lỗi khi gọi Groq API: {str(e)}", results


if __name__ == "__main__":
    load_dotenv()
    
    # Khởi tạo Groq Client
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    # Load VectorStore từ cache
    myStore = VectorStore().load()
    print(f"[bold green]Đã load thành công VectorStore từ cache![/bold green]")
        
        # Test câu hỏi thực tế với chế độ hybrid và lọc metadata môn học (ví dụ)
    test_query = "Nói cho tôi về chuyến bay từ Hồ Chí Minh tới Nha Trang"
    test_metadata = {} # Hoặc ví dụ: {"subject": "Toán học"}
        
    print(f"\n[bold cyan]Đang chạy RAG Pipeline (Mode: hybrid)...[/bold cyan]")
    answer, retrieved_chunks = rag_pipeline(
            query_text=test_query,
            store=myStore,
            client=groq_client,
            mode="dense",
            top_k=3,
            score_threshold=0.1,
            metadata=test_metadata
        )
        
    print(f"\n[bold yellow]=== CÂU TRẢ LỜI TỪ LLM ===[/bold yellow]\n{answer}\n")
    print(f"[bold green]=== CÁC PARENT CHUNKS ĐƯỢC RETRIEVE ({len(retrieved_chunks)}) ===[/bold green]")
    for idx, rc in enumerate(retrieved_chunks, 1):
      print(f"- [Top {idx}] Parent ID: {rc.parent.parent_id} | Score: {rc.score:.4f}")
      print(f"  Nội dung: {rc.parent.content[:120]}...\n")
