import os
import time
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
    )

MODEL = os.getenv(
    "MODEL", "gpt-6.1-sol"
)

MAX_TOKENS = int(os.getenv("MAX_TOKENS", "0"))
RETRIES = int(os.getenv("LLM_RETRIES", "4"))
RETRY_STATUS ={429, 500, 502, 503, 504}

USAGE = {
    "calls": 0,
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "max_prompt": 0
}

def reset_usage():
    for k in USAGE:
        USAGE[k] = 0

def call_llm(message, tools=None):
    kwargs = {
        "model": MODEL,
        "messages": message,
        "temperature": 0
    }

    if MAX_TOKENS:
        kwargs["max_tokens"] = MAX_TOKENS
    if tools:
        kwargs["tools"] = tools

    respone = None
    for attempt in range(RETRIES):
        try:
            respone = client.chat.completions.create(**kwargs)
            break
        except Exception as exc:
            status = getattr(exc, "status_code", None)

            if attempt == RETRIES - 1 or (status is not None and status not in RETRY_STATUS):
                raise
            wait = 5 * (attempt + 1)
            print(f"[llm] HTTP {status or type(exc).__name__} - thử lại {attempt + 1}/{RETRIES - 1} sau {wait}s...")
            time.sleep(wait)

    prompt_tokens = respone.usage.prompt_tokens
    completion_tokens = respone.usage.completion_tokens

    USAGE["calls"] += 1
    USAGE["prompt_tokens"] += prompt_tokens
    USAGE["completion_tokens"] += completion_tokens
    USAGE["max_prompt"] = max(USAGE["max_prompt"], prompt_tokens)

    return respone.choices[0].message

def call_llm_stream(message, tools = None):
    kwargs = {
        "model": MODEL,
        "messages": message,
        "temperature": 0,
        "stream": True
    }
    if MAX_TOKENS:
        kwargs["max_tokens"] = MAX_TOKENS
    if tools:
        kwargs["tools"] = tools
    for attempt in range(RETRIES):
        try:
            stream_response = client.chat.completions.create(**kwargs)
            for chunk in stream_response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
            break
        except Exception as exc:
            status = getattr(exc, "status_code", None)
            if attempt == RETRIES - 1 or (status is not None and status not in RETRY_STATUS):
                raise
            wait = 5 * (attempt + 1)
            print(f"[llm-stream] HTTP {status or type(exc).__name__} - thử lại sau {wait}s...")
            time.sleep(wait)


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
    print("\n" + "=" * 50)
    print("🌊 TEST STREAMING (Chữ chạy ra từng từ):")
    stream_msgs = [
        {"role": "user", "content": "Hãy đếm từ 1 đến 5 và giải thích ngắn gọn vì sao nên học môn AI."}
    ]
    print("AI: ", end="", flush=True)
    for token in call_llm_stream(stream_msgs):
        print(token, end="", flush=True)
        time.sleep(0.03)  # Tạo hiệu ứng gõ phím mượt mà
    print("\n")









