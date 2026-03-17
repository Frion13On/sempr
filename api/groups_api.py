from flask import Blueprint, request, jsonify
from flask_login import login_required
from models import get_db_connection
from api_access import require_roles

groups_api = Blueprint('groups_api', __name__)

@groups_api.route('/api/groups', methods=['GET'])
@login_required
@require_roles(1, 2, 3)
def get_groups():
    try:
        search = request.args.get('search', '')
        query = """
            SELECT g.название_группы, s.название_спец AS Специальность, g.курс, t.фио_преп AS Куратор 
            FROM группы g 
            LEFT JOIN специальности s ON g.специальность = s.id_спец 
            LEFT JOIN преподаватели t ON g.куратор = t.id_преп
        """
        params = []
        
        if search:
            query += " WHERE g.название_группы LIKE %s"
            params.append(f"{search}%")

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            columns = [column[0] for column in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                result = {}
                for i, value in enumerate(row):
                    result[columns[i]] = value
                results.append(result)

            return jsonify(results)

    except Exception as e:
        print(f"Error in get_groups: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@groups_api.route('/api/groups', methods=['POST'])
@login_required
@require_roles(1)
def add_group():
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        print(f"Received group data: {data}")

        required_fields = ['Название_группы', 'Специальность', 'Курс', 'Куратор']
        for field in required_fields:
            if field not in data or not str(data[field]).strip():
                return jsonify({'success': False, 'error': f'Поле {field} обязательно'}), 400

        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM группы WHERE название_группы = %s", [data['Название_группы']])
            if cursor.fetchone()[0] > 0:
                return jsonify({'success': False, 'error': 'Группа с таким названием уже существует'}), 400

            cursor.execute("SELECT id_спец FROM специальности WHERE название_спец = %s", [data['Специальность']])
            specialty_id = cursor.fetchone()
            if not specialty_id:
                return jsonify({'success': False, 'error': 'Специальность не найдена'}), 404

            cursor.execute("SELECT id_преп FROM преподаватели WHERE фио_преп = %s", [data['Куратор']])
            curator_id = cursor.fetchone()
            if not curator_id:
                return jsonify({'success': False, 'error': 'Куратор не найден'}), 404

            try:
                cursor.execute("""
                    INSERT INTO группы (название_группы, специальность, курс, куратор) 
                    VALUES (%s, %s, %s, %s)
                """, [
                    data['Название_группы'],
                    specialty_id[0],
                    data['Курс'],
                    curator_id[0]
                ])
                conn.commit()
                return jsonify({'success': True})
            except Exception as e:
                print(f"Database error: {str(e)}")
                return jsonify({'success': False, 'error': 'Ошибка при сохранении в базу данных'}), 500

    except Exception as e:
        print(f"Error in add_group: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@groups_api.route('/api/groups/<group_name>', methods=['PUT'])
@login_required
@require_roles(1)
def update_group(group_name):
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT id_спец FROM специальности WHERE название_спец = %s", [data['Специальность']])
            specialty_id = cursor.fetchone()
            if not specialty_id:
                return jsonify({'success': False, 'error': 'Специальность не найдена'}), 404

            cursor.execute("SELECT id_преп FROM преподаватели WHERE фио_преп = %s", [data['Куратор']])
            curator_id = cursor.fetchone()
            if not curator_id:
                return jsonify({'success': False, 'error': 'Куратор не найден'}), 404

            cursor.execute("""
                UPDATE группы 
                SET специальность = %s, курс = %s, куратор = %s 
                WHERE название_группы = %s
            """, [
                specialty_id[0],
                data['Курс'],
                curator_id[0],
                group_name
            ])
            conn.commit()
            return jsonify({'success': True})

    except Exception as e:
        print(f"Error in update_group: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@groups_api.route('/api/groups/<group_name>', methods=['DELETE'])
@login_required
@require_roles(1)
def delete_group(group_name):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM группы WHERE название_группы = %s", [group_name])
            conn.commit()
            return jsonify({'success': True})
    except Exception as e:
        print(f"Error in delete_group: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
