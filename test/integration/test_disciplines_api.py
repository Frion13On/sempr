from http import HTTPStatus

from api import disciplines_api
from conftest import QueryStep


def test_get_disciplines_with_search(client, mock_db):
    mock_db(
        disciplines_api,
        [
            QueryStep(
                description=["id_дисц", "название", "количество_занятий"],
                fetchall=[(1, "Математика", 30)],
            )
        ],
    )

    response = client.get("/api/disciplines", query_string={"search": "Мат"})
    assert response.status_code == HTTPStatus.OK
    body = response.get_json()
    assert body[0]["название"] == "Математика"


def test_add_discipline_success(client, mock_db):
    connection = mock_db(
        disciplines_api,
        [
            QueryStep(),
        ],
    )

    response = client.post(
        "/api/disciplines",
        json={"Название": "Физика", "Количество_занятий": 20},
    )

    assert response.status_code == HTTPStatus.OK
    assert connection.committed is True
    assert "INSERT INTO дисциплина" in connection._cursor.executed[0][0]


def test_update_discipline_missing_body(client):
    response = client.put(
        "/api/disciplines/1",
        data="null",
        content_type="application/json",
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_update_discipline_success(client, mock_db):
    connection = mock_db(
        disciplines_api,
        [
            QueryStep(),
        ],
    )

    response = client.put(
        "/api/disciplines/5",
        json={"Название": "Информатика", "Количество_занятий": 16},
    )

    assert response.status_code == HTTPStatus.OK
    assert connection.committed is True
    assert "UPDATE дисциплина" in connection._cursor.executed[0][0]


def test_delete_discipline_success(client, mock_db):
    connection = mock_db(
        disciplines_api,
        [
            QueryStep(),
        ],
    )

    response = client.delete("/api/disciplines/3")

    assert response.status_code == HTTPStatus.OK
    assert connection.committed is True
    assert "DELETE FROM дисциплина" in connection._cursor.executed[0][0]


def test_get_discipline_assignments(client, mock_db):
    mock_db(
        disciplines_api,
        [
            QueryStep(
                fetchall=[("Иванов И.И.", "Математика"), ("Петров П.П.", "Физика")],
            ),
        ],
    )

    response = client.get("/api/discipline-assignments", query_string={"search": "Ив"})
    assert response.status_code == HTTPStatus.OK
    body = response.get_json()
    assert body[0]["ФИО_преп"] == "Иванов И.И."


def test_assign_discipline_missing_data(client):
    response = client.post("/api/discipline-assignments", json={"ФИО_преп": "Иванов"})
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_assign_discipline_not_found(client, mock_db):
    mock_db(
        disciplines_api,
        [
            QueryStep(fetchone=None),  # teacher lookup
        ],
    )

    response = client.post(
        "/api/discipline-assignments",
        json={"ФИО_преп": "Неизвестный", "Название": "Математика"},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND


def test_assign_discipline_success(client, mock_db):
    connection = mock_db(
        disciplines_api,
        [
            QueryStep(fetchone=(10,)),  # teacher id
            QueryStep(fetchone=(5,)),  # discipline id
            QueryStep(),  # insert
        ],
    )

    response = client.post(
        "/api/discipline-assignments",
        json={"ФИО_преп": "Иванов И.И.", "Название": "Математика"},
    )

    assert response.status_code == HTTPStatus.OK
    assert connection.committed is True
    assert "INSERT INTO дисц_преп" in connection._cursor.executed[-1][0]


def test_remove_assignment_missing_data(client):
    response = client.delete("/api/discipline-assignments", json={"ФИО_преп": "Иванов"})
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_remove_assignment_success(client, mock_db):
    connection = mock_db(
        disciplines_api,
        [
            QueryStep(),
        ],
    )

    response = client.delete(
        "/api/discipline-assignments",
        json={"ФИО_преп": "Иванов И.И.", "Название": "Математика"},
    )

    assert response.status_code == HTTPStatus.OK
    assert connection.committed is True
    assert "DELETE FROM дисц_преп" in connection._cursor.executed[0][0]


def test_get_teachers(client, mock_db):
    mock_db(
        disciplines_api,
        [
            QueryStep(fetchall=[("Иванов И.И.",), ("Петров П.П.",)]),
        ],
    )

    response = client.get("/api/teachers")
    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == ["Иванов И.И.", "Петров П.П."]

