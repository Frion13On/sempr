from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from auth import check_student_access

student_bp = Blueprint('student', __name__)

@student_bp.route('/student')
@login_required
def student_dashboard():
    if not check_student_access():
        flash('Доступ запрещен', 'error')
        return redirect(url_for('auth.login'))
    return render_template('student.html')

@student_bp.route('/student/debts')
@login_required
def student_debts():
    if not current_user.is_authenticated:
        flash('Доступ запрещен', 'error')
        return redirect(url_for('auth.login'))
    return render_template('debts.html')

@student_bp.route('/student/grades')
@login_required
def student_grades():
    if not current_user.is_authenticated:
        flash('Доступ запрещен', 'error')
        return redirect(url_for('auth.login'))
    return render_template('grades.html')

@student_bp.route('/account')
@login_required
def account():
    if not current_user.is_authenticated:
        flash('Доступ запрещен', 'error')
        return redirect(url_for('auth.login'))
    return render_template('account.html')

@student_bp.route('/expulsion')
@login_required
def expulsion_list():
    if not current_user.is_authenticated:
        flash('Доступ запрещен', 'error')
        return redirect(url_for('auth.login'))
    return render_template('expulsion.html')
