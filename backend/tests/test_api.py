from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models import AISettings, Execution, User
from app.security import create_access_token, decrypt_api_key, encrypt_api_key
from app.services.openrouter import OpenRouterError


def test_private_history_and_execution_ownership() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        first = User(google_sub="first", email="first@example.test", name="First")
        second = User(google_sub="second", email="second@example.test", name="Second")
        db.add_all([first, second])
        db.flush()
        db.add_all(
            [
                AISettings(user_id=first.id, model="openrouter/free"),
                AISettings(
                    user_id=second.id,
                    encrypted_api_key=encrypt_api_key("private-openrouter-key-012345"),
                    model="openrouter/free",
                ),
            ]
        )
        private_result = Execution(
            user_id=second.id,
            tool_id="private-tool",
            input_data={"context": "private"},
            result="private result",
            model="openrouter/free",
            tone="professional",
        )
        db.add(private_result)
        db.commit()
        first_token = create_access_token(first.id)
        second_token = create_access_token(second.id)
        private_id = private_result.id

    with TestClient(app) as client:
        assert client.get("/api/auth/status").status_code == 200
        assert client.get("/api/auth/status").json() is None
        client.cookies.set("aitoolnity_session", first_token)
        assert client.get("/api/auth/status").json()["email"] == "first@example.test"
        history = client.get("/api/history")
        assert history.status_code == 200
        assert history.json() == []
        private_execution = client.post(
            f"/api/executions/{private_id}/regenerate",
            headers={"Idempotency-Key": "private-regenerate-request-0001"},
        )
        assert private_execution.status_code == 404
        private_settings = client.get("/api/settings")
        assert private_settings.status_code == 200
        assert "encrypted_api_key" not in private_settings.text
        assert private_settings.json() == {
            "model": "openrouter/free",
            "has_api_key": False,
        }
        client.cookies.set("aitoolnity_session", second_token)
        second_settings = client.get("/api/settings")
        assert second_settings.status_code == 200
        assert second_settings.json()["has_api_key"] is True
        assert "private-openrouter-key" not in second_settings.text
        client.cookies.delete("aitoolnity_session")
        assert client.get("/api/history").status_code == 401

    with SessionLocal() as db:
        assert db.scalar(select(User).where(User.email == "first@example.test")) is not None


def test_generic_execution_is_idempotent_and_saves_result(monkeypatch) -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        user = User(google_sub="runner", email="runner@example.test", name="Runner")
        db.add(user)
        db.flush()
        db.add(
            AISettings(
                user_id=user.id,
                encrypted_api_key=encrypt_api_key("test-openrouter-key-012345"),
                model="openrouter/free",
            )
        )
        db.commit()
        token = create_access_token(user.id)

    calls = []

    async def fake_generate(**kwargs):
        calls.append(kwargs)
        return f"A useful answer {len(calls)}."

    monkeypatch.setattr("app.main.generate", fake_generate)
    with TestClient(app) as client:
        client.cookies.set("aitoolnity_session", token)
        headers = {"Idempotency-Key": "generate-request-0001"}
        response = client.post(
            "/api/executions",
            headers=headers,
            json={
                "tool_id": "career-path-finder",
                "inputs": {"context": "I enjoy working with data."},
                "tone": "professional",
            },
        )
        assert response.status_code == 200
        assert response.json()["result"] == "A useful answer 1."
        assert response.json()["model"] == "openrouter/free"
        assert calls[0]["model"] == "openrouter/free"
        assert calls[0]["api_key"] == "test-openrouter-key-012345"
        assert "Professional" in calls[0]["system_prompt"]
        replay = client.post(
            "/api/executions",
            headers=headers,
            json={
                "tool_id": "career-path-finder",
                "inputs": {"context": "I enjoy working with data."},
                "tone": "professional",
            },
        )
        assert replay.status_code == 200
        assert replay.json()["id"] == response.json()["id"]
        assert len(calls) == 1
        reused_key = client.post(
            "/api/executions",
            headers=headers,
            json={
                "tool_id": "career-path-finder",
                "inputs": {"context": "A different task."},
                "tone": "professional",
            },
        )
        assert reused_key.status_code == 409
        assert len(calls) == 1

        regenerated = client.post(
            f"/api/executions/{response.json()['id']}/regenerate",
            headers={"Idempotency-Key": "regenerate-request-0002"},
        )
        assert regenerated.status_code == 200
        assert regenerated.json()["result"] == "A useful answer 2."

        refined = client.post(
            f"/api/executions/{regenerated.json()['id']}/refine",
            headers={"Idempotency-Key": "refine-request-0003"},
            json={"tone": "concise", "instructions": "Use three bullet points."},
        )
        assert refined.status_code == 200
        assert refined.json()["tone"] == "concise"
        assert "Previous result:" in calls[-1]["user_prompt"]
        assert "Use three bullet points." in calls[-1]["user_prompt"]
        assert "Concise" in calls[-1]["system_prompt"]
        assert len(calls) == 3

        history = client.get("/api/history")
        assert len(history.json()) == 3

        invalid = client.post(
            "/api/executions",
            headers={"Idempotency-Key": "invalid-request-0004"},
            json={
                "tool_id": "career-path-finder",
                "inputs": {"unknown": "value"},
                "tone": "professional",
            },
        )
        assert invalid.status_code == 422


