from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from auth import check_admin_access

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin')
@login_required
def admin_dashboard():
    if not check_admin_access():
        flash('Доступ запрещен', 'error')
        return redirect(url_for('auth.login'))
    return render_template('admin.html')

@admin_bp.route('/admin/manage')
@login_required
def admin_manage():
    if not check_admin_access():
        flash('Доступ запрещен', 'error')
        return redirect(url_for('auth.login'))
    return render_template('manage.html')
