from __future__ import annotations

import asyncio
import json
import random
import re
import time
from collections.abc import Sequence

from openai import APIError, APITimeoutError, AsyncAzureOpenAI, RateLimitError

from app.config import get_settings
from app.redis_client import get_redis_client
from app.services.ai_cache import ai_cache_service
from app.services.prompt_templates import (
    CONTRACT_EXTRACTION_PROMPT,
    EMAIL_CLASSIFICATION_PROMPT,
    EMAIL_SUMMARY_PROMPT,
    LIFECYCLE_STAGE_PROMPT,
    STAKEHOLDER_EXTRACTION_PROMPT,
    THREAD_MERGE_PROMPT,
)

settings = get_settings()


class TokenBucketLimiter:
    def __init__(self, requests_per_minute: int = 60, tokens_per_minute: int = 90_000) -> None:
        self.requests_capacity = float(requests_per_minute)
        self.tokens_capacity = float(tokens_per_minute)
        self.requests_available = float(requests_per_minute)
        self.tokens_available = float(tokens_per_minute)
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self, estimated_tokens: int) -> None:
        while True:
            async with self._lock:
                now = time.monotonic()
                elapsed = now - self.last_refill
                if elapsed > 0:
                    self.requests_available = min(
                        self.requests_capacity,
                        self.requests_available + elapsed * (self.requests_capacity / 60.0),
                    )
                    self.tokens_available = min(
                        self.tokens_capacity,
                        self.tokens_available + elapsed * (self.tokens_capacity / 60.0),
                    )
                    self.last_refill = now

                if self.requests_available >= 1 and self.tokens_available >= estimated_tokens:
                    self.requests_available -= 1
                    self.tokens_available -= estimated_tokens
                    return

                req_wait = max(0.0, (1 - self.requests_available) / (self.requests_capacity / 60.0))
                tok_wait = max(0.0, (estimated_tokens - self.tokens_available) / (self.tokens_capacity / 60.0))
                wait_for = max(req_wait, tok_wait, 0.05)

            await asyncio.sleep(wait_for)


class AIService:
    context_window = 128_000

    def __init__(self) -> None:
        self.client = AsyncAzureOpenAI(
            api_key=settings.azure_openai_api_key,
            azure_endpoint=settings.azure_openai_endpoint,
            api_version="2024-10-21",
        )
        self.deployment = settings.azure_openai_deployment
        self.limiter = TokenBucketLimiter()

    @staticmethod
    def estimate_tokens(*parts: str) -> int:
        text = "\n".join(p for p in parts if p)
        return max(1, int(len(text) / 4))

    @staticmethod
    def _safe_json_parse(raw_content: str) -> dict:
        try:
            return json.loads(raw_content)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw_content, flags=re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    return {"raw": raw_content}
            return {"raw": raw_content}

    async def _record_usage(self, usage: object) -> None:
        redis = await get_redis_client()
        prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
        completion_tokens = getattr(usage, "completion_tokens", 0) or 0
        total_tokens = getattr(usage, "total_tokens", prompt_tokens + completion_tokens) or 0
        await redis.hincrby("ai:usage", "prompt_tokens", int(prompt_tokens))
        await redis.hincrby("ai:usage", "completion_tokens", int(completion_tokens))
        await redis.hincrby("ai:usage", "total_tokens", int(total_tokens))

    async def _create_completion(self, payload: dict) -> object:
        retries = 3
        delay = 0.5
        for attempt in range(retries):
            try:
                return await self.client.chat.completions.create(**payload)
            except (RateLimitError, APITimeoutError, APIError):
                if attempt == retries - 1:
                    raise
                await asyncio.sleep(delay + random.uniform(0.0, 0.2))
                delay *= 2

        raise RuntimeError("unreachable")

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        response_format: str = "json",
    ) -> dict:
        cache_payload = {
            "system": system_prompt,
            "user": user_prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": response_format,
            "model": self.deployment,
        }
        cache_key = ai_cache_service.make_cache_key(cache_payload)
        cached = await ai_cache_service.get(cache_key)
        if cached is not None:
            return cached

        estimated_tokens = self.estimate_tokens(system_prompt, user_prompt)
        if estimated_tokens + max_tokens > self.context_window:
            user_prompt = user_prompt[: (self.context_window - max_tokens) * 4]
            estimated_tokens = self.estimate_tokens(system_prompt, user_prompt)

        await self.limiter.acquire(estimated_tokens)

        payload = {
            "model": self.deployment,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "timeout": 45,
        }
        if response_format == "json":
            payload["response_format"] = {"type": "json_object"}

        response = await self._create_completion(payload)
        await self._record_usage(getattr(response, "usage", None))

        content = response.choices[0].message.content if response.choices else "{}"
        if isinstance(content, Sequence) and not isinstance(content, str):
            content = "".join(getattr(item, "text", "") for item in content)
        content = content or "{}"

        parsed = self._safe_json_parse(content) if response_format == "json" else {"text": content}
        await ai_cache_service.set(cache_key, parsed)
        return parsed

    async def batch_complete(self, system_prompt: str, user_prompts: list[str], temperature: float = 0.1) -> list[dict]:
        numbered = "\n\n".join(f"[{idx+1}] {item}" for idx, item in enumerate(user_prompts))
        payload = await self.complete(
            system_prompt=system_prompt,
            user_prompt=f"Process all items and return JSON array under 'items'.\n{numbered}",
            temperature=temperature,
            max_tokens=4096,
            response_format="json",
        )
        items = payload.get("items") if isinstance(payload, dict) else None
        if isinstance(items, list):
            return [item for item in items if isinstance(item, dict)]
        return []

    async def classify_emails(self, emails: list[dict]) -> list[dict]:
        prompts = [json.dumps(item, default=str) for item in emails]
        return await self.batch_complete(EMAIL_CLASSIFICATION_PROMPT, prompts)

    async def merge_threads(self, email_groups: list[dict]) -> list[dict]:
        prompts = [json.dumps(item, default=str) for item in email_groups]
        return await self.batch_complete(THREAD_MERGE_PROMPT, prompts)

    async def extract_contract_metadata(self, thread_data: dict) -> dict:
        return await self.complete(CONTRACT_EXTRACTION_PROMPT, json.dumps(thread_data, default=str), max_tokens=2000)

    async def extract_stakeholder_info(self, emails: list[dict]) -> list[dict]:
        prompts = [json.dumps(item, default=str) for item in emails]
        return await self.batch_complete(STAKEHOLDER_EXTRACTION_PROMPT, prompts)

    async def detect_lifecycle_stage(self, thread_data: dict) -> dict:
        return await self.complete(LIFECYCLE_STAGE_PROMPT, json.dumps(thread_data, default=str), max_tokens=2000)

    async def generate_summary(self, text: str) -> str:
        result = await self.complete(EMAIL_SUMMARY_PROMPT, text, max_tokens=500)
        return str(result.get("summary", ""))


_ai_service: AIService | None = None


def get_ai_service() -> AIService:
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service
