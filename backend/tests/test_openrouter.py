import httpx
import pytest

from app.services import openrouter


@pytest.mark.parametrize(
    ("status_code", "expected_status", "expected_text"),
    [
        (401, 401, "rejected the API key"),
        (404, 422, "model 'openai/missing' is unavailable"),
        (429, 429, "rate limit"),
        (503, 502, "service error"),
    ],
)
def test_provider_errors_are_mapped_without_exposing_credentials(
    monkeypatch: pytest.MonkeyPatch,
    status_code: int,
    expected_status: int,
    expected_text: str,
) -> None:
    key = "test-provider-key-should-never-appear"
    real_client = httpx.AsyncClient

    def client_factory(**kwargs):
        return real_client(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(status_code, json={"error": "failed"})
            ),
            **kwargs,
        )

    monkeypatch.setattr(openrouter.httpx, "AsyncClient", client_factory)

    async def run():
        with pytest.raises(openrouter.OpenRouterError) as raised:
            await openrouter.generate(
                api_key=key,
                model="openai/missing",
                system_prompt="Be useful.",
                user_prompt="Write a summary.",
            )
        assert raised.value.status_code == expected_status
        assert expected_text in raised.value.message
        assert key not in raised.value.message

    import asyncio

    asyncio.run(run())


def test_provider_uses_the_selected_model_and_tone_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests = []
    real_client = httpx.AsyncClient

    def client_factory(**kwargs):
        return real_client(
            transport=httpx.MockTransport(
                lambda request: (
                    requests.append(request)
                    or httpx.Response(
                        200,
                        json={
                            "choices": [
                                {"message": {"content": "A concise answer."}}
                            ]
                        },
                    )
                )
            ),
            **kwargs,
        )

    monkeypatch.setattr(openrouter.httpx, "AsyncClient", client_factory)

    async def run():
        result = await openrouter.generate(
            api_key="test-provider-key-should-never-appear",
            model="openrouter/free",
            system_prompt="Use a concise tone.",
            user_prompt="Summarize this.",
        )
        assert result == "A concise answer."

    import asyncio

    asyncio.run(run())
    assert len(requests) == 1
    assert requests[0].headers["Authorization"] == "Bearer test-provider-key-should-never-appear"
    assert requests[0].read()
    body = requests[0].read().decode()
    assert '"model":"openrouter/free"' in body
    assert "Use a concise tone." in body
