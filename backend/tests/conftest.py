import os

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("APP_SECRET_KEY", "test-secret-key-for-aitoolnity")
os.environ.setdefault(
    "ENCRYPTION_KEY", "MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA="
)


@pytest.fixture(autouse=True)
def clear_request_limits():
    from app.main import app
    from app.request_guard import RequestGuard

    if app.middleware_stack is None:
        app.middleware_stack = app.build_middleware_stack()
    current = app.middleware_stack
    while current is not None:
        if isinstance(current, RequestGuard):
            current._requests.clear()
        current = getattr(current, "app", None)
    yield
