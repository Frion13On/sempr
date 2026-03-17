from http import HTTPStatus

import auth
from conftest import QueryStep
from flask_login import logout_user
from models import User, users


def test_login_sql_injection_blocked(app, mock_db, monkeypatch):
    connection = mock_db(
        auth,
        [
            QueryStep(fetchone=None),
        ],
    )
    monkeypatch.setattr(auth, "flash", lambda *args, **kwargs: None)

    with app.test_request_context():
        user, role_id = auth.authenticate_user("' OR '1'='1", "' OR '1'='1")

    assert user is None
    assert role_id is None
    query, params = connection._cursor.executed[0]
    assert "%s" in query
    assert params == ("' OR '1'='1",)


def test_add_user_rejects_sql_injection(client):
    response = client.post(
        "/api/add_user",
        json={
            "table": "преподаватели",
            "data": {
                "фио_преп": "Иванов И.И.",
                "логин": "' OR '1'='1",
                "пароль": "StrongPass1!",
            },
        },
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    body = response.get_json()
    assert body["success"] is False
    assert "опасный" in body["error"]


def test_authorization_checks(app):
    with app.test_request_context():
        admin = User(1, role_id=1)
        teacher = User(2, role_id=2, teacher_id=42)
        student = User(3, role_id=3, student_id=100)

        auth.login_user(admin)
        assert auth.check_admin_access() is True
        logout_user()

        auth.login_user(student)
        assert auth.check_teacher_access() is False
        logout_user()

        auth.login_user(teacher)
        assert auth.check_teacher_access() is True
        logout_user()


def test_logout_invalidates_session(app):
    app.config["LOGIN_DISABLED"] = False

    with app.test_client() as client:
        users.clear()
        users[1] = User(1, role_id=1)
        with client.session_transaction() as session:
            session["_user_id"] = "1"

        response = client.get("/logout")

        assert response.status_code == 302
        assert 1 not in users

