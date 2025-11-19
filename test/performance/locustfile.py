import os
from random import choice

from locust import HttpUser, between, task


class AcademicPortalUser(HttpUser):
    host = os.getenv("LOCUST_HOST", "http://localhost:5000")
    wait_time = between(0.01, 0.05)  # почти без ожидания


    # Используем реальные дисциплины и группы из БД
    _disciplines = ["Математика", "Программирование", "Физика", "История", "Химия"]
    _groups = ["22-ИСиП-01", "23-ИСиП-02", "24-СиСА-01", "24-СиСА-04"]

    # Преподаватели из БД (ID взяты из INSERT)
    _teachers = [3, 4, 6, 8]

    # Студенты с их группами
    _students = [
        {"name": "Комаров Кирилл Аркадьевич", "group": "22-ИСиП-01"},
        {"name": "Леон Сибрич Олегович", "group": "23-ИСиП-02"},
        {"name": "Морозова Анна Сергеевна", "group": "22-ИСиП-01"},
        {"name": "Антонов Антон Антонович", "group": "23-ИСиП-02"},
        {"name": "Иванов Иван Сергеевич", "group": "23-ИСиП-02"},
        {"name": "Петров Сергей Сергеевич", "group": "23-ИСиП-02"},
    ]

    def on_start(self):
        # Добавляем авторизацию через токен, если задан
        token = os.getenv("LOCUST_BEARER_TOKEN")
        if token:
            self.client.headers.update({"Authorization": f"Bearer {token}"})

    @task(3)
    def list_teachers(self):
        self.client.get(
            "/api/get_users",
            params={"table": "преподаватели", "fioField": "фио_преп"},
        )

    @task(3)
    def fetch_group_grades(self):
        discipline = choice(self._disciplines)
        group = choice(self._groups)
        self.client.get(
            "/api/grades/table",
            params={"discipline": discipline, "group": group},
        )

    @task(2)
    def fetch_expulsion_candidates(self):
        self.client.get("/api/expulsion")

    @task(1)
    def post_grade_snapshot(self):
        discipline = choice(self._disciplines)
        group = choice(self._groups)
        teacher_id = choice(self._teachers)

        # Выбираем случайного студента из этой группы
        students_in_group = [s for s in self._students if s["group"] == group]
        if not students_in_group:
            return
        student = choice(students_in_group)

        # Случайная оценка от 2 до 5
        grade_value = choice(["2", "3", "4", "5"])

        self.client.post(
            "/api/grades/save",
            json={
                "discipline": discipline,
                "group": group,
                "teacherId": teacher_id,
                "grades": [
                    {
                        "studentName": student["name"],
                        "grades": {"1": grade_value},
                    }
                ],
            },
        )

