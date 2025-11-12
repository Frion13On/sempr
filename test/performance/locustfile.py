import os
from random import choice

from locust import HttpUser, between, task


class AcademicPortalUser(HttpUser):
    host = os.getenv("LOCUST_HOST", "http://localhost:5000")
    wait_time = between(0.5, 2.0)

    _disciplines = ["Математика", "Физика", "Информатика"]
    _groups = ["ИБ-01", "ИБ-02", "ИБ-03"]

    def on_start(self):
        # Placeholder for authentication hook if API requires it.
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
        self.client.post(
            "/api/grades/save",
            json={
                "discipline": discipline,
                "group": group,
                "teacherId": 501,
                "grades": [
                    {
                        "studentName": "Иванов И.И.",
                        "grades": {"1": "5"},
                    }
                ],
            },
        )

