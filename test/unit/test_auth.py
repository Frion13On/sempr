from flask import Flask

import auth
from conftest import MockConnection, QueryStep
from models import users


def _setup_app_context():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test"
    return app.app_context()


def test_authenticate_user_success(monkeypatch):
    users.clear()
    connection = MockConnection([QueryStep(fetchone=(2, 42))])
    monkeypatch.setattr(auth, "get_db_connection", lambda: connection)
    monkeypatch.setattr(auth, "login_user", lambda user: None)

    with _setup_app_context():
        user, role_id = auth.authenticate_user("teacher01", "secret")

    assert role_id == 2
    assert user.id == "teacher01"
    assert connection.closed
    assert connection.committed is False


def test_authenticate_user_invalid_credentials(monkeypatch):
    users.clear()
    connection = MockConnection([QueryStep(fetchone=None)])
    monkeypatch.setattr(auth, "get_db_connection", lambda: connection)
    monkeypatch.setattr(auth, "login_user", lambda user: None)

    with _setup_app_context():
        user, role_id = auth.authenticate_user("ghost", "wrong")

    assert user is None
    assert role_id is None
    assert connection.closed


def test_authenticate_user_db_error(monkeypatch):
    messages = []

    def raise_conn():
        raise Exception("DB offline")

    users.clear()
    monkeypatch.setattr(auth, "get_db_connection", raise_conn)
    monkeypatch.setattr(auth, "flash", lambda message, category: messages.append((message, category)))

    with _setup_app_context():
        user, role_id = auth.authenticate_user("any", "pass")

    assert user is None
    assert role_id is None
    assert any("Ошибка подключения к базе данных" in msg[0] for msg in messages)

