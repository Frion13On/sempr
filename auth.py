from flask import request, redirect, url_for, flash
from flask_login import login_user, current_user
from models import User, get_db_connection
from password_utils import verify_password, hash_password, is_password_hashed

def authenticate_user(login, password):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, роль, пароль FROM авторизация WHERE логин = %s", (login,))
        row = cursor.fetchone()
        if not row:
            return None, None

        auth_id, role_id, password_hash = row
        if not verify_password(password, password_hash):
            return None, None
        if not is_password_hashed(password_hash):
            new_hash = hash_password(password)
            cursor.execute("UPDATE авторизация SET пароль = %s WHERE id = %s", (new_hash, auth_id))
            conn.commit()

        student_id = None
        teacher_id = None

        if role_id == 1:
            cursor.execute("SELECT код_адм FROM администраторы WHERE user_id = %s", (auth_id,))
            cursor.fetchone()
        elif role_id == 2:
            cursor.execute("SELECT id_преп FROM преподаватели WHERE user_id = %s", (auth_id,))
            ref = cursor.fetchone()
            if ref:
                teacher_id = ref[0]
        elif role_id == 3:
            cursor.execute("SELECT id_студ FROM студенты WHERE user_id = %s", (auth_id,))
            ref = cursor.fetchone()
            if ref:
                student_id = ref[0]

        user = User(auth_id, role_id, student_id=student_id, teacher_id=teacher_id)
        login_user(user)
        return user, role_id

    except Exception as e:
        flash(f'Ошибка подключения к базе данных: {str(e)}', 'error')
        return None, None
    finally:
        if 'conn' in locals() and not conn.closed:
            conn.close()

def check_admin_access():
    return current_user.is_authenticated and current_user.role_id == 1

def check_teacher_access():
    return current_user.is_authenticated and current_user.role_id == 2

def check_student_access():
    return current_user.is_authenticated and current_user.role_id == 3

def require_admin():
    if not check_admin_access():
        flash('Доступ запрещен', 'error')
        return redirect(url_for('auth.login'))

def require_teacher():
    if not check_teacher_access():
        flash('Доступ запрещен', 'error')
        return redirect(url_for('auth.login'))

def require_student():
    if not check_student_access():
        flash('Доступ запрещен', 'error')
        return redirect(url_for('auth.login'))
