from http import HTTPStatus

from api import expulsion_api
from conftest import QueryStep


def test_get_expulsion_list(client, mock_db):
    mock_db(
        expulsion_api,
        [
            QueryStep(
                description=["id_студ", "ФИО", "название_группы", "Количество_долгов"],
                fetchall=[(1001, "Иванов И.И.", "Группа-1", 3)],
            )
        ],
    )

    response = client.get("/api/expulsion")

    assert response.status_code == HTTPStatus.OK
    body = response.get_json()
    assert isinstance(body, list)
    assert body[0]["ФИО"] == "Иванов И.И."


def test_expel_students_success(client, mock_db):
    connection = mock_db(
        expulsion_api,
        [
            QueryStep(),  # delete id 1001
            QueryStep(),  # delete id 1002
        ],
    )

    response = client.delete(
        "/api/expulsion",
        json={"student_ids": [1001, 1002]},
    )

    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == {"success": True}
    assert connection.committed is True
    executed = connection._cursor.executed
    assert len(executed) == 2
    assert all("DELETE FROM студенты" in stmt for stmt, _ in executed)


def test_expel_students_missing_payload(client):
    response = client.delete("/api/expulsion", json={"student_ids": []})
    assert response.status_code == HTTPStatus.BAD_REQUEST

