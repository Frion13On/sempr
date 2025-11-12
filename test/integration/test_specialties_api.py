from http import HTTPStatus

from api import specialties_api
from conftest import QueryStep


def test_get_specialties(client, mock_db):
    mock_db(
        specialties_api,
        [
            QueryStep(
                description=["id_спец", "название_спец", "уровень_образования", "кафедра"],
                fetchall=[("IB01", "Информатика", "Бакалавр", "Кафедра ИБ")],
            ),
        ],
    )

    response = client.get("/api/specialties", query_string={"search": "Ин"})
    assert response.status_code == HTTPStatus.OK
    assert response.get_json()[0]["название_спец"] == "Информатика"


def test_get_specialty_assignments(client, mock_db):
    mock_db(
        specialties_api,
        [
            QueryStep(
                fetchall=[("Информатика", "Математика"), ("Информатика", "Физика")],
            )
        ],
    )

    response = client.get("/api/specialty-assignments", query_string={"search": "Ин"})
    assert response.status_code == HTTPStatus.OK
    assert response.get_json()[0]["Название_спец"] == "Информатика"


def test_add_specialty_duplicate(client, mock_db):
    mock_db(
        specialties_api,
        [
            QueryStep(fetchone=(1,)),
        ],
    )

    response = client.post(
        "/api/specialties",
        json={
            "ID_спец": "IB01",
            "Название_спец": "Информатика",
            "Уровень_образования": "Бакалавр",
            "Кафедра": "Кафедра ИБ",
        },
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "уже существует" in response.get_json()["error"]


def test_add_specialty_success(client, mock_db):
    connection = mock_db(
        specialties_api,
        [
            QueryStep(fetchone=(0,)),
            QueryStep(),
        ],
    )

    response = client.post(
        "/api/specialties",
        json={
            "ID_спец": "IB02",
            "Название_спец": "Кибербезопасность",
            "Уровень_образования": "Магистр",
            "Кафедра": "Кафедра ИБ",
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert connection.committed is True
    assert "INSERT INTO специальности" in connection._cursor.executed[1][0]


def test_update_specialty_success(client, mock_db):
    connection = mock_db(
        specialties_api,
        [
            QueryStep(),
        ],
    )

    response = client.put(
        "/api/specialties/IB02",
        json={
            "ID_спец": "IB02",
            "Название_спец": "Кибербезопасность",
            "Уровень_образования": "Магистр",
            "Кафедра": "Кафедра ИБ",
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert connection.committed is True
    assert "UPDATE специальности" in connection._cursor.executed[0][0]


def test_delete_specialty_success(client, mock_db):
    connection = mock_db(
        specialties_api,
        [
            QueryStep(),
        ],
    )

    response = client.delete("/api/specialties/IB02")

    assert response.status_code == HTTPStatus.OK
    assert connection.committed is True
    assert "DELETE FROM специальности" in connection._cursor.executed[0][0]


def test_assign_discipline_missing_data(client):
    response = client.post("/api/specialty-assignments", json={"Название_спец": "Информатика"})
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_assign_discipline_specialty_not_found(client, mock_db):
    mock_db(
        specialties_api,
        [
            QueryStep(fetchone=None),
        ],
    )

    response = client.post(
        "/api/specialty-assignments",
        json={"Название_спец": "Неизвестная", "Название": "Математика"},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND


def test_assign_discipline_success(client, mock_db):
    connection = mock_db(
        specialties_api,
        [
            QueryStep(fetchone=("IB02",)),  # specialty id
            QueryStep(fetchone=(10,)),  # discipline id
            QueryStep(),  # insert
        ],
    )

    response = client.post(
        "/api/specialty-assignments",
        json={"Название_спец": "Кибербезопасность", "Название": "Математика"},
    )

    assert response.status_code == HTTPStatus.OK
    assert connection.committed is True
    assert "INSERT INTO спец_дисц" in connection._cursor.executed[-1][0]


def test_remove_specialty_assignment_success(client, mock_db):
    connection = mock_db(
        specialties_api,
        [
            QueryStep(),
        ],
    )

    response = client.delete(
        "/api/specialty-assignments",
        json={"Название_спец": "Кибербезопасность", "Название": "Математика"},
    )

    assert response.status_code == HTTPStatus.OK
    assert connection.committed is True
    assert "DELETE FROM спец_дисц" in connection._cursor.executed[0][0]

