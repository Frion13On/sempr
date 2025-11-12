from http import HTTPStatus

from api import grades_api
from conftest import QueryStep


def test_get_student_debts_success(client, mock_db):
    mock_db(
        grades_api,
        [
            QueryStep(
                description=["DisciplineName", "ExamDate", "Grade"],
                fetchall=[("Математика", "2025-01-10", "2")],
            )
        ],
    )

    response = client.get(
        "/api/student/debts",
        query_string={"student_id": "2001"},
    )

    assert response.status_code == HTTPStatus.OK
    debts = response.get_json()
    assert debts[0]["DisciplineName"] == "Математика"


def test_get_student_debts_missing_id(client):
    response = client.get("/api/student/debts")
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_get_student_disciplines(client, mock_db):
    mock_db(
        grades_api,
        [
            QueryStep(fetchall=[("Математика",), ("Физика",)]),
        ],
    )

    response = client.get(
        "/api/student/disciplines",
        query_string={"student_id": "2001"},
    )

    assert response.status_code == HTTPStatus.OK
    assert set(response.get_json()) == {"Математика", "Физика"}


def test_get_student_grades_success(client, mock_db):
    mock_db(
        grades_api,
        [
            QueryStep(fetchone=(101,)),  # discipline id lookup
            QueryStep(
                fetchall=[
                    (1, "5"),
                    (2, "4"),
                    (3, "Н"),
                ]
            ),
        ],
    )

    response = client.get(
        "/api/student/grades",
        query_string={"student_id": "2001", "discipline": "Математика"},
    )

    assert response.status_code == HTTPStatus.OK
    body = response.get_json()
    assert body["stats"]["finalGrade"] == "4.50"
    assert body["stats"]["gradesCount"] == 2
    assert body["stats"]["absencesCount"] == 1
    assert {grade["LessonNumber"] for grade in body["grades"]} == {1, 2, 3}


def test_get_student_grades_missing_params(client):
    response = client.get("/api/student/grades")
    assert response.status_code == HTTPStatus.BAD_REQUEST
    body = response.get_json()
    assert body["success"] is False


def test_get_teacher_groups(client, mock_db):
    mock_db(
        grades_api,
        [
            QueryStep(fetchall=[("ИБ-01",), ("ИБ-02",)]),
        ],
    )

    response = client.get(
        "/api/teacher/groups",
        query_string={"teacher_id": "501"},
    )

    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == ["ИБ-01", "ИБ-02"]


def test_get_group_grades(client, mock_db):
    mock_db(
        grades_api,
        [
            QueryStep(
                fetchall=[
                    (
                        "Математика",
                        4.5,
                        3,
                    )
                ]
            )
        ],
    )

    response = client.get(
        "/api/group/grades",
        query_string={"group": "ИБ-01"},
    )

    assert response.status_code == HTTPStatus.OK
    body = response.get_json()
    assert body["groupName"] == "ИБ-01"
    assert body["grades"][0]["AverageGrade"] == "4.50"


def test_get_teacher_disciplines(client, mock_db):
    mock_db(
        grades_api,
        [
            QueryStep(fetchall=[("Математика",), ("Физика",)]),
        ],
    )

    response = client.get(
        "/api/teacher/disciplines",
        query_string={"teacher_id": "501"},
    )

    assert response.status_code == HTTPStatus.OK
    assert set(response.get_json()) == {"Математика", "Физика"}


def test_get_final_grades(client, mock_db):
    mock_db(
        grades_api,
        [
            QueryStep(
                fetchall=[
                    ("Иванов И.И.", 0, 10, 4.8),
                    ("Петров П.П.", 6, 10, 3.2),
                ]
            )
        ],
    )

    response = client.get(
        "/api/final/grades",
        query_string={"discipline": "Математика", "group": "ИБ-01"},
    )

    assert response.status_code == HTTPStatus.OK
    results = response.get_json()
    assert results[0]["finalGrade"] == "4.80"
    assert results[1]["finalGrade"] == "н/а"


