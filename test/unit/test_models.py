import builtins

import psycopg2
import pytest

import models


class DummyConnection:
    def close(self):
        pass


def test_get_db_connection_success(monkeypatch):
    dummy = DummyConnection()
    monkeypatch.setattr(psycopg2, "connect", lambda dsn: dummy)

    conn = models.get_db_connection()

    assert conn is dummy


def test_get_db_connection_failure(monkeypatch):
    monkeypatch.setattr(psycopg2, "connect", lambda dsn: (_ for _ in ()).throw(Exception("boom")))

    with pytest.raises(Exception):
        models.get_db_connection()


def test_user_cache_behaviour():
    models.users.clear()
    user = models.User("user1", role_id=1, student_id=42)

    assert models.get_user_by_id("user1") is user
    assert user.get_id() == "user1"

