import os
from typing import List, Any
from groq import Groq

RELEVANCE_PROMPT = """Does this answer directly address the question?
Question: {question}
Answer: {answer}
Answer only YES or NO."""

PRECISION_PROMPT = """Does this chunk contain information relevant to the question?
Question: {question}
Chunk: {chunk}
Answer only YES or NO."""

def check_answer_relevance(question: str, answer: str, client: Groq = None, model: str = "openai/gpt-oss-120b") -> bool:
    """Kiểm tra xem câu trả lời có trực tiếp giải quyết câu hỏi không (True/False)."""
    if client is None:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    res = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": RELEVANCE_PROMPT.format(question=question, answer=answer)}],
        temperature=0.0
    )
    return res.choices[0].message.content.strip().upper().startswith("YES")

def check_context_precision(question: str, chunks: List[Any], client: Groq = None, model: str = "openai/gpt-oss-120b") -> float:
    """Tính tỷ lệ các chunk thực sự hữu ích đối với câu hỏi (từ 0.0 đến 1.0)."""
    if not chunks:
        return 0.0
    if client is None:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    relevant_count = 0
    for chunk in chunks:
        if hasattr(chunk, "parent") and hasattr(chunk.parent, "content"):
            chunk_text = chunk.parent.content
        elif hasattr(chunk, "content"):
            chunk_text = chunk.content
        elif isinstance(chunk, dict) and "content" in chunk:
            chunk_text = chunk["content"]
        else:
            chunk_text = str(chunk)

        res = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": PRECISION_PROMPT.format(question=question, chunk=chunk_text[:500])}],
            temperature=0.0
        )
        if res.choices[0].message.content.strip().upper().startswith("YES"):
            relevant_count += 1

    return relevant_count / len(chunks)