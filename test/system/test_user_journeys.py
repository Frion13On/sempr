from http import HTTPStatus

from api import grades_api, users_api
from conftest import QueryStep


def test_admin_user_management_flow(client, mock_db):
    connection = mock_db(
        users_api,
        [
            QueryStep(fetchone=(0,)),   # add_user: проверка логина в авторизация
            QueryStep(fetchone=(1,)),   # add_user: INSERT авторизация RETURNING id
            QueryStep(),                 # add_user: INSERT администраторы
            QueryStep(
                description=["код_адм", "фио_адм", "логин", "пароль"],
                fetchall=[(1, "Администратор Тест", "admin_test", "secret")],
            ),
            QueryStep(fetchone=(1,)),   # update_user: user_id из администраторы
            QueryStep(fetchone=(0,)),   # update_user: проверка логина в авторизация
            QueryStep(),                 # update_user: UPDATE авторизация
            QueryStep(),                 # update_user: UPDATE администраторы
            QueryStep(fetchone=(1,)),   # delete_user: user_id
            QueryStep(),                 # delete_user: DELETE администраторы
            QueryStep(),                 # delete_user: DELETE авторизация
        ],
    )

    add_response = client.post(
        "/api/add_user",
        json={
            "table": "администраторы",
            "data": {
                "фио_адм": "Администратор Тест",
                "логин": "admin_test",
                "пароль": "Secret123!",
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
                "пароль": "New_secret1!",
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
    assert executed_queries[0] == "SELECT COUNT(*) FROM авторизация WHERE логин = %s"
    assert any("SELECT COUNT(*) FROM авторизация" in stmt and "AND id <> %s" in stmt for stmt in executed_queries)
    assert any("INSERT INTO администраторы" in stmt for stmt in executed_queries)
    assert any("UPDATE администраторы" in stmt for stmt in executed_queries)
    assert any("DELETE FROM администраторы" in stmt for stmt in executed_queries)
    assert any("DELETE FROM авторизация" in stmt for stmt in executed_queries)


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

