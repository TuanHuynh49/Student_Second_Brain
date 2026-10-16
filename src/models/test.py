import os
import time
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key= os.getenv("OPENAI_API_KEY"),
    base_url= os.getenv("OPENAI_BASE_URL")
)

MODEL = os.getenv("MODEL", "gpt-6.1-sol")

MAX_TOKENS = int(os.getenv("MAX_TOKENS", "0"))
RETRIES = int(os.getenv("RETRIES", "4"))
RETRY_STATUS = {429, 500, 502, 503, 504}

USAGE = {
    "calls": 0,
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "max_prompt": 0
}

def reset_usage():
    for k in USAGE:
        USAGE[k] = 0

def call_llm(messages, tools = None):
    kwargs = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0
    }

    if MAX_TOKENS:
        kwargs["max_tokens"] = MAX_TOKENS
    if tools:
        kwargs["tools"] = tools

    response = None
    for attempt in range(RETRIES):
        try:
            response = client.chat.completions.create(**kwargs)
            break
        except Exception as exc:
            status = getattr(exc, "status_code", None)
            if attempt == RETRIES - 1 or (status is not None and status not in RETRY_STATUS):
                raise
            wait = 5 * (attempt + 1)
            print(f"[llm] HTTP {status or type(exc).__name__} - thử lại lần {attempt + 1}/ {RETRIES - 1} sau {wait}s")
            time.sleep(wait)


    prompt_tokens = response.usage.prompt_tokens
    completion_tokens = response.usage.completion_tokens

    USAGE["calls"] += 1
    USAGE["prompt_tokens"] += prompt_tokens
    USAGE["completion_tokens"] += completion_tokens
    USAGE["max_prompt"] = max(USAGE["max_prompt"], prompt_tokens)

    return response.choices[0].message

    
            
if __name__ == "__main__":
    test_messages = [
        {"role": "user", "content": "Chào bạn, hãy giới thiệu ngắn gọn trong 1 câu bạn là ai?"}
    ]
    print("⏳ Đang gửi yêu cầu kiểm tra tới LLM...")
    reply = call_llm(test_messages)
    print("\n✅ Phản hồi từ AI:")
    print(reply.content)
    print("\n📊 Thống kê Token USAGE:")
    print(USAGE)