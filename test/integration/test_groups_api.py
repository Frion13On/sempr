from http import HTTPStatus

from api import groups_api
from conftest import QueryStep


def test_get_groups(client, mock_db):
    mock_db(
        groups_api,
        [
            QueryStep(
                description=[
                    "название_группы",
                    "Специальность",
                    "курс",
                    "Куратор",
                ],
                fetchall=[("ИБ-01", "Информатика", 1, "Иванов И.И.")],
            )
        ],
    )

    response = client.get("/api/groups", query_string={"search": "ИБ"})
    assert response.status_code == HTTPStatus.OK
    assert response.get_json()[0]["Куратор"] == "Иванов И.И."


def test_add_group_missing_field(client):
    response = client.post(
        "/api/groups",
        json={
            "Название_группы": "ИБ-01",
            "Специальность": "Информатика",
            "Курс": 1,
        },
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_add_group_duplicate(client, mock_db):
    mock_db(
        groups_api,
        [
            QueryStep(fetchone=(1,)),  # group count
        ],
    )

    response = client.post(
        "/api/groups",
        json={
            "Название_группы": "ИБ-01",
            "Специальность": "Информатика",
            "Курс": 1,
            "Куратор": "Иванов И.И.",
        },
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "уже существует" in response.get_json()["error"]


def test_add_group_specialty_not_found(client, mock_db):
    mock_db(
        groups_api,
        [
            QueryStep(fetchone=(0,)),  # group count
            QueryStep(fetchone=None),  # specialty not found
        ],
    )

    response = client.post(
        "/api/groups",
        json={
            "Название_группы": "ИБ-02",
            "Специальность": "Неизвестная",
            "Курс": 1,
            "Куратор": "Иванов И.И.",
        },
    )

    assert response.status_code == HTTPStatus.NOT_FOUND


def test_add_group_success(client, mock_db):
    connection = mock_db(
        groups_api,
        [
            QueryStep(fetchone=(0,)),  # count
            QueryStep(fetchone=(5,)),  # specialty id
            QueryStep(fetchone=(10,)),  # curator id
            QueryStep(),  # insert
        ],
    )

    response = client.post(
        "/api/groups",
        json={
            "Название_группы": "ИБ-03",
            "Специальность": "Информатика",
            "Курс": 2,
            "Куратор": "Иванов И.И.",
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert connection.committed is True


def test_update_group_success(client, mock_db):
    connection = mock_db(
        groups_api,
        [
            QueryStep(fetchone=(5,)),  # specialty id
            QueryStep(fetchone=(10,)),  # curator id
            QueryStep(),  # update
        ],
    )

    response = client.put(
        "/api/groups/ИБ-03",
        json={
            "Специальность": "Информатика",
            "Курс": 3,
            "Куратор": "Иванов И.И.",
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert connection.committed is True
    assert "UPDATE группы" in connection._cursor.executed[-1][0]


def test_delete_group_success(client, mock_db):
    connection = mock_db(
        groups_api,
        [
            QueryStep(),
        ],
    )

    response = client.delete("/api/groups/ИБ-03")

    assert response.status_code == HTTPStatus.OK
    assert connection.committed is True
    assert "DELETE FROM группы" in connection._cursor.executed[0][0]

