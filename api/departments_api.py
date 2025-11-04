from flask import Blueprint, request, jsonify
from models import get_db_connection
import re

departments_api = Blueprint('departments_api', __name__)

_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
def _is_valid_email(v: str) -> bool:
    return bool(_EMAIL_RE.match(v))

def _is_valid_phone(v: str) -> bool:
    return v.isdigit() and len(v) <= 11

@departments_api.route('/api/get_departments')
def get_departments():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT назв_каф FROM кафедра")
            departments = [row[0] for row in cursor.fetchall()]
            return jsonify(departments)
    except Exception as e:
        print(f"Error in get_departments: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@departments_api.route('/api/departments_list')
def get_departments_list():
    try:
        query = """
            SELECT назв_каф, факультет, заведующий, должность_каф, почта_каф, тел_каф
            FROM кафедра
            ORDER BY назв_каф
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            columns = [column[0] for column in cursor.description]
            results = []
            for row in cursor.fetchall():
                result = {}
                for i, value in enumerate(row):
                    result[columns[i]] = value
                results.append(result)
            return jsonify(results)
    except Exception as e:
        print(f"Error in get_departments: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@departments_api.route('/api/departments', methods=['POST'])
def add_department():
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        # basic format validation
        if data.get('Тел_каф') and not _is_valid_phone(str(data['Тел_каф']).strip()):
            return jsonify({'success': False, 'error': 'Телефон должен содержать только цифры (до 11)'}), 400
        if data.get('Почта_каф') and not _is_valid_email(str(data['Почта_каф']).strip()):
            return jsonify({'success': False, 'error': 'Неверный формат email'}), 400
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM кафедра WHERE назв_каф = %s", [data['Назв_каф']])
            if cursor.fetchone()[0] > 0:
                return jsonify({'success': False, 'error': 'Кафедра с таким названием уже существует'}), 400
            cursor.execute("""
                INSERT INTO кафедра (назв_каф, факультет, заведующий, должность_каф, почта_каф, тел_каф)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, [
                data['Назв_каф'],
                data['Факультет'],
                data['Заведующий'],
                data['Должность_каф'],
                data['Почта_каф'],
                data['Тел_каф']
            ])
            conn.commit()
            return jsonify({'success': True})
    except Exception as e:
        print(f"Error in add_department: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@departments_api.route('/api/departments/<department_name>', methods=['PUT'])
def update_department(department_name):
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        if data.get('Тел_каф') and not _is_valid_phone(str(data['Тел_каф']).strip()):
            return jsonify({'success': False, 'error': 'Телефон должен содержать только цифры (до 11)'}), 400
        if data.get('Почта_каф') and not _is_valid_email(str(data['Почта_каф']).strip()):
            return jsonify({'success': False, 'error': 'Неверный формат email'}), 400
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE кафедра 
                SET назв_каф = %s, факультет = %s, заведующий = %s, 
                    должность_каф = %s, почта_каф = %s, тел_каф = %s
                WHERE назв_каф = %s
            """, [
                data['Назв_каф'],
                data['Факультет'],
                data['Заведующий'],
                data['Должность_каф'],
                data['Почта_каф'],
                data['Тел_каф'],
                department_name
            ])
            conn.commit()
            return jsonify({'success': True})
    except Exception as e:
        print(f"Error in update_department: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@departments_api.route('/api/departments/<department_name>', methods=['DELETE'])
def delete_department(department_name):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM кафедра WHERE назв_каф = %s", [department_name])
            conn.commit()
            return jsonify({'success': True})
    except Exception as e:
        print(f"Error in delete_department: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@departments_api.route('/api/faculties')
def get_faculties():
    try:
        query = """
            SELECT назв_факультет, декан, должность_ф, почта_ф, тел_ф
            FROM факультет
            ORDER BY назв_факультет
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            columns = [column[0] for column in cursor.description]
            results = []
            for row in cursor.fetchall():
                result = {}
                for i, value in enumerate(row):
                    result[columns[i]] = value
                results.append(result)
            return jsonify(results)
    except Exception as e:
        print(f"Error in get_faculties: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@departments_api.route('/api/faculties', methods=['POST'])
def add_faculty():
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        if data.get('Тел_ф') and not _is_valid_phone(str(data['Тел_ф']).strip()):
            return jsonify({'success': False, 'error': 'Телефон должен содержать только цифры (до 11)'}), 400
        if data.get('Почта_ф') and not _is_valid_email(str(data['Почта_ф']).strip()):
            return jsonify({'success': False, 'error': 'Неверный формат email'}), 400
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM факультет WHERE назв_факультет = %s", [data['Назв_факультет']])
            if cursor.fetchone()[0] > 0:
                return jsonify({'success': False, 'error': 'Факультет с таким названием уже существует'}), 400
            cursor.execute("""
                INSERT INTO факультет (назв_факультет, декан, должность_ф, почта_ф, тел_ф)
                VALUES (%s, %s, %s, %s, %s)
            """, [
                data['Назв_факультет'],
                data['Декан'],
                data['Должность_ф'],
                data['Почта_ф'],
                data['Тел_ф']
            ])
            conn.commit()
            return jsonify({'success': True})
    except Exception as e:
        print(f"Error in add_faculty: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@departments_api.route('/api/faculties/<faculty_name>', methods=['PUT'])
def update_faculty(faculty_name):
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        if data.get('Тел_ф') and not _is_valid_phone(str(data['Тел_ф']).strip()):
            return jsonify({'success': False, 'error': 'Телефон должен содержать только цифры (до 11)'}), 400
        if data.get('Почта_ф') and not _is_valid_email(str(data['Почта_ф']).strip()):
            return jsonify({'success': False, 'error': 'Неверный формат email'}), 400

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE факультет 
                SET назв_факультет = %s, декан = %s, должность_ф = %s, 
                    почта_ф = %s, тел_ф = %s
                WHERE назв_факультет = %s
            """, [
                data['Назв_факультет'],
                data['Декан'],
                data['Должность_ф'],
                data['Почта_ф'],
                data['Тел_ф'],
                faculty_name
            ])
            conn.commit()
            return jsonify({'success': True})
    except Exception as e:
        print(f"Error in update_faculty: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@departments_api.route('/api/faculties/<faculty_name>', methods=['DELETE'])
def delete_faculty(faculty_name):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM факультет WHERE назв_факультет = %s", [faculty_name])
            conn.commit()
            return jsonify({'success': True})
    except Exception as e:
        print(f"Error in delete_faculty: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
