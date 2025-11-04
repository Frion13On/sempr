from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import logout_user, current_user
from models import users
from auth import authenticate_user

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_name = request.form.get('login')
        password = request.form.get('password')
        
        user, role_id = authenticate_user(login_name, password)
        
        if user and role_id:
            if role_id == 1:
                return redirect(url_for('admin.admin_dashboard'))
            elif role_id == 2:
                return redirect(url_for('teacher.teacher_dashboard'))
            elif role_id == 3:
                return redirect(url_for('student.student_dashboard'))
        else:
            flash('Неверный логин или пароль', 'error')
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    if current_user.is_authenticated:
        users.pop(current_user.id, None)
    logout_user()
    return redirect(url_for('auth.login'))
