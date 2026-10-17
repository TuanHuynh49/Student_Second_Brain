import os
from typing import List, Any
from groq import Groq
from src.evaluation.faithfulness import decompose_claims, judge_claim

CHUNK_RELEVANCE_PROMPT = """Does this chunk contain information relevant to the question?

Question: {question}

Chunk: {chunk}

Answer only "YES" or "NO"."""

def judge_chunk_relevant(question: str, chunk: Any, client: Groq = None, model: str = "openai/gpt-oss-120b") -> bool:
    """Kiểm tra xem một chunk có thực sự liên quan đến câu hỏi hay không."""
    if client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY chưa được thiết lập trong môi trường hoặc file .env.")
        client = Groq(api_key=api_key)

    def ask(prompt: str) -> str:
        reply = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        return reply.choices[0].message.content.strip()

    # Lấy nội dung chunk linh hoạt theo các cấu trúc dữ liệu khác nhau
    if hasattr(chunk, "parent") and hasattr(chunk.parent, "content"):
        chunk_text = chunk.parent.content
    elif hasattr(chunk, "content"):
        chunk_text = chunk.content
    elif isinstance(chunk, dict) and "content" in chunk:
        chunk_text = chunk["content"]
    else:
        chunk_text = str(chunk)

    verdict = ask(CHUNK_RELEVANCE_PROMPT.format(question=question, chunk=chunk_text[:500]))
    return verdict.upper().startswith("YES")

def detect_failure_modes(
    answer: str, 
    question: str, 
    chunks: list, 
    client: Groq = None, 
    model: str = "openai/gpt-oss-120b"
) -> list[str]:
    """
    Phát hiện các dạng lỗi thường gặp (failure modes) của RAG từ câu trả lời + retrieval.
    Trả về danh sách tên các lỗi (nếu rỗng = hệ thống khỏe mạnh, không lỗi).
    """
    failures = []

    # 1. Missing context / low recall: Không retrieve được chunk nào
    if not chunks:
        failures.append("missing_context (no chunks retrieved)")
        return failures

    # Lấy toàn bộ text context từ các chunks
    context_text = "\n\n".join(
        c.parent.content if hasattr(c, "parent") and hasattr(c.parent, "content") 
        else (c.content if hasattr(c, "content") else str(c)) 
        for c in chunks
    )

    # 2. Hallucination: >50% các claims không được context hỗ trợ
    claims = decompose_claims(answer)
    unsupported = sum(1 for c in claims if not judge_claim(c, context_text))
    if claims and unsupported / len(claims) > 0.5:
        failures.append(f"hallucination ({unsupported}/{len(claims)} claims unsupported)")

    # 3. Irrelevant retrieval: <50% số chunks thực sự liên quan câu hỏi
    relevant = sum(1 for c in chunks if judge_chunk_relevant(question, c, client=client, model=model))
    if chunks and relevant / len(chunks) < 0.5:
        failures.append(f"irrelevant_retrieval ({relevant}/{len(chunks)} chunks relevant)")

    # 4. Over-reliance: Mô hình lười suy luận, sao chép nguyên văn (verbatim) từ context
    if answer.strip() in context_text:
        failures.append("over_reliance (answer copied verbatim from context)")

    return failures