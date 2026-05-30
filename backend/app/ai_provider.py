import os
import httpx
import asyncio
from typing import Dict, Any

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OLLAMA_URL = os.getenv("OLLAMA_URL")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")


async def _call_openai(prompt: str, max_tokens: int = 300) -> Dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": "You are a concise summarizer that extracts the meaningful changes from web page snapshots."},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.2,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        text = ""
        try:
            text = data["choices"][0]["message"]["content"]
        except Exception:
            text = data.get("choices", [{}])[0].get("text", "")
        return {"summary": text.strip(), "raw": data}


async def _call_ollama(prompt: str, model: str = "llama2", max_tokens: int = 300) -> Dict[str, Any]:
    # Generic lightweight Ollama/local-LLM caller.
    # The environment variable OLLAMA_URL should point to an HTTP endpoint that accepts {'prompt': ...}
    if not OLLAMA_URL:
        raise RuntimeError("OLLAMA_URL not configured")
    payload = {"prompt": prompt, "max_tokens": max_tokens, "model": model}
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(OLLAMA_URL, json=payload)
        r.raise_for_status()
        data = r.json()
        # Expecting {'text': '...'} or {'result': '...'}
        text = data.get("text") or data.get("result") or data.get("output") or ""
        return {"summary": text.strip(), "raw": data}


async def generate_summary(text: str, max_tokens: int = 400) -> Dict[str, Any]:
    """Generate a concise summary and importance score for given snapshot text/html.

    Strategy: prefer OpenAI if API key configured; else try Ollama URL; else fallback to heuristic.
    """
    prompt = f"Summarize the most important changes or items from the following webpage snapshot. Present a short 2-3 sentence summary and a single importance score 0-1.\n\nContent:\n{text}"
    try:
        if OPENAI_API_KEY:
            res = await _call_openai(prompt, max_tokens=max_tokens)
            summary = res.get("summary", "")
            # simple heuristic importance: length ratio
            importance = min(1.0, max(0.0, len(summary) / 400.0))
            return {"summary": summary, "importance_score": importance, "raw": res.get("raw")}
        elif OLLAMA_URL:
            res = await _call_ollama(prompt, max_tokens=max_tokens)
            summary = res.get("summary", "")
            importance = min(1.0, max(0.0, len(summary) / 400.0))
            return {"summary": summary, "importance_score": importance, "raw": res.get("raw")}
        else:
            # fallback: naive extract first 3 lines
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            summary = " ".join(lines[:3])
            importance = 0.3
            return {"summary": summary, "importance_score": importance, "raw": {"method": "heuristic"}}
    except Exception as e:
        return {"summary": "", "importance_score": 0.0, "raw": {"error": str(e)}}
