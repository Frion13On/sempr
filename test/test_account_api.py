from http import HTTPStatus

from api import account_api
from conftest import QueryStep


def test_get_student_account_success(client, mock_db):
    mock_db(
        account_api,
        [
            QueryStep(
                fetchone=(
                    "Иванов Иван Иваныч",
                    "22-СПО-ОИБАС-01",
                    "Информатика",
                    "Кафедра ИБ",
                    "Факультет ИТ",
                    "Зав. кафедры",
                    "89001234567",
                    "kaf@example.com",
                    "Декан",
                    "89007654321",
                    "faculty@example.com",
                )
            ),
        ],
    )

    response = client.get("/api/account/student", query_string={"user_id": "2001"})

    assert response.status_code == HTTPStatus.OK
    body = response.get_json()
    assert body["name"] == "Иванов Иван Иваныч"
    assert body["department_info"]["email"] == "kaf@example.com"


def test_get_student_account_missing_id(client):
    response = client.get("/api/account/student")
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_get_student_account_not_found(client, mock_db):
    mock_db(
        account_api,
        [
            QueryStep(fetchone=None),
        ],
    )

    response = client.get("/api/account/student", query_string={"user_id": "9999"})
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_get_teacher_account_success(client, mock_db):
    mock_db(
        account_api,
        [
            QueryStep(
                fetchone=(
                    "Петров Петр Петрович",
                    "Кафедра ИБ",
                    "Факультет ИТ",
                    "Зав. кафедры",
                    "89001234567",
                    "kaf@example.com",
                    "Декан",
                    "89007654321",
                    "faculty@example.com",
                    "22-СПО-ОИБАС-01, 22-СПО-ОИБАС-02",
                )
            ),
        ],
    )

    response = client.get("/api/account/teacher", query_string={"user_id": "501"})

    assert response.status_code == HTTPStatus.OK
    body = response.get_json()
    assert body["groups"] == "22-СПО-ОИБАС-01, 22-СПО-ОИБАС-02"
    assert body["faculty_info"]["dean"] == "Декан"


def test_get_teacher_account_missing_id(client):
    response = client.get("/api/account/teacher")
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_get_teacher_account_not_found(client, mock_db):
    mock_db(
        account_api,
        [
            QueryStep(fetchone=None),
        ],
    )

    response = client.get("/api/account/teacher", query_string={"user_id": "123"})
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_update_student_password_success(client, mock_db):
    connection = mock_db(
        account_api,
        [
            QueryStep(),
        ],
    )

    response = client.put(
        "/api/account/student/password",
        json={"user_id": 2001, "new_password": "NewPass123!"},
    )

    assert response.status_code == HTTPStatus.OK
    assert connection.committed is True
    assert "UPDATE авторизация SET пароль" in connection._cursor.executed[0][0]


def test_update_student_password_missing_fields(client):
    response = client.put("/api/account/student/password", json={"user_id": 1})
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_update_teacher_password_success(client, mock_db):
    connection = mock_db(
        account_api,
        [
            QueryStep(),
        ],
    )

    response = client.put(
        "/api/account/teacher/password",
        json={"user_id": 501, "new_password": "TeacherPass!"},
    )

    assert response.status_code == HTTPStatus.OK
    assert connection.committed is True
    assert "UPDATE авторизация SET пароль" in connection._cursor.executed[0][0]


def test_update_teacher_password_missing_fields(client):
    response = client.put("/api/account/teacher/password", json={"new_password": "123"})
    assert response.status_code == HTTPStatus.BAD_REQUEST

