import pytest

from app.services import ai_service
from app.services.ai_service import AIService


class FakeMessage:
    def __init__(self, content):
        self.content = content


class FakeChoice:
    def __init__(self, content):
        self.message = FakeMessage(content)


class FakeUsage:
    prompt_tokens = 10
    completion_tokens = 5
    total_tokens = 15


class FakeResponse:
    def __init__(self, content):
        self.choices = [FakeChoice(content)]
        self.usage = FakeUsage()


@pytest.mark.asyncio
async def test_retry_logic(monkeypatch):
    ai_service.settings.azure_openai_api_key = "test-key"
    ai_service.settings.azure_openai_endpoint = "https://example.openai.azure.com"
    service = AIService()
    calls = {"count": 0}

    async def fake_client_create(**_kwargs):
        calls["count"] += 1
        if calls["count"] < 3:
            from openai import APIError

            raise APIError("boom", request=None, body=None)
        return FakeResponse('{"ok": true}')

    monkeypatch.setattr(service.client.chat.completions, "create", fake_client_create)
    result = await service._create_completion({"model": "x", "messages": []})
    assert result.choices[0].message.content == '{"ok": true}'
    assert calls["count"] == 3


@pytest.mark.asyncio
async def test_rate_limiter_acquire():
    ai_service.settings.azure_openai_api_key = "test-key"
    ai_service.settings.azure_openai_endpoint = "https://example.openai.azure.com"
    service = AIService()
    await service.limiter.acquire(10)
    assert service.limiter.requests_available <= service.limiter.requests_capacity



@pytest.mark.asyncio
async def test_response_parsing_fallback(monkeypatch):
    ai_service.settings.azure_openai_api_key = "test-key"
    ai_service.settings.azure_openai_endpoint = "https://example.openai.azure.com"
    service = AIService()

    async def fake_create(_payload):
        return FakeResponse('noise {"answer": 1} noise')

    monkeypatch.setattr(service, "_create_completion", fake_create)
    async def fake_record_usage(*_args, **_kwargs):
        return None

    monkeypatch.setattr(service, "_record_usage", fake_record_usage)

    async def fake_get(*_args, **_kwargs):
        return None

    monkeypatch.setattr("app.services.ai_service.ai_cache_service.get", fake_get)

    async def fake_set(*_args, **_kwargs):
        return None

    monkeypatch.setattr("app.services.ai_service.ai_cache_service.set", fake_set)

    result = await service.complete("sys", "user")
    assert result["answer"] == 1


def test_token_estimation():
    assert AIService.estimate_tokens("abcd") == 1
    assert AIService.estimate_tokens("a" * 400) >= 100


@pytest.mark.asyncio
async def test_batch_processing(monkeypatch):
    ai_service.settings.azure_openai_api_key = "test-key"
    ai_service.settings.azure_openai_endpoint = "https://example.openai.azure.com"
    service = AIService()

    async def fake_complete(*_args, **_kwargs):
        return {"items": [{"id": "1"}, {"id": "2"}]}

    monkeypatch.setattr(service, "complete", fake_complete)
    items = await service.batch_complete("sys", ["a", "b"])
    assert len(items) == 2
