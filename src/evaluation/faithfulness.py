import os
from typing import List, Any
from groq import Groq

DECOMPOSE_PROMPT = """Break this answer into individual factual claims.
Return one claim per line. Do not add anything else.

Answer:
{answer}"""

JUDGE_PROMPT = """You are a strict verifier.
Check whether the given claim is SUPPORTED by the context.

Context:
{context}

Claim:
{claim}

Is this claim supported by the context? Answer only "YES" or "NO"."""

def check_faithfulness(
    answer: str, 
    context_chunks: List[Any], 
    client: Groq = None, 
    model: str = "openai/gpt-oss-120b"
) -> float:
    
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

    context_texts = []
    for c in context_chunks:
        if hasattr(c, "parent") and hasattr(c.parent, "content"):
            context_texts.append(c.parent.content)
        elif hasattr(c, "content"):
            context_texts.append(c.content)
        elif isinstance(c, dict) and "content" in c:
            context_texts.append(c["content"])
        else:
            context_texts.append(str(c))
            
    context_text = "\n\n".join(context_texts)
    
    if not context_text.strip():
        return 0.0

    text = ask(DECOMPOSE_PROMPT.format(answer=answer))
    claims = [line.strip("-• ") for line in text.splitlines() if line.strip()]
    
    if not claims:
        return 1.0

    supported_count = 0
    for claim in claims:
        verdict = ask(JUDGE_PROMPT.format(context=context_text, claim=claim))
        if verdict.upper().startswith("YES"):
            supported_count += 1

    return supported_count / len(claims)