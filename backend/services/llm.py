"""
services/llm.py – LLM service with Groq (primary) and Ollama (fallback).

Groq gives fast cloud inference (Llama 3.3 70B).
If Groq is unavailable or unconfigured, falls back to local Ollama.
"""

import json
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class LLMService:
    """
    Unified LLM interface.

    Priority:
      1. Groq API  (llama-3.3-70b-versatile)
      2. Ollama    (llama3.1:latest — local, no API key)
    """

    def __init__(
        self,
        groq_api_key: str = "",
        groq_model: str = "llama-3.3-70b-versatile",
        ollama_url: str = "http://localhost:11434",
        ollama_model: str = "llama3.1:latest",
    ):
        self.groq_api_key = groq_api_key.strip()
        self.groq_model = groq_model
        self.ollama_url = ollama_url.rstrip("/")
        self.ollama_model = ollama_model

        self._groq_available = bool(self.groq_api_key)
        if not self._groq_available:
            logger.warning("Groq API key not set — using Ollama only.")

    # ──────────────────────────────────────────────────────────────────────────
    # Public
    # ──────────────────────────────────────────────────────────────────────────

    async def generate(self, prompt: str, max_tokens: int = 1024) -> str:
        """
        Generate a response.
        Tries Groq first; on any failure falls back to Ollama.
        """
        if self._groq_available:
            try:
                result = await self._generate_groq(prompt, max_tokens)
                logger.debug("LLM response via Groq (%d chars)", len(result))
                return result
            except Exception as exc:
                logger.warning("Groq failed (%s) — falling back to Ollama", exc)

        return await self._generate_ollama(prompt, max_tokens)

    async def health_check(self) -> dict:
        """Check which providers are reachable."""
        status = {"groq": False, "ollama": False}

        if self._groq_available:
            try:
                await self._generate_groq("Say 'ok'", max_tokens=5)
                status["groq"] = True
            except Exception:
                pass

        try:
            await self._generate_ollama("Say 'ok'", max_tokens=5)
            status["ollama"] = True
        except Exception:
            pass

        return status

    # ──────────────────────────────────────────────────────────────────────────
    # Groq
    # ──────────────────────────────────────────────────────────────────────────

    async def _generate_groq(self, prompt: str, max_tokens: int) -> str:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.groq_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        return data["choices"][0]["message"]["content"].strip()

    # ──────────────────────────────────────────────────────────────────────────
    # Ollama
    # ──────────────────────────────────────────────────────────────────────────

    async def _generate_ollama(self, prompt: str, max_tokens: int) -> str:
        url = f"{self.ollama_url}/api/generate"
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": 0.7,
            },
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()

        result = data.get("response", "").strip()
        logger.debug("LLM response via Ollama (%d chars)", len(result))
        return result
