import os
from typing import Any

import httpx


class OpenRouterError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(message)


async def generate(
    *,
    api_key: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
) -> str:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    site_url = os.getenv("OPENROUTER_SITE_URL")
    site_name = os.getenv("OPENROUTER_SITE_NAME", "AIToolnity")
    if site_url:
        headers["HTTP-Referer"] = site_url
    headers["X-Title"] = site_name

    try:
        async with httpx.AsyncClient(timeout=75) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                },
            )
    except httpx.TimeoutException as error:
        raise OpenRouterError(504, "OpenRouter did not respond in time. Try again.") from error
    except httpx.RequestError as error:
        raise OpenRouterError(
            502, "Could not connect to OpenRouter. Check the service and try again."
        ) from error

    if response.status_code == 401:
        raise OpenRouterError(401, "OpenRouter rejected the API key. Check your saved key.")
    if response.status_code == 429:
        raise OpenRouterError(429, "OpenRouter rate limit reached. Try again shortly.")
    if response.status_code == 404:
        raise OpenRouterError(
            422, f"OpenRouter model '{model}' is unavailable. Select another model."
        )
    if response.status_code >= 400:
        if response.status_code >= 500:
            raise OpenRouterError(502, "OpenRouter reported a service error. Try again later.")
        raise OpenRouterError(
            422,
            f"OpenRouter could not complete this request (HTTP {response.status_code}). "
            "Check the selected model and account.",
        )

    try:
        data: Any = response.json()
        content = data["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError) as error:
        raise OpenRouterError(502, "OpenRouter returned an unexpected response.") from error
    if not isinstance(content, str) or not content.strip():
        raise OpenRouterError(502, "OpenRouter returned an empty response.")
    return content.strip()
