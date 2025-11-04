from flask import request, redirect, url_for, flash
from flask_login import login_user, current_user
import psycopg2
import os
from models import User, get_db_connection, users

def authenticate_user(login, password):
    """Аутентификация пользователя"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """ SELECT RoleID, StudentID FROM 
        (SELECT логин, пароль, NULL AS StudentID, 1 AS RoleID FROM администраторы UNION
        SELECT логин, пароль, id_преп AS StudentID, 2 AS RoleID FROM преподаватели UNION 
        SELECT логин, пароль, id_студ AS StudentID, 3 AS RoleID FROM студенты) AS Users
        WHERE логин = %s AND пароль = %s"""   
        
        cursor.execute(query, (login, password))
        result = cursor.fetchone()
        
        if result:
            role_id, student_id = result
            user = User(login, role_id, student_id)
            login_user(user)
            return user, role_id
        else:
            return None, None
            
    except Exception as e:
        flash(f'Ошибка подключения к базе данных: {str(e)}', 'error')
        return None, None
    finally:
        if 'conn' in locals():
            conn.close()

def check_admin_access():
    """Проверка доступа администратора"""
    return current_user.is_authenticated and current_user.role_id == 1

def check_teacher_access():
    """Проверка доступа преподавателя"""
    return current_user.is_authenticated and current_user.role_id == 2

def check_student_access():
    """Проверка доступа студента"""
    return current_user.is_authenticated and current_user.role_id == 3

def require_admin():
    """Декоратор для проверки прав администратора"""
    if not check_admin_access():
        flash('Доступ запрещен', 'error')
        return redirect(url_for('login'))

def require_teacher():
    """Декоратор для проверки прав преподавателя"""
    if not check_teacher_access():
        flash('Доступ запрещен', 'error')
        return redirect(url_for('login'))

def require_student():
    """Декоратор для проверки прав студента"""
    if not check_student_access():
        flash('Доступ запрещен', 'error')
        return redirect(url_for('login'))
