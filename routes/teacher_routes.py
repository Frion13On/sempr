from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from auth import check_teacher_access

teacher_bp = Blueprint('teacher', __name__)

@teacher_bp.route('/teacher')
@login_required
def teacher_dashboard():
    if not check_teacher_access():
        flash('Доступ запрещен', 'error')
        return redirect(url_for('auth.login'))
    return render_template('teacher.html')

@teacher_bp.route('/final/grades')
@login_required
def final_grades():
    if not check_teacher_access():
        flash('Доступ запрещен', 'error')
        return redirect(url_for('auth.login'))
    return render_template('fingrade.html')

@teacher_bp.route('/input/grades')
@login_required
def input_grades():
    if not check_teacher_access():
        flash('Доступ запрещен', 'error')
        return redirect(url_for('auth.login'))
    return render_template('inpgrades.html')

@teacher_bp.route('/exam/grades')
@login_required
def exam_grades():
    if not check_teacher_access():
        flash('Доступ запрещен. Эта страница доступна только для преподавателей.', 'error')
        return redirect(url_for('auth.login'))
    return render_template('exinpgrades.html', current_user=current_user)

@teacher_bp.route('/group/grades')
@login_required
def group_grades():
    if not current_user.is_authenticated:
        flash('Доступ запрещен', 'error')
        return redirect(url_for('auth.login'))
    return render_template('grgrades.html')
