"""CRM field extraction call, shared by the Streamlit app (app.py) and the eval (eval/run_eval.py).

The OpenAI-compatible client is passed in, so tests can use a fake client with no network.
"""

import json
import time

from prompts import MODEL_NAME, SYSTEM_PROMPT, TEMPERATURE


def build_messages(text):
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"入力メモ:\n{text}"},
    ]


def parse_json_object(content):
    """Parse the model output. Raises ValueError if it is not a JSON object."""
    try:
        data = json.loads(content)
    except (TypeError, json.JSONDecodeError) as e:
        raise ValueError(f"model output is not valid JSON: {e}") from e
    if not isinstance(data, dict):
        raise ValueError("model output is not a JSON object")
    return data


def extract_crm_data(client, text):
    """Call the model once. Returns a dict with success, data or error, latency and token usage."""
    start = time.perf_counter()
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=build_messages(text),
            response_format={"type": "json_object"},
            temperature=TEMPERATURE,
        )
        latency = round(time.perf_counter() - start, 2)
        usage = response.usage
        return {
            "success": True,
            "data": parse_json_object(response.choices[0].message.content),
            "latency": latency,
            "prompt_tokens": getattr(usage, "prompt_tokens", None),
            "completion_tokens": getattr(usage, "completion_tokens", None),
            "total_tokens": getattr(usage, "total_tokens", None),
        }
    except Exception as e:
        return {"success": False, "error": str(e), "latency": round(time.perf_counter() - start, 2)}
