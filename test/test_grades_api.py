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
            QueryStep(fetchone=(101,)), 
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

                fetchall=[(1,)],
            ),
            QueryStep(
                fetchall=[(10, "Математика")],
            ),
            QueryStep(
                fetchall=[(1, "4.5"), (1, "4.5"), (1, "4.5")],
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


def test_get_group_grades_excludes_low_attendance_students(client, mock_db):
    mock_db(
        grades_api,
        [
            QueryStep(
                fetchall=[(1,), (2,)],
            ),
            QueryStep(
                fetchall=[(10, "Математика")],
            ),
            QueryStep(
                fetchall=[
                    (1, "4.5"),
                    (1, "4.5"),
                    (1, "4.5"),
                    (2, "5"),
                    (2, "5"),
                    (2, "5"),
                    (2, "Н"),
                    (2, "Н"),
                    (2, "Н"),
                    (2, "Н"),
                ],
            ),
        ],
    )

    response = client.get(
        "/api/group/grades",
        query_string={"group": "ИБ-01"},
    )

    assert response.status_code == HTTPStatus.OK
    body = response.get_json()
    assert body["grades"][0]["AverageGrade"] == "4.50"
    assert body["grades"][0]["SuccessRate"] == "50.0"


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
                    ("Иванов Иван Иваныч", 0, 10, 4.8),
                    ("Петров Петр Петрович", 6, 10, 3.2),
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
            QueryStep(fetchone=(3,)), 
            QueryStep(fetchone=(101,)),
            QueryStep(
                fetchall=[
                    ("Иванов Иван Иваныч", " 1 ", "5", "Петров Петр Петрович"),
                    ("Иванов Иван Иваныч", "2", "Н", "Петров Петр Петрович"),
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
    assert students["Иванов Иван Иваныч"]["grades"]["1"] == "5"
    assert students["Иванов Иван Иваныч"]["absences"] == 1


def test_save_grades_success(client, mock_db):
    connection = mock_db(
        grades_api,
        [
            QueryStep(fetchone=(101,)),  
            QueryStep(fetchone=(2001,)),  
            QueryStep(fetchone=(0,)),  
            QueryStep(), 
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
                    "studentName": "Иванов Иван Иваныч",
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
                    "studentName": "Иванов Иван Иваныч",
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
                    ("Иванов Иван Иваныч", "5"),
                    ("Петров Петр Петрович", None),
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
                {"studentName": "Иванов Иван Иваныч", "grade": "5"},
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
                {"studentName": "Иванов Иван Иваныч", "grade": "10"},
            ],
        },
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.get_json()["success"] is False
    assert connection.committed is False


def test_get_group_rating_success(client, mock_db):
    mock_db(
        grades_api,
        [
            QueryStep(
                fetchall=[
                    ("Иванов Иван Иваныч", 4.8),
                    ("Петров Петр Петрович", 4.5),
                    ("Сидоров Сидор Сидорович", None),
                ]
            )
        ],
    )

    response = client.get(
        "/api/group/rating",
        query_string={"group": "ИБ-01", "discipline": "Математика"},
    )

    assert response.status_code == HTTPStatus.OK
    body = response.get_json()
    assert body["group"] == "ИБ-01"
    assert body["discipline"] == "Математика"
    assert len(body["rating"]) == 2
    assert body["rating"][0]["place"] == 1
    assert body["rating"][0]["studentName"] == "Иванов Иван Иваныч"
    assert body["rating"][0]["averageGrade"] == "4.80"
    assert body["rating"][1]["place"] == 2
    assert body["rating"][1]["studentName"] == "Петров Петр Петрович"
    assert body["rating"][1]["averageGrade"] == "4.50"


def test_get_group_rating_missing_params(client):
    response = client.get("/api/group/rating", query_string={"group": "ИБ-01"})
    assert response.status_code == HTTPStatus.BAD_REQUEST
    body = response.get_json()
    assert body["success"] is False
    assert "Missing required parameters" in body["error"]

    response = client.get("/api/group/rating", query_string={"discipline": "Математика"})
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_get_group_rating_empty_result(client, mock_db):
    mock_db(
        grades_api,
        [
            QueryStep(fetchall=[])
        ],
    )

    response = client.get(
        "/api/group/rating",
        query_string={"group": "ИБ-01", "discipline": "Математика"},
    )

    assert response.status_code == HTTPStatus.OK
    body = response.get_json()
    assert body["rating"] == []


def test_get_group_rating_all_students_no_grades(client, mock_db):
    """Test when students have no grades (all None)"""
    mock_db(
        grades_api,
        [
            QueryStep(
                fetchall=[
                    ("Иванов Иван Иваныч", None),
                    ("Петров Петр Петрович", None),
                ]
            )
        ],
    )

    response = client.get(
        "/api/group/rating",
        query_string={"group": "ИБ-01", "discipline": "Математика"},
    )

    assert response.status_code == HTTPStatus.OK
    body = response.get_json()
    assert body["rating"] == []

