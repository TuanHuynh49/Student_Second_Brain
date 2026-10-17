import os
from typing import List, Any
from groq import Groq

DECOMPOSE_PROMPT = """Break this answer into individual factual claims. Return one claim per line. No extra text.
Answer: {answer}"""

JUDGE_PROMPT = """Context:
{context}

Claim: {claim}

Is this claim supported by the context? Answer only YES or NO."""

def check_faithfulness(answer: str, context_chunks: List[Any], client: Groq = None, model: str = "openai/gpt-oss-120b") -> float:
    """Tính tỷ lệ các khẳng định được context hỗ trợ (từ 0.0 đến 1.0)."""
    if client is None:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    def ask(prompt: str) -> str:
        res = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        return res.choices[0].message.content.strip()

    # Trích xuất nội dung từ chunks linh hoạt
    texts = []
    for c in context_chunks:
        if hasattr(c, "parent") and hasattr(c.parent, "content"):
            texts.append(c.parent.content)
        elif hasattr(c, "content"):
            texts.append(c.content)
        elif isinstance(c, dict) and "content" in c:
            texts.append(c["content"])
        else:
            texts.append(str(c))
    context_text = "\n\n".join(texts)

    if not context_text.strip() or not answer.strip():
        return 0.0

    # Tách và chấm điểm từng claim
    claims_text = ask(DECOMPOSE_PROMPT.format(answer=answer))
    claims = [line.strip("-• ") for line in claims_text.splitlines() if line.strip()]
    if not claims:
        return 1.0

    supported = sum(
        1 for claim in claims 
        if ask(JUDGE_PROMPT.format(context=context_text, claim=claim)).upper().startswith("YES")
    )
    return supported / len(claims)