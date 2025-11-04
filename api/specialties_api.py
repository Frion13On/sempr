from flask import Blueprint, request, jsonify
from models import get_db_connection

specialties_api = Blueprint('specialties_api', __name__)

@specialties_api.route('/api/specialties')
def get_specialties():
    try:
        search = request.args.get('search', '')
        query = """
            SELECT id_спец, название_спец, уровень_образования, кафедра 
            FROM специальности
        """
        params = []
        if search:
            query += " WHERE название_спец LIKE %s"
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
        print(f"Error in get_specialties: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@specialties_api.route('/api/specialty-assignments')
def get_specialty_assignments():
    try:
        search = request.args.get('search', '')
        base_query = """
            SELECT специальности.название_спец, дисциплина.название 
            FROM спец_дисц 
            INNER JOIN специальности ON спец_дисц.id_спец = специальности.id_спец 
            INNER JOIN дисциплина ON спец_дисц.id_дисц = дисциплина.id_дисц
        """
        params = []
        if search:
            base_query += "\n            WHERE специальности.название_спец ILIKE %s OR дисциплина.название ILIKE %s\n"
            like = f"%{search}%"
            params.extend([like, like])
        base_query += "\n            ORDER BY специальности.название_спец, дисциплина.название\n"
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(base_query, params)
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'Название_спец': row[0],
                    'Название': row[1]
                })
            return jsonify(results)
    except Exception as e:
        print(f"Error in get_specialty_assignments: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@specialties_api.route('/api/specialties', methods=['POST'])
def add_specialty():
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM специальности WHERE id_спец = %s", [data['ID_спец']])
            if cursor.fetchone()[0] > 0:
                return jsonify({'success': False, 'error': 'Специальность с таким ID уже существует'}), 400
            cursor.execute("""
                INSERT INTO специальности (id_спец, название_спец, уровень_образования, кафедра)
                VALUES (%s, %s, %s, %s)
            """, [
                data['ID_спец'],
                data['Название_спец'],
                data['Уровень_образования'],
                data['Кафедра']
            ])
            conn.commit()
            return jsonify({'success': True})
    except Exception as e:
        print(f"Error in add_specialty: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@specialties_api.route('/api/specialties/<specialty_id>', methods=['PUT'])
def update_specialty(specialty_id):
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE специальности 
                SET id_спец = %s, название_спец = %s, уровень_образования = %s, кафедра = %s
                WHERE id_спец = %s
            """, [
                data['ID_спец'],
                data['Название_спец'],
                data['Уровень_образования'],
                data['Кафедра'],
                specialty_id
            ])
            conn.commit()
            return jsonify({'success': True})
    except Exception as e:
        print(f"Error in update_specialty: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@specialties_api.route('/api/specialties/<specialty_id>', methods=['DELETE'])
def delete_specialty(specialty_id):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM специальности WHERE id_спец = %s", [specialty_id])
            conn.commit()
            return jsonify({'success': True})
    except Exception as e:
        print(f"Error in delete_specialty: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@specialties_api.route('/api/specialty-assignments', methods=['POST'])
def assign_discipline_to_specialty():
    try:
        data = request.json
        if not data or 'Название_спец' not in data or 'Название' not in data:
            return jsonify({'success': False, 'error': 'Missing required data'}), 400
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id_спец FROM специальности WHERE название_спец = %s", [data['Название_спец']])
            specialty_id = cursor.fetchone()
            if not specialty_id:
                return jsonify({'success': False, 'error': 'Специальность не найдена'}), 404
            cursor.execute("SELECT id_дисц FROM дисциплина WHERE название = %s", [data['Название']])
            discipline_id = cursor.fetchone()
            if not discipline_id:
                return jsonify({'success': False, 'error': 'Дисциплина не найдена'}), 404
            cursor.execute(
                "INSERT INTO спец_дисц (id_спец, id_дисц) VALUES (%s, %s)",
                [specialty_id[0], discipline_id[0]]
            )
            conn.commit()
            return jsonify({'success': True})
    except Exception as e:
        print(f"Error in assign_discipline_to_specialty: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@specialties_api.route('/api/specialty-assignments', methods=['DELETE'])
def remove_specialty_assignment():
    try:
        data = request.json
        if not data or 'Название_спец' not in data or 'Название' not in data:
            return jsonify({'success': False, 'error': 'Missing required data'}), 400
        query = """
            DELETE FROM спец_дисц
            WHERE id_спец = (SELECT id_спец FROM специальности WHERE название_спец = %s)
            AND id_дисц = (SELECT id_дисц FROM дисциплина WHERE название = %s)
        """ 
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (data['Название_спец'], data['Название']))
            conn.commit()
            return jsonify({'success': True})
    except Exception as e:
        print(f"Error in remove_specialty_assignment: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
