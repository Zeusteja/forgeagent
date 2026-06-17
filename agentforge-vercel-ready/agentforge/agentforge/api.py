"""Thin Anthropic API wrapper used by all agents."""
from __future__ import annotations
import os
import json
import time
import httpx
from typing import Optional

MODEL = "claude-sonnet-4-6"
API_URL = "https://api.anthropic.com/v1/messages"


def _headers() -> dict:
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        raise EnvironmentError("ANTHROPIC_API_KEY is not set.")
    return {
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }


def chat(
    system: str,
    user: str,
    max_tokens: int = 2048,
    retries: int = 3,
    temperature: float = 0.3,
) -> str:
    """Call Claude and return the text response."""
    payload = {
        "model": MODEL,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": user}],
        "temperature": temperature,
    }
    for attempt in range(retries):
        try:
            resp = httpx.post(API_URL, headers=_headers(), json=payload, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            return data["content"][0]["text"]
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429 and attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
    raise RuntimeError("API call failed after retries")
