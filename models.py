from flask_login import UserMixin
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

users = {}

class User(UserMixin):
    def __init__(self, id, role_id, student_id=None, teacher_id=None):
        self.id = id
        self.role_id = role_id
        self.student_id = student_id
        self.teacher_id = teacher_id
        users[id] = self

    def get_id(self):
        return str(self.id)

def get_db_connection():
    """Создает подключение к базе данных PostgreSQL"""
    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        return conn
    except Exception as e:
        print(f"Database connection error: {str(e)}")
        raise

def get_user_by_id(user_id):
    """Получает пользователя по ID"""
    return users.get(user_id)
