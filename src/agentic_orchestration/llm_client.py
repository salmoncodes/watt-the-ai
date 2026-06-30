import json
import os

import requests


def call_llm(prompt, base_url=None, model=None, temperature=0):
    base_url = base_url or os.getenv("RAG_BIG_LLM_BASE_URL")
    model = model or os.getenv("RAG_BIG_LLM_MODEL", "local-model")

    if not base_url:
        return ""

    url = base_url.rstrip("/") + "/v1/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
    }
    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except (requests.RequestException, KeyError, IndexError, ValueError):
        return ""


def call_small_llm(prompt):
    return call_llm(
        prompt,
        base_url=os.getenv("RAG_SMALL_LLM_BASE_URL"),
        model=os.getenv("RAG_SMALL_LLM_MODEL", "local-small-model"),
        temperature=0,
    )


def parse_json(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}
