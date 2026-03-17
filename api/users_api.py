from flask import Blueprint, request, jsonify
from flask_login import login_required
from models import get_db_connection
from datetime import datetime
import re
import psycopg2
from psycopg2 import errors
from password_utils import hash_password, is_strong_password
from api_access import require_roles

users_api = Blueprint('users_api', __name__)

# Роли: 1 — администратор, 2 — преподаватель, 3 — студент
_ROLE_BY_TABLE = {'администраторы': 1, 'преподаватели': 2, 'студенты': 3}

_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_MALICIOUS_PATTERN_RE = re.compile(
    r"(<\s*script|</\s*script|--|;|/\*|\*/|\bOR\b\s+['\"]?1['\"]?\s*=\s*['\"]?1['\"]?)",
    re.IGNORECASE,
)
def _is_valid_email(v: str) -> bool:
    return bool(_EMAIL_RE.match(v))

def _is_valid_phone(v: str) -> bool:
    return v.isdigit() and len(v) <= 11

def _is_safe_string(value: str) -> bool:
    if value is None:
        return True
    return not bool(_MALICIOUS_PATTERN_RE.search(value))

_ALLOWED_FIELDS = {
    'администраторы': {'фио_адм', 'логин', 'пароль'},
    'преподаватели': {'фио_преп', 'логин', 'пароль', 'пол', 'дата_рождения', 'телефон', 'почта', 'должность', 'кафедра'},
    'студенты': {'фио_студ', 'логин', 'пароль', 'пол', 'дата_рождения', 'телефон', 'почта', 'название_группы'}
}

def _validate_and_filter_user_payload(table: str, payload: dict, *, require_password: bool = True):
    if table not in _ALLOWED_FIELDS:
        return False, 'Invalid table name', None
    allowed = _ALLOWED_FIELDS[table]
    data = {k: v for k, v in payload.items() if k in allowed}
    if table == 'администраторы':
        required = ['фио_адм', 'логин'] + (['пароль'] if require_password else [])
        phone_key, email_key, login_key, pass_key = None, None, 'логин', 'пароль'
    elif table == 'преподаватели':
        required = ['фио_преп', 'логин'] + (['пароль'] if require_password else [])
        phone_key, email_key, login_key, pass_key = 'телефон', 'почта', 'логин', 'пароль'
    else:
        required = ['фио_студ', 'логин'] + (['пароль'] if require_password else [])
        phone_key, email_key, login_key, pass_key = 'телефон', 'почта', 'логин', 'пароль'

    for k in required:
        if not str(data.get(k, '')).strip():
            return False, f'Поле {k} обязательно', None

    if require_password and str(data.get(login_key, '')) == str(data.get(pass_key, '')):
        return False, 'Логин и пароль не должны совпадать', None

    # Проверка сложности пароля
    if pass_key and data.get(pass_key):
        ok, err = is_strong_password(str(data[pass_key]))
        if not ok:
            return False, err, None

    if phone_key and data.get(phone_key):
        if not _is_valid_phone(str(data[phone_key]).strip()):
            return False, 'Телефон должен содержать только цифры (до 11)', None
    if email_key and data.get(email_key):
        if not _is_valid_email(str(data[email_key]).strip()):
            return False, 'Неверный формат email', None

    for field, value in data.items():
        text_value = str(value)
        if not _is_safe_string(text_value):
            return False, f'Поле {field} содержит потенциально опасный ввод', None

    return True, None, data

def _role_table_columns(table: str):
    """Колонки только по таблице роли (без логин/пароль)."""
    if table == 'администраторы':
        return ['фио_адм']
    if table == 'преподаватели':
        return ['фио_преп', 'пол', 'дата_рождения', 'телефон', 'почта', 'должность', 'кафедра']
    return ['фио_студ', 'пол', 'дата_рождения', 'телефон', 'почта', 'название_группы']

