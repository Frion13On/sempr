from http import HTTPStatus

from api import grades_api, users_api
from conftest import QueryStep


def test_admin_user_management_flow(client, mock_db):
    connection = mock_db(
        users_api,
        [
            QueryStep(fetchone=(0,)),  # add_user unique check
            QueryStep(),  # add_user insert
            QueryStep(  # get_users list
                description=["код_адм", "фио_адм", "логин", "пароль"],
                fetchall=[(1, "Администратор Тест", "admin_test", "secret")],
            ),
            QueryStep(fetchone=(0,)),  # update_user unique check
            QueryStep(),  # update_user update
            QueryStep(),  # delete_user delete
        ],
    )

    add_response = client.post(
        "/api/add_user",
        json={
            "table": "администраторы",
            "data": {
                "фио_адм": "Администратор Тест",
                "логин": "admin_test",
                "пароль": "secret123",
            },
        },
    )
    assert add_response.status_code == HTTPStatus.OK

    list_response = client.get(
        "/api/get_users",
        query_string={
            "table": "администраторы",
            "fioField": "фио_адм",
            "search": "",
        },
    )
    assert list_response.status_code == HTTPStatus.OK
    assert list_response.get_json()[0]["фио_адм"] == "Администратор Тест"

    update_response = client.put(
        "/api/update_user",
        json={
            "table": "администраторы",
            "idField": "код_адм",
            "id": 1,
            "data": {
                "фио_адм": "Администратор Обновленный",
                "логин": "admin_test",
                "пароль": "new_secret",
            },
        },
    )
    assert update_response.status_code == HTTPStatus.OK

    delete_response = client.delete(
        "/api/delete_user",
        json={
            "table": "администраторы",
            "idField": "код_адм",
            "id": 1,
        },
    )
    assert delete_response.status_code == HTTPStatus.OK

    executed_queries = [stmt for stmt, _ in connection._cursor.executed]
    assert executed_queries[0] == "SELECT COUNT(*) FROM администраторы WHERE логин = %s"
    assert any(
        stmt.startswith("SELECT COUNT(*) FROM администраторы WHERE логин = %s AND код_адм <> %s")
        for stmt in executed_queries
    )
    assert any("INSERT INTO администраторы" in stmt for stmt in executed_queries)
    assert any("UPDATE администраторы" in stmt for stmt in executed_queries[-2:])
    assert executed_queries[-1].startswith("DELETE FROM администраторы")


def test_teacher_grade_entry_flow(client, mock_db):
    connection = mock_db(
        grades_api,
        [
            QueryStep(fetchone=(3,)),  # количество занятий
            QueryStep(fetchone=(101,)),  # id_дисц
            QueryStep(
                fetchall=[
                    ("Иванов И.И.", "1", "4", "Петров П.П."),
                    ("Иванов И.И.", "2", "5", "Петров П.П."),
                ]
            ),
            QueryStep(fetchone=(101,)),  # save_grades discipline lookup
            QueryStep(fetchone=(2001,)),  # student id
            QueryStep(fetchone=(0,)),  # grade exists
            QueryStep(),  # insert grade
        ],
    )

    table_response = client.get(
        "/api/grades/table",
        query_string={"discipline": "Математика", "group": "ИБ-01"},
    )
    assert table_response.status_code == HTTPStatus.OK
    table_data = table_response.get_json()
    assert table_data["numberOfLessons"] == 3

    save_response = client.post(
        "/api/grades/save",
        json={
            "discipline": "Математика",
            "group": "ИБ-01",
            "teacherId": 501,
            "grades": [
                {
                    "studentName": "Иванов И.И.",
                    "grades": {"3": "5"},
                }
            ],
        },
    )
    assert save_response.status_code == HTTPStatus.OK
    assert connection.committed is True

    executed = connection._cursor.executed
    # last command should be insert
    assert "INSERT INTO электронный_журнал" in executed[-1][0]

