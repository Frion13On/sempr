from flask import Blueprint, request, jsonify
from flask_login import login_required
from models import get_db_connection
from api_access import require_roles

disciplines_api = Blueprint('disciplines_api', __name__)

@disciplines_api.route('/api/disciplines')
@login_required
@require_roles(1, 2, 3)
def get_disciplines():
    try:
        search = request.args.get('search', '')
        query = "SELECT id_дисц, название, количество_занятий FROM дисциплина"
        params = []
        
        if search:
            query += " WHERE название LIKE %s"
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
        print(f"Error in get_disciplines: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@disciplines_api.route('/api/disciplines', methods=['POST'])
@login_required
@require_roles(1)
def add_discipline():
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        query = "INSERT INTO дисциплина (название, количество_занятий) VALUES (%s, %s)"
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (data['Название'], data['Количество_занятий']))
            conn.commit()
            return jsonify({'success': True})

    except Exception as e:
        print(f"Error in add_discipline: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@disciplines_api.route('/api/disciplines/<int:id>', methods=['PUT'])
@login_required
@require_roles(1)
def update_discipline(id):
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        query = "UPDATE дисциплина SET название = %s, количество_занятий = %s WHERE id_дисц = %s"
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (data['Название'], data['Количество_занятий'], id))
            conn.commit()
            return jsonify({'success': True})

    except Exception as e:
        print(f"Error in update_discipline: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@disciplines_api.route('/api/disciplines/<int:id>', methods=['DELETE'])
@login_required
@require_roles(1)
def delete_discipline(id):
    try:
        query = "DELETE FROM дисциплина WHERE id_дисц = %s"
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, [id])
            conn.commit()
            return jsonify({'success': True})

    except Exception as e:
        print(f"Error in delete_discipline: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@disciplines_api.route('/api/discipline-assignments')
@login_required
@require_roles(1)
def get_discipline_assignments():
    try:
        search = request.args.get('search', '')
        base_query = "SELECT п.фио_преп, д.название FROM преподаватели п INNER JOIN дисц_преп дп ON п.id_преп = дп.id_преп INNER JOIN дисциплина д ON дп.id_дисц = д.id_дисц"
        params = []
        if search:
            base_query += "\n            WHERE п.фио_преп ILIKE %s OR д.название ILIKE %s\n"
            like = f"%{search}%"
            params.extend([like, like])
        base_query += "\n            ORDER BY п.фио_преп, д.название\n"
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(base_query, params)
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'ФИО_преп': row[0],
                    'Название': row[1]
                })

            return jsonify(results)

    except Exception as e:
        print(f"Error in get_discipline_assignments: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@disciplines_api.route('/api/discipline-assignments', methods=['POST'])
@login_required
@require_roles(1)
def assign_discipline():
    try:
        data = request.json
        if not data or 'ФИО_преп' not in data or 'Название' not in data:
            return jsonify({'success': False, 'error': 'Missing required data'}), 400

        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT id_преп FROM преподаватели WHERE фио_преп = %s", [data['ФИО_преп']])
            teacher_id = cursor.fetchone()
            if not teacher_id:
                return jsonify({'success': False, 'error': 'Преподаватель не найден'}), 404
            
            cursor.execute("SELECT id_дисц FROM дисциплина WHERE название = %s", [data['Название']])
            discipline_id = cursor.fetchone()
            if not discipline_id:
                return jsonify({'success': False, 'error': 'Дисциплина не найдена'}), 404

            cursor.execute(
                "INSERT INTO дисц_преп (id_преп, id_дисц) VALUES (%s, %s)",
                [teacher_id[0], discipline_id[0]]
            )
            conn.commit()
            return jsonify({'success': True})

    except Exception as e:
        print(f"Error in assign_discipline: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@disciplines_api.route('/api/discipline-assignments', methods=['DELETE'])
@login_required
@require_roles(1)
def remove_assignment():
    try:
        data = request.json
        if not data or 'ФИО_преп' not in data or 'Название' not in data:
            return jsonify({'success': False, 'error': 'Missing required data'}), 400

        query = "DELETE FROM дисц_преп WHERE id_преп = (SELECT id_преп FROM преподаватели WHERE фио_преп = %s) AND id_дисц = (SELECT id_дисц FROM дисциплина WHERE название = %s)"
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (data['ФИО_преп'], data['Название']))
            conn.commit()
            return jsonify({'success': True})

    except Exception as e:
        print(f"Error in remove_assignment: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@disciplines_api.route('/api/teachers')
@login_required
@require_roles(1)
def get_teachers():
    try:
        query = "SELECT фио_преп FROM преподаватели ORDER BY фио_преп"
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            teachers = [row[0] for row in cursor.fetchall()]
            return jsonify(teachers)

    except Exception as e:
        print(f"Error in get_teachers: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