@users_api.route('/api/get_users')
@login_required
@require_roles(1)
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
            'администраторы': """SELECT adm.код_адм, adm.фио_адм, a.логин
                FROM администраторы adm LEFT JOIN авторизация a ON a.id = adm.user_id""",
            'преподаватели': """SELECT p.id_преп, p.фио_преп, a.логин, p.пол, p.дата_рождения, p.телефон, p.почта, p.должность, p.кафедра
                FROM преподаватели p LEFT JOIN авторизация a ON a.id = p.user_id""",
            'студенты': """SELECT s.id_студ, s.фио_студ, a.логин, s.пол, s.дата_рождения, s.телефон, s.почта, s.название_группы
                FROM студенты s LEFT JOIN авторизация a ON a.id = s.user_id"""
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
@login_required
@require_roles(1)
def add_user():
    try:
        data = request.json
        if not data or 'table' not in data or 'data' not in data:
            return jsonify({'success': False, 'error': 'Missing required data'}), 400
        table = data['table']
        user_data = data['data']
        if table not in _ROLE_BY_TABLE:
            return jsonify({'success': False, 'error': 'Invalid table name'}), 400

        ok, err, filtered = _validate_and_filter_user_payload(table, user_data, require_password=True)
        if not ok:
            return jsonify({'success': False, 'error': err}), 400

        role = _ROLE_BY_TABLE[table]
        login = filtered.get('логин')
        password = filtered.get('пароль')
        password_hash = hash_password(password)
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM авторизация WHERE логин = %s", [login])
            if cursor.fetchone()[0] > 0:
                return jsonify({'success': False, 'error': 'Логин уже существует'}), 409
            cursor.execute(
                "INSERT INTO авторизация (логин, пароль, роль) VALUES (%s, %s, %s) RETURNING id",
                (login, password_hash, role),
            )
            auth_id = cursor.fetchone()[0]
            cols = _role_table_columns(table)
            data_cols = [k for k in cols if k in filtered]
            columns_with_user = data_cols + ['user_id']
            col_values = [filtered[k] for k in data_cols] + [auth_id]
            placeholders = ', '.join(['%s'] * len(col_values))
            columns_str = ', '.join(columns_with_user)
            query = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"
            try:
                cursor.execute(query, col_values)
                conn.commit()
                return jsonify({'success': True})
            except errors.UniqueViolation:
                conn.rollback()
                cursor.execute("DELETE FROM авторизация WHERE id = %s", [auth_id])
                conn.commit()
                return jsonify({'success': False, 'error': 'Нарушение уникальности (повторяющееся значение)'}), 409
            except psycopg2.Error as e:
                conn.rollback()
                cursor.execute("DELETE FROM авторизация WHERE id = %s", [auth_id])
                conn.commit()
                return jsonify({'success': False, 'error': str(e)}), 500
    except Exception as e:
        print(f"Error in add_user: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@users_api.route('/api/update_user', methods=['PUT'])
@login_required
@require_roles(1)
def update_user():
    try:
        data = request.json
        if not data or 'table' not in data or 'idField' not in data or 'id' not in data or 'data' not in data:
            return jsonify({'success': False, 'error': 'Missing required data'}), 400
        table = data['table']
        id_field = data['idField']
        row_id = data['id']
        user_data = data['data']
        valid_tables = {'администраторы': 'код_адм', 'преподаватели': 'id_преп', 'студенты': 'id_студ'}
        if table not in valid_tables or id_field != valid_tables[table]:
            return jsonify({'success': False, 'error': 'Invalid table or id field'}), 400

        ok, err, filtered = _validate_and_filter_user_payload(table, user_data, require_password=False)
        if not ok:
            return jsonify({'success': False, 'error': err}), 400

        with get_db_connection() as conn:
            cursor = conn.cursor()
            if 'логин' in filtered or 'пароль' in filtered:
                cursor.execute(f"SELECT user_id FROM {table} WHERE {id_field} = %s", [row_id])
                ref = cursor.fetchone()
                if ref:
                    auth_id = ref[0]
                    if auth_id:
                        if filtered.get('логин') is not None:
                            cursor.execute("SELECT COUNT(*) FROM авторизация WHERE логин = %s AND id <> %s", [filtered['логин'], auth_id])
                            if cursor.fetchone()[0] > 0:
                                return jsonify({'success': False, 'error': 'Логин уже существует'}), 409
                        updates = []
                        vals = []
                        if 'логин' in filtered:
                            updates.append("логин = %s")
                            vals.append(filtered['логин'])
                        if 'пароль' in filtered:
                            password_hash = hash_password(filtered['пароль'])
                            updates.append("пароль = %s")
                            vals.append(password_hash)
                        if updates:
                            vals.append(auth_id)
                            cursor.execute("UPDATE авторизация SET " + ", ".join(updates) + " WHERE id = %s", vals)

            role_cols = _role_table_columns(table)
            set_parts = [f"{k} = %s" for k in role_cols if k in filtered]
            if set_parts:
                values = [filtered[k] for k in role_cols if k in filtered]
                values.append(row_id)
                cursor.execute(f"UPDATE {table} SET {', '.join(set_parts)} WHERE {id_field} = %s", values)
            conn.commit()
            return jsonify({'success': True})
    except Exception as e:
        print(f"Error in update_user: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@users_api.route('/api/delete_user', methods=['DELETE'])
@login_required
@require_roles(1)
def delete_user():
    try:
        data = request.json
        if not data or 'table' not in data or 'idField' not in data or 'id' not in data:
            return jsonify({'success': False, 'error': 'Missing required data'}), 400
        table = data['table']
        id_field = data['idField']
        row_id = data['id']
        valid_tables = {'администраторы': 'код_адм', 'преподаватели': 'id_преп', 'студенты': 'id_студ'}
        if table not in valid_tables or id_field != valid_tables[table]:
            return jsonify({'success': False, 'error': 'Invalid table or id field'}), 400

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT user_id FROM {table} WHERE {id_field} = %s", [row_id])
            ref = cursor.fetchone()
            cursor.execute(f"DELETE FROM {table} WHERE {id_field} = %s", [row_id])
            if ref and ref[0]:
                cursor.execute("DELETE FROM авторизация WHERE id = %s", [ref[0]])
            conn.commit()
            return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