def test_get_grades_table(client, mock_db):
    mock_db(
        grades_api,
        [
            QueryStep(fetchone=(3,)),  # количество занятий
            QueryStep(fetchone=(101,)),  # id дисциплины
            QueryStep(
                fetchall=[
                    ("Иванов И.И.", " 1 ", "5", "Петров П.П."),
                    ("Иванов И.И.", "2", "Н", "Петров П.П."),
                    ("Петров С.С.", None, None, None),
                ]
            ),
        ],
    )

    response = client.get(
        "/api/grades/table",
        query_string={"discipline": "Математика", "group": "ИБ-01"},
    )

    assert response.status_code == HTTPStatus.OK
    body = response.get_json()
    assert body["numberOfLessons"] == 3
    students = {student["name"]: student for student in body["students"]}
    assert students["Иванов И.И."]["grades"]["1"] == "5"
    assert students["Иванов И.И."]["absences"] == 1


def test_save_grades_success(client, mock_db):
    connection = mock_db(
        grades_api,
        [
            QueryStep(fetchone=(101,)),  # discipline id
            QueryStep(fetchone=(2001,)),  # student id
            QueryStep(fetchone=(0,)),  # grade exists
            QueryStep(),  # insert
        ],
    )

    response = client.post(
        "/api/grades/save",
        json={
            "discipline": "Математика",
            "group": "ИБ-01",
            "teacherId": 501,
            "grades": [
                {
                    "studentName": "Иванов И.И.",
                    "grades": {"1": "5"},
                }
            ],
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == {"success": True}
    assert connection.committed is True


def test_save_grades_invalid_value(client, mock_db):
    connection = mock_db(
        grades_api,
        [
            QueryStep(fetchone=(101,)),
            QueryStep(fetchone=(2001,)),
            QueryStep(fetchone=(0,)),
        ],
    )

    response = client.post(
        "/api/grades/save",
        json={
            "discipline": "Математика",
            "group": "ИБ-01",
            "teacherId": 501,
            "grades": [
                {
                    "studentName": "Иванов И.И.",
                    "grades": {"1": "10"},
                }
            ],
        },
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.get_json()["success"] is False
    assert connection.committed is False


def test_get_exam_grades_table(client, mock_db):
    mock_db(
        grades_api,
        [
            QueryStep(fetchone=(301,)),  # exam id
            QueryStep(
                fetchall=[
                    ("Иванов И.И.", "5"),
                    ("Петров П.П.", None),
                ]
            ),
        ],
    )

    response = client.get(
        "/api/exam/grades/table",
        query_string={"discipline": "Математика", "group": "ИБ-01"},
    )

    assert response.status_code == HTTPStatus.OK
    data = response.get_json()
    assert data["students"][1]["grade"] == ""


def test_save_exam_grades_success(client, mock_db):
    connection = mock_db(
        grades_api,
        [
            QueryStep(fetchone=(101,)),  # discipline id
            QueryStep(fetchone=(301,)),  # exam id
            QueryStep(fetchone=(2001,)),  # student id
            QueryStep(fetchone=(0,)),  # grade exists
            QueryStep(),  # insert
        ],
    )

    response = client.post(
        "/api/exam/grades/save",
        json={
            "discipline": "Математика",
            "group": "ИБ-01",
            "teacherId": 501,
            "grades": [
                {"studentName": "Иванов И.И.", "grade": "5"},
            ],
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == {"success": True}
    assert connection.committed is True


def test_save_exam_grades_invalid_value(client, mock_db):
    connection = mock_db(
        grades_api,
        [
            QueryStep(fetchone=(101,)),  # discipline id
            QueryStep(fetchone=(301,)),  # exam id
            QueryStep(fetchone=(2001,)),  # student id
            QueryStep(fetchone=(0,)),  # grade exists
        ],
    )

    response = client.post(
        "/api/exam/grades/save",
        json={
            "discipline": "Математика",
            "group": "ИБ-01",
            "teacherId": 501,
            "grades": [
                {"studentName": "Иванов И.И.", "grade": "10"},
            ],
        },
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.get_json()["success"] is False
    assert connection.committed is False

