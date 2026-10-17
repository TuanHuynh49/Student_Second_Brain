import os
from typing import List, Any
from groq import Groq

RELEVANCE_PROMPT = """You are evaluating a RAG system. A user asked a question and the system answered.
Determine whether the answer actually addresses the question.

Question:
{question}

Answer:
{answer}

Is the answer relevant to the question? Answer only "YES" or "NO"."""

CHUNK_PROMPT = """Does this chunk contain information relevant to the question?

Question: {question}

Chunk: {chunk}

Answer only "YES" or "NO"."""

def check_answer_relevance(
    question: str, 
    answer: str, 
    client: Groq = None, 
    model: str = "openai/gpt-oss-120b"
) -> bool:
    """Kiểm tra xem câu trả lời có giải quyết đúng trọng tâm câu hỏi hay không (LLM-as-judge)."""
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

    verdict = ask(RELEVANCE_PROMPT.format(question=question, answer=answer))
    return verdict.upper().startswith("YES")
def check_context_precision(
    question: str, 
    chunks: List[Any], 
    client: Groq = None, 
    model: str = "openai/gpt-oss-120b"
) -> float:
    """Tính tỷ lệ phần trăm các retrieved chunks thực sự liên quan đến câu hỏi (từ 0.0 đến 1.0)."""
    if not chunks:
        return 0.0

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

    hits = 0
    for chunk in chunks:
        # Xử lý linh hoạt nhiều kiểu cấu trúc chunk khác nhau trong hệ thống của bạn
        if hasattr(chunk, "parent") and hasattr(chunk.parent, "content"):
            chunk_text = chunk.parent.content
        elif hasattr(chunk, "content"):
            chunk_text = chunk.content
        elif isinstance(chunk, dict) and "content" in chunk:
            chunk_text = chunk["content"]
        else:
            chunk_text = str(chunk)

        prompt = CHUNK_PROMPT.format(question=question, chunk=chunk_text[:500])
        verdict = ask(prompt)
        if verdict.upper().startswith("YES"):
            hits += 1

    return hits / len(chunks)