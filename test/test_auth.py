from flask import Flask

import auth
from conftest import MockConnection, QueryStep
from models import users


def _setup_app_context():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test"
    return app.test_request_context()


def test_authenticate_user_success(monkeypatch):
    users.clear()
    # 1) авторизация: id=1, роль=2 (преподаватель); 2) id_преп по user_id
    # 1) авторизация: id=1, роль=2, пароль в открытом виде (будет миграция в хэш)
    # 2) id_преп по user_id
    connection = MockConnection(
        [
            # SELECT id, роль, пароль FROM авторизация WHERE логин = %s
            QueryStep(fetchone=(1, 2, "Secret123!")),
            # UPDATE авторизация SET пароль = %s WHERE id = %s
            QueryStep(),
            # SELECT id_преп FROM преподаватели WHERE user_id = %s
            QueryStep(fetchone=(42,)),
        ]
    )
    monkeypatch.setattr(auth, "get_db_connection", lambda: connection)
    monkeypatch.setattr(auth, "login_user", lambda user: None)

    with _setup_app_context():
        user, role_id = auth.authenticate_user("teacher01", "Secret123!")

    assert role_id == 2
    assert user.id == 1
    assert user.teacher_id == 42
    assert connection.closed
    # При миграции старого пароля в хэш выполняется commit
    assert connection.committed is True


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

