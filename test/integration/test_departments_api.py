from http import HTTPStatus

from api import departments_api
from conftest import QueryStep


def test_get_departments(client, mock_db):
    mock_db(
        departments_api,
        [
            QueryStep(fetchall=[("Кафедра ИБ",), ("Кафедра ИС",)]),
        ],
    )

    response = client.get("/api/get_departments")
    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == ["Кафедра ИБ", "Кафедра ИС"]


def test_get_departments_list(client, mock_db):
    mock_db(
        departments_api,
        [
            QueryStep(
                description=[
                    "назв_каф",
                    "факультет",
                    "заведующий",
                    "должность_каф",
                    "почта_каф",
                    "тел_каф",
                ],
                fetchall=[
                    ("Кафедра ИБ", "ИТ", "Иванов", "Профессор", "dept@example.com", "89001234567"),
                ],
            )
        ],
    )

    response = client.get("/api/departments_list")
    assert response.status_code == HTTPStatus.OK
    body = response.get_json()
    assert body[0]["назв_каф"] == "Кафедра ИБ"


def test_add_department_invalid_phone(client):
    response = client.post(
        "/api/departments",
        json={
            "Назв_каф": "Кафедра ИБ",
            "Факультет": "ИТ",
            "Заведующий": "Иванов",
            "Должность_каф": "Профессор",
            "Почта_каф": "dept@example.com",
            "Тел_каф": "12-34",
        },
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_add_department_duplicate(client, mock_db):
    mock_db(
        departments_api,
        [
            QueryStep(fetchone=(1,)),
        ],
    )

    response = client.post(
        "/api/departments",
        json={
            "Назв_каф": "Кафедра ИБ",
            "Факультет": "ИТ",
            "Заведующий": "Иванов",
            "Должность_каф": "Профессор",
            "Почта_каф": "dept@example.com",
            "Тел_каф": "89001234567",
        },
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "уже существует" in response.get_json()["error"]


def test_add_department_success(client, mock_db):
    connection = mock_db(
        departments_api,
        [
            QueryStep(fetchone=(0,)),
            QueryStep(),
        ],
    )

    response = client.post(
        "/api/departments",
        json={
            "Назв_каф": "Кафедра ИБ",
            "Факультет": "ИТ",
            "Заведующий": "Иванов",
            "Должность_каф": "Профессор",
            "Почта_каф": "dept@example.com",
            "Тел_каф": "89001234567",
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert connection.committed is True
    assert "INSERT INTO кафедра" in connection._cursor.executed[1][0]


def test_update_department_invalid_email(client):
    response = client.put(
        "/api/departments/Кафедра ИБ",
        json={
            "Назв_каф": "Кафедра ИБ",
            "Факультет": "ИТ",
            "Заведующий": "Иванов",
            "Должность_каф": "Профессор",
            "Почта_каф": "invalid",
            "Тел_каф": "89001234567",
        },
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_update_department_success(client, mock_db):
    connection = mock_db(
        departments_api,
        [
            QueryStep(),
        ],
    )

    response = client.put(
        "/api/departments/Кафедра ИБ",
        json={
            "Назв_каф": "Кафедра ИБ",
            "Факультет": "ИТ",
            "Заведующий": "Иванов",
            "Должность_каф": "Профессор",
            "Почта_каф": "dept@example.com",
            "Тел_каф": "89001234567",
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert connection.committed is True
    assert "UPDATE кафедра" in connection._cursor.executed[0][0]


def test_delete_department_success(client, mock_db):
    connection = mock_db(
        departments_api,
        [
            QueryStep(),
        ],
    )

    response = client.delete("/api/departments/Кафедра ИБ")

    assert response.status_code == HTTPStatus.OK
    assert connection.committed is True
    assert "DELETE FROM кафедра" in connection._cursor.executed[0][0]


def test_get_faculties(client, mock_db):
    mock_db(
        departments_api,
        [
            QueryStep(
                description=[
                    "назв_факультет",
                    "декан",
                    "должность_ф",
                    "почта_ф",
                    "тел_ф",
                ],
                fetchall=[
                    ("Факультет ИТ", "Петров", "Профессор", "faculty@example.com", "89001234567"),
                ],
            ),
        ],
    )

    response = client.get("/api/faculties")
    assert response.status_code == HTTPStatus.OK
    assert response.get_json()[0]["назв_факультет"] == "Факультет ИТ"


def test_add_faculty_duplicate(client, mock_db):
    mock_db(
        departments_api,
        [
            QueryStep(fetchone=(1,)),
        ],
    )

    response = client.post(
        "/api/faculties",
        json={
            "Назв_факультет": "Факультет ИТ",
            "Декан": "Петров",
            "Должность_ф": "Профессор",
            "Почта_ф": "faculty@example.com",
            "Тел_ф": "89001234567",
        },
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "уже существует" in response.get_json()["error"]


def test_add_faculty_success(client, mock_db):
    connection = mock_db(
        departments_api,
        [
            QueryStep(fetchone=(0,)),
            QueryStep(),
        ],
    )

    response = client.post(
        "/api/faculties",
        json={
            "Назв_факультет": "Факультет ИТ",
            "Декан": "Петров",
            "Должность_ф": "Профессор",
            "Почта_ф": "faculty@example.com",
            "Тел_ф": "89001234567",
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert connection.committed is True
    assert "INSERT INTO факультет" in connection._cursor.executed[1][0]


def test_update_faculty_success(client, mock_db):
    connection = mock_db(
        departments_api,
        [
            QueryStep(),
        ],
    )

    response = client.put(
        "/api/faculties/Факультет ИТ",
        json={
            "Назв_факультет": "Факультет ИТ",
            "Декан": "Петров",
            "Должность_ф": "Профессор",
            "Почта_ф": "faculty@example.com",
            "Тел_ф": "89001234567",
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert connection.committed is True
    assert "UPDATE факультет" in connection._cursor.executed[0][0]


def test_delete_faculty_success(client, mock_db):
    connection = mock_db(
        departments_api,
        [
            QueryStep(),
        ],
    )

    response = client.delete("/api/faculties/Факультет ИТ")

    assert response.status_code == HTTPStatus.OK
    assert connection.committed is True
    assert "DELETE FROM факультет" in connection._cursor.executed[0][0]

