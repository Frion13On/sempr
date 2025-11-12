from http import HTTPStatus

from api import exams_api
from conftest import QueryStep


def test_get_exams(client, mock_db):
    mock_db(
        exams_api,
        [
            QueryStep(
                description=[
                    "id_экзамен",
                    "Дисциплина",
                    "Преподаватель",
                    "название_группы",
                    "дата_экзамена",
                ],
                fetchall=[
                    (10, "Математика", "Иванов И.И.", "ИБ-01", "2025-01-15"),
                ],
            )
        ],
    )

    response = client.get("/api/exams", query_string={"search": "ИБ"})
    assert response.status_code == HTTPStatus.OK
    body = response.get_json()
    assert body[0]["Преподаватель"] == "Иванов И.И."


def test_add_exam_missing_body(client):
    response = client.post(
        "/api/exams",
        data="null",
        content_type="application/json",
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_add_exam_discipline_not_found(client, mock_db):
    mock_db(
        exams_api,
        [
            QueryStep(fetchone=None),
        ],
    )

    response = client.post(
        "/api/exams",
        json={
            "Дисциплина": "Неизвестная",
            "Преподаватель": "Иванов И.И.",
            "Название_группы": "ИБ-01",
            "Дата_экзамена": "2025-01-15",
        },
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert "Дисциплина" in response.get_json()["error"]


def test_add_exam_teacher_not_found(client, mock_db):
    mock_db(
        exams_api,
        [
            QueryStep(fetchone=(1,)),  # discipline id
            QueryStep(fetchone=None),  # teacher not found
        ],
    )

    response = client.post(
        "/api/exams",
        json={
            "Дисциплина": "Математика",
            "Преподаватель": "Неизвестный",
            "Название_группы": "ИБ-01",
            "Дата_экзамена": "2025-01-15",
        },
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert "Преподаватель" in response.get_json()["error"]


def test_add_exam_success(client, mock_db):
    connection = mock_db(
        exams_api,
        [
            QueryStep(fetchone=(1,)),  # discipline id
            QueryStep(fetchone=(2,)),  # teacher id
            QueryStep(),  # insert
        ],
    )

    response = client.post(
        "/api/exams",
        json={
            "Дисциплина": "Математика",
            "Преподаватель": "Иванов И.И.",
            "Название_группы": "ИБ-01",
            "Дата_экзамена": "2025-01-15",
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert connection.committed is True


def test_update_exam_success(client, mock_db):
    connection = mock_db(
        exams_api,
        [
            QueryStep(fetchone=(1,)),  # discipline id
            QueryStep(fetchone=(2,)),  # teacher id
            QueryStep(),  # update
        ],
    )

    response = client.put(
        "/api/exams/10",
        json={
            "Дисциплина": "Математика",
            "Преподаватель": "Иванов И.И.",
            "Название_группы": "ИБ-01",
            "Дата_экзамена": "2025-01-20",
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert connection.committed is True
    assert "UPDATE экзамены" in connection._cursor.executed[-1][0]


def test_delete_exam_success(client, mock_db):
    connection = mock_db(
        exams_api,
        [
            QueryStep(),
        ],
    )

    response = client.delete("/api/exams/10")

    assert response.status_code == HTTPStatus.OK
    assert connection.committed is True
    assert "DELETE FROM экзамены" in connection._cursor.executed[0][0]

