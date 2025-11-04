from flask import Blueprint, request, jsonify
from models import get_db_connection
from datetime import datetime
import re
import psycopg2
from psycopg2 import errors

users_api = Blueprint('users_api', __name__)

# Simple validators
_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
def _is_valid_email(v: str) -> bool:
    return bool(_EMAIL_RE.match(v))

def _is_valid_phone(v: str) -> bool:
    return v.isdigit() and len(v) <= 11

_ALLOWED_FIELDS = {
    'администраторы': {'фио_адм', 'логин', 'пароль'},
    'преподаватели': {'фио_преп', 'логин', 'пароль', 'пол', 'дата_рождения', 'телефон', 'почта', 'должность', 'кафедра'},
    'студенты': {'фио_студ', 'логин', 'пароль', 'пол', 'дата_рождения', 'телефон', 'почта', 'название_группы'}
}

def _validate_and_filter_user_payload(table: str, payload: dict):
    if table not in _ALLOWED_FIELDS:
        return False, 'Invalid table name', None
    allowed = _ALLOWED_FIELDS[table]
    data = {k: v for k, v in payload.items() if k in allowed}
    if table == 'администраторы':
        required = ['фио_адм', 'логин', 'пароль']
        phone_key, email_key, login_key, pass_key = None, None, 'логин', 'пароль'
    elif table == 'преподаватели':
        required = ['фио_преп', 'логин', 'пароль']
        phone_key, email_key, login_key, pass_key = 'телефон', 'почта', 'логин', 'пароль'
    else:  
        required = ['фио_студ', 'логин', 'пароль']
        phone_key, email_key, login_key, pass_key = 'телефон', 'почта', 'логин', 'пароль'

    for k in required:
        if not str(data.get(k, '')).strip():
            return False, f'Поле {k} обязательно', None

    if str(data.get(login_key, '')) == str(data.get(pass_key, '')):
        return False, 'Логин и пароль не должны совпадать', None

    if phone_key and data.get(phone_key):
        if not _is_valid_phone(str(data[phone_key]).strip()):
            return False, 'Телефон должен содержать только цифры (до 11)', None
    if email_key and data.get(email_key):
        if not _is_valid_email(str(data[email_key]).strip()):
            return False, 'Неверный формат email', None

    return True, None, data

