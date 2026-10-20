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

RETRIES = int(os.getenv("LLM_RETRIES", "4"))
RETRY_STATUS ={429, 500, 502, 503, 504}

USAGE = {
    "calls": 0,
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "max_prompt": 0
}


# Giá tính theo USD / 1 triệu tokens.
# Điền đúng giá của nhà cung cấp và model bạn đang sử dụng.
INPUT_PRICE_PER_MILLION = float(
    os.getenv("INPUT_PRICE_PER_MILLION", "0")
)
OUTPUT_PRICE_PER_MILLION = float(
    os.getenv("OUTPUT_PRICE_PER_MILLION", "0")
)

USAGE["cost_usd"] = 0.0


def get_usage() -> dict:
    """Trả về bản sao thống kê token hiện tại."""
    return USAGE.copy()


def get_cost_usd() -> float:
    """Ước tính chi phí dựa trên token input/output."""
    input_cost = (
        USAGE["prompt_tokens"]
        * INPUT_PRICE_PER_MILLION
        / 1_000_000
    )
    output_cost = (
        USAGE["completion_tokens"]
        * OUTPUT_PRICE_PER_MILLION
        / 1_000_000
    )
    return input_cost + output_cost


def print_usage() -> None:
    """In thống kê token và chi phí."""
    cost = get_cost_usd()

    print("\n========== TOKEN USAGE & COST ==========")
    print(f"LLM calls:        {USAGE['calls']}")
    print(f"Input tokens:     {USAGE['prompt_tokens']:,}")
    print(f"Output tokens:    {USAGE['completion_tokens']:,}")
    print(
        "Total tokens:     "
        f"{USAGE['prompt_tokens'] + USAGE['completion_tokens']:,}"
    )
    print(f"Max prompt:       {USAGE['max_prompt']:,}")
    print(f"Estimated cost:   ${cost:.8f} USD")
    print("========================================")


def reset_usage():
    for k in USAGE:
        USAGE[k] = 0

def call_llm(messages, tools=None):
    kwargs = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0
    }

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
            print(f"[llm] HTTP {status or type(exc).__name__} - thử lại {attempt + 1}/{RETRIES - 1} sau {wait}s...")
            time.sleep(wait)

    prompt_tokens = response.usage.prompt_tokens
    completion_tokens = response.usage.completion_tokens

    USAGE["calls"] += 1
    USAGE["prompt_tokens"] += prompt_tokens
    USAGE["completion_tokens"] += completion_tokens
    USAGE["max_prompt"] = max(
        USAGE["max_prompt"], prompt_tokens
    )
    USAGE["cost_usd"] = get_cost_usd()

    return response.choices[0].message

# def call_llm_stream(messages, tools=None):
#     kwargs = {
#         "model": MODEL,
#         "messages": messages,
#         "temperature": 0,
#         "stream": True,
#         "stream_options": {"include_usage": True}
#     }
#     if MAX_TOKENS:
#         kwargs["max_tokens"] = MAX_TOKENS
#     if tools:
#         kwargs["tools"] = tools
#     for attempt in range(RETRIES):
#         try:
#             stream_response = client.chat.completions.create(**kwargs)
#             for chunk in stream_response:
#                 if chunk.choices and chunk.choices[0].delta.content:
#                     yield chunk.choices[0].delta.content
#                 if hasattr(chunk, "usage") and chunk.usage:
#                     prompt_tokens = chunk.usage.prompt_tokens
#                     completion_tokens = chunk.usage.completion_tokens
#                     USAGE["calls"] += 1
#                     USAGE["prompt_tokens"] += prompt_tokens
#                     USAGE["completion_tokens"] += completion_tokens
#                     USAGE["max_prompt"] = max(USAGE["max_prompt"], prompt_tokens)
#                     USAGE["cost_usd"] = get_cost_usd()
#             break
#         except Exception as exc:
#             status = getattr(exc, "status_code", None)
#             if attempt == RETRIES - 1 or (status is not None and status not in RETRY_STATUS):
#                 raise
#             wait = 5 * (attempt + 1)
#             print(f"[llm-stream] HTTP {status or type(exc).__name__} - thử lại sau {wait}s...")
#             time.sleep(wait)