def test_missing_personal_key_does_not_use_server_key(monkeypatch) -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        user = User(google_sub="no-key", email="no-key@example.test", name="No key")
        db.add(user)
        db.flush()
        db.add(AISettings(user_id=user.id, model="openrouter/free"))
        db.commit()
        token = create_access_token(user.id)

    monkeypatch.setenv("OPENROUTER_API_KEY", "shared-server-key-0123456789")
    with TestClient(app) as client:
        client.cookies.set("aitoolnity_session", token)
        response = client.post(
            "/api/executions",
            headers={"Idempotency-Key": "no-key-request-0001"},
            json={
                "tool_id": "career-path-finder",
                "inputs": {"context": "I enjoy working with data."},
                "tone": "professional",
            },
        )
        assert response.status_code == 400
        assert "shared-server-key" not in response.text
        assert client.get("/api/history").json() == []


def test_provider_failure_does_not_create_history(monkeypatch) -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        user = User(google_sub="provider-failure", email="provider@example.test", name="Provider")
        db.add(user)
        db.flush()
        db.add(
            AISettings(
                user_id=user.id,
                encrypted_api_key=encrypt_api_key("test-openrouter-key-012345"),
                model="openrouter/free",
            )
        )
        db.commit()
        token = create_access_token(user.id)

    async def failed_generate(**kwargs):
        raise OpenRouterError(429, "OpenRouter rate limit reached.")

    monkeypatch.setattr("app.main.generate", failed_generate)
    with TestClient(app) as client:
        client.cookies.set("aitoolnity_session", token)
        response = client.post(
            "/api/executions",
            headers={"Idempotency-Key": "provider-failure-0001"},
            json={
                "tool_id": "career-path-finder",
                "inputs": {"context": "A task"},
                "tone": "professional",
            },
        )
        assert response.status_code == 429
        assert client.get("/api/history").json() == []


def test_settings_are_encrypted_updated_and_removed() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        user = User(google_sub="settings-owner", email="settings@example.test", name="Settings")
        db.add(user)
        db.flush()
        db.add(AISettings(user_id=user.id, model="openrouter/free"))
        db.commit()
        token = create_access_token(user.id)
        user_id = user.id

    with TestClient(app) as client:
        client.cookies.set("aitoolnity_session", token)
        saved = client.put(
            "/api/settings",
            json={
                "model": "openai/gpt-4o-mini",
                "api_key": "test-openrouter-key-012345",
            },
        )
        assert saved.status_code == 200
        assert saved.json() == {"model": "openai/gpt-4o-mini", "has_api_key": True}
        assert "test-openrouter-key" not in saved.text

        with SessionLocal() as db:
            settings = db.scalar(
                select(AISettings).where(AISettings.user_id == user_id)
            )
            assert settings is not None
            assert settings.encrypted_api_key != "test-openrouter-key-012345"
            assert decrypt_api_key(settings.encrypted_api_key) == "test-openrouter-key-012345"

        removed = client.delete("/api/settings/api-key")
        assert removed.status_code == 200
        assert removed.json()["has_api_key"] is False
        leaked_key = "private-key material with spaces"
        invalid_key = client.put(
            "/api/settings",
            json={"model": "openai/gpt-4o-mini", "api_key": leaked_key},
        )
        assert invalid_key.status_code == 422
        assert leaked_key not in invalid_key.text


def test_invalid_and_missing_authentication_are_rejected() -> None:
    with TestClient(app) as client:
        assert client.get("/api/history").status_code == 401
        client.cookies.set("aitoolnity_session", "not-a-session-token")
        assert client.get("/api/settings").status_code == 401
        assert client.get("/api/auth/status").json() is None


def test_request_size_limit_and_rate_limit() -> None:
    with TestClient(app) as client:
        assert (
            client.get(
                "/api/catalogue/categories",
                headers={"Origin": "http://localhost:3000"},
            ).status_code
            == 200
        )
        disallowed_origin = client.get(
            "/api/catalogue/categories",
            headers={"Origin": "https://untrusted.example"},
        )
        assert disallowed_origin.status_code == 403

        too_large = client.post(
            "/api/auth/logout",
            content=b"x" * (512 * 1024 + 1),
            headers={"content-type": "application/json"},
        )
        assert too_large.status_code == 413

        responses = [
            client.post(
                "/api/executions",
                headers={"Idempotency-Key": f"rate-limited-request-{index:04d}"},
                json={},
            )
            for index in range(6)
        ]
        assert [response.status_code for response in responses].count(429) == 1
