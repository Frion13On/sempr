from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import get_db_connection
from password_utils import hash_password, is_strong_password
from api_access import require_roles, require_same_user_id

account_api = Blueprint('account_api', __name__)

@account_api.route('/api/account/student')
@login_required
@require_roles(3)
@require_same_user_id(param='user_id', user_attr='student_id', sources=('args',))
def get_student_account():
    try:
        student_id = request.args.get('user_id') or getattr(current_user, 'student_id', None)
        if not student_id:
            return jsonify({'success': False, 'error': 'Student ID not found in session'}), 400

        query = """
            SELECT s.фио_студ AS name, s.название_группы AS groups, 
                   sp.название_спец AS specialty, k.назв_каф AS department, 
                   f.назв_факультет AS faculty,
                   k.заведующий AS dept_head, k.тел_каф AS dept_phone, k.почта_каф AS dept_email,
                   f.декан AS faculty_dean, f.тел_ф AS faculty_phone, f.почта_ф AS faculty_email
            FROM студенты s
            LEFT JOIN группы g ON s.название_группы = g.название_группы 
            LEFT JOIN специальности sp ON g.специальность = sp.id_спец
            LEFT JOIN кафедра k ON sp.кафедра = k.назв_каф 
            LEFT JOIN факультет f ON k.факультет = f.назв_факультет 
            WHERE s.id_студ = %s
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, [student_id])
            row = cursor.fetchone()
            if not row:
                return jsonify({'success': False, 'error': 'Student not found'}), 404
            result = {
                'name': row[0],
                'groups': row[1],
                'specialty': row[2],
                'department': row[3],
                'faculty': row[4],
                'department_info': {
                    'head': row[5],
                    'phone': row[6],
                    'email': row[7]
                },
                'faculty_info': {
                    'dean': row[8],
                    'phone': row[9],
                    'email': row[10]
                }
            }
            return jsonify(result)
    except Exception as e:
        print(f"Error in get_student_account: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@account_api.route('/api/account/teacher')
@login_required
@require_roles(2)
@require_same_user_id(param='user_id', user_attr='teacher_id', sources=('args',))
def get_teacher_account():
    try:
        teacher_id = request.args.get('user_id') or getattr(current_user, 'teacher_id', None)
        if not teacher_id:
            return jsonify({'success': False, 'error': 'Teacher ID not found in session'}), 400
        query = """
            SELECT t.фио_преп AS name, k.назв_каф AS department, 
                   f.назв_факультет AS faculty,
                   k.заведующий AS dept_head, k.тел_каф AS dept_phone, k.почта_каф AS dept_email,
                   f.декан AS faculty_dean, f.тел_ф AS faculty_phone, f.почта_ф AS faculty_email,
                   STRING_AGG(g.название_группы, ', ') AS groups
            FROM преподаватели t
            LEFT JOIN кафедра k ON t.кафедра = k.назв_каф 
            LEFT JOIN факультет f ON k.факультет = f.назв_факультет
            LEFT JOIN группы g ON g.куратор = t.id_преп
            WHERE t.id_преп = %s
            GROUP BY t.фио_преп, k.назв_каф, f.назв_факультет, k.заведующий, k.тел_каф, k.почта_каф,
                     f.декан, f.тел_ф, f.почта_ф
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, [teacher_id])
            row = cursor.fetchone()
            if not row:
                return jsonify({'success': False, 'error': 'Teacher not found'}), 404
            result = {
                'name': row[0],
                'groups': row[9] or 'Нет курируемых групп',
                'department': row[1],
                'faculty': row[2],
                'department_info': {
                    'head': row[3],
                    'phone': row[4],
                    'email': row[5]
                },
                'faculty_info': {
                    'dean': row[6],
                    'phone': row[7],
                    'email': row[8]
                }
            }
            return jsonify(result)
    except Exception as e:
        print(f"Error in get_teacher_account: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@account_api.route('/api/account/student/password', methods=['PUT'])
@login_required
@require_roles(3)
@require_same_user_id(param='user_id', user_attr='student_id', sources=('json',))
def update_student_password():
    try:
        data = request.json
        if not data or 'user_id' not in data or 'new_password' not in data:
            return jsonify({'success': False, 'error': 'Missing required data'}), 400
        ok, err = is_strong_password(str(data['new_password']))
        if not ok:
            return jsonify({'success': False, 'error': err}), 400
        password_hash = hash_password(data['new_password'])
        query = "UPDATE авторизация SET пароль = %s WHERE id = (SELECT user_id FROM студенты WHERE id_студ = %s)"
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, [password_hash, data['user_id']])
            conn.commit()
            return jsonify({'success': True})
    except Exception as e:
        print(f"Error in update_student_password: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@account_api.route('/api/account/teacher/password', methods=['PUT'])
@login_required
@require_roles(2)
@require_same_user_id(param='user_id', user_attr='teacher_id', sources=('json',))
def update_teacher_password():
    try:
        data = request.json
        if not data or 'user_id' not in data or 'new_password' not in data:
            return jsonify({'success': False, 'error': 'Missing required data'}), 400
        ok, err = is_strong_password(str(data['new_password']))
        if not ok:
            return jsonify({'success': False, 'error': err}), 400
        password_hash = hash_password(data['new_password'])
        query = "UPDATE авторизация SET пароль = %s WHERE id = (SELECT user_id FROM преподаватели WHERE id_преп = %s)"
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, [password_hash, data['user_id']])
            conn.commit()
            return jsonify({'success': True})
    except Exception as e:
        print(f"Error in update_teacher_password: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