@users_api.route('/api/get_users')
def get_users():
    try:
        table = request.args.get('table')
        search = request.args.get('search', '')
        fio_field = request.args.get('fioField')
        valid_tables = {
            'администраторы': 'фио_адм',
            'преподаватели': 'фио_преп',
            'студенты': 'фио_студ'
        }

        if table not in valid_tables:
            return jsonify({'success': False, 'error': 'Invalid table name'}), 400

        if fio_field != valid_tables[table]:
            return jsonify({'success': False, 'error': 'Invalid FIO field'}), 400
        queries = {
            'администраторы': "SELECT код_адм, фио_адм, логин, пароль FROM администраторы",
            'преподаватели': "SELECT id_преп, фио_преп, логин, пароль, пол, дата_рождения, телефон, почта, должность, кафедра FROM преподаватели",
            'студенты': "SELECT id_студ, фио_студ, логин, пароль, пол, дата_рождения, телефон, почта, название_группы FROM студенты"
        }
        
        query = queries[table]
        params = []

        if search:
            query += f" WHERE {fio_field} LIKE %s"
            params.append(f"%{search}%")

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            columns = [column[0] for column in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                result = {}
                for i, value in enumerate(row):
                    if isinstance(value, datetime):
                        value = value.strftime('%Y-%m-%d')
                    result[columns[i]] = value
                results.append(result)

            return jsonify(results)

    except Exception as e:
        print(f"Error in get_users: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@users_api.route('/api/add_user', methods=['POST'])
def add_user():
    try:
        data = request.json
        if not data or 'table' not in data or 'data' not in data:
            return jsonify({'success': False, 'error': 'Missing required data'}), 400

        table = data['table']
        user_data = data['data']

        valid_tables = {'администраторы', 'преподаватели', 'студенты'}
        if table not in valid_tables:
            return jsonify({'success': False, 'error': 'Invalid table name'}), 400

        ok, err, filtered = _validate_and_filter_user_payload(table, user_data)
        if not ok:
            return jsonify({'success': False, 'error': err}), 400

        columns = [f"{k}" for k in filtered.keys()]
        placeholders = ['%s' for _ in filtered]
        
        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        
        print(f"Debug - Query: {query}")
        print(f"Debug - Values: {list(filtered.values())}")

        with get_db_connection() as conn:
            cursor = conn.cursor()
            if 'логин' in filtered:
                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE логин = %s", [filtered['логин']])
                if cursor.fetchone()[0] > 0:
                    return jsonify({'success': False, 'error': 'Логин уже существует'}), 409
            try:
                cursor.execute(query, list(filtered.values()))
                conn.commit()
                return jsonify({'success': True})
            except errors.UniqueViolation:
                conn.rollback()
                return jsonify({'success': False, 'error': 'Нарушение уникальности (повторяющееся значение)'}), 409
            except psycopg2.Error as e:
                conn.rollback()
                return jsonify({'success': False, 'error': str(e)}), 500

    except Exception as e:
        print(f"Error in add_user: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@users_api.route('/api/update_user', methods=['PUT'])
def update_user():
    try:
        data = request.json
        if not data or 'table' not in data or 'idField' not in data or 'id' not in data or 'data' not in data:
            return jsonify({'success': False, 'error': 'Missing required data'}), 400

        table = data['table']
        id_field = data['idField']
        user_id = data['id']
        user_data = data['data']

        valid_tables = {
            'администраторы': 'код_адм',
            'преподаватели': 'id_преп',
            'студенты': 'id_студ'
        }

        if table not in valid_tables:
            return jsonify({'success': False, 'error': 'Invalid table name'}), 400

        if id_field != valid_tables[table]:
            return jsonify({'success': False, 'error': 'Invalid ID field'}), 400

        ok, err, filtered = _validate_and_filter_user_payload(table, user_data)
        if not ok:
            return jsonify({'success': False, 'error': err}), 400

        set_parts = [f"{k} = %s" for k in filtered.keys()]
        query = f"UPDATE {table} SET {', '.join(set_parts)} WHERE {id_field} = %s"

        values = list(filtered.values())
        values.append(user_id)

        print(f"Debug - Query: {query}")
        print(f"Debug - Values: {values}")

        with get_db_connection() as conn:
            cursor = conn.cursor()
            if 'логин' in filtered:
                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE логин = %s AND {id_field} <> %s", [filtered['логин'], user_id])
                if cursor.fetchone()[0] > 0:
                    return jsonify({'success': False, 'error': 'Логин уже существует'}), 409
            try:
                cursor.execute(query, values)
                conn.commit()
                return jsonify({'success': True})
            except errors.UniqueViolation:
                conn.rollback()
                return jsonify({'success': False, 'error': 'Нарушение уникальности (повторяющееся значение)'}), 409
            except psycopg2.Error as e:
                conn.rollback()
                return jsonify({'success': False, 'error': str(e)}), 500

    except Exception as e:
        print(f"Error in update_user: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@users_api.route('/api/delete_user', methods=['DELETE'])
def delete_user():
    try:
        data = request.json
        if not data or 'table' not in data or 'idField' not in data or 'id' not in data:
            return jsonify({'success': False, 'error': 'Missing required data'}), 400

        table = data['table']
        id_field = data['idField']
        user_id = data['id']

        valid_tables = {
            'администраторы': 'код_адм',
            'преподаватели': 'id_преп',
            'студенты': 'id_студ'
        }

        if table not in valid_tables:
            return jsonify({'success': False, 'error': 'Invalid table name'}), 400

        if id_field != valid_tables[table]:
            return jsonify({'success': False, 'error': 'Invalid ID field'}), 400

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {table} WHERE {id_field} = %s", [user_id])
            conn.commit()
            return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
