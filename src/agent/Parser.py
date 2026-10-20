import re
import json
from typing import Optional, Dict, Any, Tuple

def safe_extract_json(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None

    markdown_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if markdown_match: 
        text = markdown_match.group(1)

    json_match = re.search(r"(\{.*\})", text, re.DOTALL)
    if not json_match:
        return None

    json_str = json_match.group(1)

    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        try:
            fixed_str = json_str.replace("'", '"')
            return json.loads(fixed_str)
        except Exception:
            return None

def parse_react_response(text: str) -> Tuple[Optional[str], Optional[Dict[str, Any]], Optional[str]]:
    if not text:
        return None, None, "Không nhận được phản hồi từ AI."

    final_match = re.search(r"Final answer:\s*(.*)", text, re.DOTALL | re.IGNORECASE)
    if final_match:
        return None, None, final_match.group(1).strip()

    action_match = re.search(r"Action:\s*([a-zA-Z0-9_]+)", text)

    input_match = re.search(r"Action Input:\s*(\{.*\}|\[.*\]|.+)", text, re.DOTALL)

    if action_match:
        action_name = action_match.group(1).strip()
        action_args = {}

        if input_match:
            raw_input = input_match.group(1).strip()
            extracted_json = safe_extract_json(raw_input)

            if extracted_json:
                action_args = extracted_json
            else:
                action_args = {"raw_input": raw_input}

        return action_name, action_args, None

    return None, None, text.strip()

