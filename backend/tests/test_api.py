from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models import AISettings, Execution, User
from app.security import create_access_token, encrypt_api_key


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
            f"/api/executions/{private_id}/regenerate"
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


def test_generic_execution_uses_provider_and_saves_result(monkeypatch) -> None:
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
        return "A useful answer."

    monkeypatch.setattr("app.main.generate", fake_generate)
    with TestClient(app) as client:
        client.cookies.set("aitoolnity_session", token)
        response = client.post(
            "/api/executions",
            json={
                "tool_id": "career-path-finder",
                "inputs": {"context": "I enjoy working with data."},
                "tone": "professional",
            },
        )
        assert response.status_code == 200
        assert response.json()["result"] == "A useful answer."
        assert response.json()["model"] == "openrouter/free"
        assert calls[0]["model"] == "openrouter/free"
        assert "Professional" in calls[0]["system_prompt"]
        history = client.get("/api/history")
        assert len(history.json()) == 1

        invalid = client.post(
            "/api/executions",
            json={
                "tool_id": "career-path-finder",
                "inputs": {"unknown": "value"},
                "tone": "professional",
            },
        )
        assert invalid.status_code == 422
