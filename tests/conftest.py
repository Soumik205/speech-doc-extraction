import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


@pytest.fixture(autouse=True)
def _isolated_settings(monkeypatch):
    """Every test runs against the mock STT provider regardless of the
    developer's local .env, and starts with a clean Settings cache."""
    monkeypatch.setenv("STT_PROVIDER", "mock")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
