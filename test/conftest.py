from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, List, Optional, Sequence

import pytest

from app_new import create_app

from flask.testing import FlaskClient


@dataclass
class QueryStep:
    description: Optional[Sequence[Any]] = None
    fetchone: Any = None
    fetchall: Any = None
    exception: Optional[Exception] = None


class MockCursor:
    def __init__(self, script: Iterable[QueryStep]):
        self._script = list(script)
        self._index = -1
        self._current: Optional[QueryStep] = None
        self.executed: List[tuple[str, Optional[Sequence[Any]]]] = []

    def execute(self, query: str, params: Optional[Sequence[Any]] = None) -> None:
        self.executed.append((query, params))
        self._index += 1
        try:
            self._current = self._script[self._index]
        except IndexError:
            raise AssertionError("MockCursor script exhausted") from None
        if self._current and self._current.exception:
            raise self._current.exception

    @property
    def description(self):
        if self._current and self._current.description:
            return [(name,) for name in self._current.description]
        return None

    def fetchone(self):
        if not self._current:
            return None
        value = self._current.fetchone
        return value() if callable(value) else value

    def fetchall(self):
        if not self._current:
            return []
        value = self._current.fetchall
        return value() if callable(value) else value or []


class MockConnection:
    def __init__(self, script: Iterable[QueryStep]):
        self._cursor = MockCursor(script)
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc:
            self.rollback()
        self.close()
        return False


@pytest.fixture
def app():
    app = create_app()
    app.config.update(TESTING=True, LOGIN_DISABLED=True)
    yield app


@pytest.fixture
def client(app):
    class CsrfClient(FlaskClient):
        csrf_token: str | None = None

        def open(self, *args, **kwargs):
            method = (kwargs.get("method") or "GET").upper()
            headers = dict(kwargs.get("headers") or {})
            if method in {"POST", "PUT", "PATCH", "DELETE"} and self.csrf_token and "X-CSRFToken" not in headers:
                headers["X-CSRFToken"] = self.csrf_token
            kwargs["headers"] = headers
            return super().open(*args, **kwargs)

    app.test_client_class = CsrfClient
    client = app.test_client()
    resp = client.get("/api/csrf")
    client.csrf_token = (resp.get_json() or {}).get("csrf_token")
    return client


@pytest.fixture
def mock_db(monkeypatch):
    def _apply(module, script: Sequence[QueryStep]):
        connection = MockConnection(script)
        monkeypatch.setattr(module, "get_db_connection", lambda: connection)
        return connection

    return _apply