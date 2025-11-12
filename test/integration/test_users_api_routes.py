from http import HTTPStatus

import pytest

from api import users_api
from conftest import QueryStep


def test_add_user_success(client, mock_db):
    connection = mock_db(
        users_api,
        [
            QueryStep(fetchone=(0,)),  # логин не используется
            QueryStep(),  # insert
        ],
    )

    response = client.post(
        "/api/add_user",
        json={
            "table": "преподаватели",
            "data": {
                "фио_преп": "Иванов И.И.",
                "логин": "teacher01",
                "пароль": "StrongPass1",
                "почта": "teacher@example.com",
            },
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == {"success": True}
    assert connection.committed is True
    assert connection._cursor.executed[0][0].startswith("SELECT COUNT(*)")


def test_add_user_duplicate_login(client, mock_db):
    mock_db(
        users_api,
        [
            QueryStep(fetchone=(1,)),  # логин существует
        ],
    )

    response = client.post(
        "/api/add_user",
        json={
            "table": "преподаватели",
            "data": {
                "фио_преп": "Петров П.П.",
                "логин": "teacher01",
                "пароль": "AnotherPass1",
            },
        },
    )

    body = response.get_json()
    assert response.status_code == HTTPStatus.CONFLICT
    assert body["success"] is False
    assert "уже существует" in body["error"]


@pytest.mark.parametrize(
    "payload,expected_status",
    [
        ({}, HTTPStatus.BAD_REQUEST),
        ({"table": "студенты"}, HTTPStatus.BAD_REQUEST),
    ],
)
def test_add_user_missing_payload(client, payload, expected_status):
    response = client.post("/api/add_user", json=payload)

    assert response.status_code == expected_status
    body = response.get_json()
    assert body["success"] is False


def test_update_user_success(client, mock_db):
    connection = mock_db(
        users_api,
        [
            QueryStep(fetchone=(0,)),  # unique login check
            QueryStep(),  # update
        ],
    )

    response = client.put(
        "/api/update_user",
        json={
            "table": "преподаватели",
            "idField": "id_преп",
            "id": 77,
            "data": {
                "фио_преп": "Обновленный Преподаватель",
                "логин": "teacher01",
                "пароль": "NewPass123",
            },
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == {"success": True}
    assert connection.committed is True
    assert "UPDATE преподаватели" in connection._cursor.executed[-1][0]


def test_update_user_invalid_table(client):
    response = client.put(
        "/api/update_user",
        json={
            "table": "unknown",
            "idField": "id",
            "id": 1,
            "data": {},
        },
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.get_json()["success"] is False


def test_delete_user_success(client, mock_db):
    connection = mock_db(
        users_api,
        [
            QueryStep(),  # delete
        ],
    )

    response = client.delete(
        "/api/delete_user",
        json={
            "table": "студенты",
            "idField": "id_студ",
            "id": 2001,
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == {"success": True}
    assert connection.committed is True
    assert "DELETE FROM студенты" in connection._cursor.executed[0][0]


def test_add_user_rejects_malicious_input(client):
    response = client.post(
        "/api/add_user",
        json={
            "table": "преподаватели",
            "data": {
                "фио_преп": "<script>alert(1)</script>",
                "логин": "teacher05",
                "пароль": "StrongPass1",
            },
        },
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    body = response.get_json()
    assert body["success"] is False
    assert "опасный" in body["error"]

