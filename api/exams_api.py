from flask import Blueprint, request, jsonify
from models import get_db_connection

exams_api = Blueprint('exams_api', __name__)

@exams_api.route('/api/exams')
def get_exams():
    try:
        search = request.args.get('search', '')
        query = """
            SELECT e.id_экзамен, d.название AS Дисциплина, 
                   p.фио_преп AS Преподаватель, 
                   e.название_группы, 
                   e.дата_экзамена
            FROM экзамены e
            JOIN дисциплина d ON e.id_дисц = d.id_дисц
            JOIN преподаватели p ON e.id_преп = p.id_преп
        """
        params = []
        if search:
            query += " WHERE e.название_группы LIKE %s"
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
        print(f"Error in get_exams: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@exams_api.route('/api/exams', methods=['POST'])
def add_exam():
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id_дисц FROM дисциплина WHERE название = %s", [data['Дисциплина']])
            discipline_id = cursor.fetchone()
            if not discipline_id:
                return jsonify({'success': False, 'error': 'Дисциплина не найдена'}), 404
            cursor.execute("SELECT id_преп FROM преподаватели WHERE фио_преп = %s", [data['Преподаватель']])
            teacher_id = cursor.fetchone()
            if not teacher_id:
                return jsonify({'success': False, 'error': 'Преподаватель не найден'}), 404

            try:
                cursor.execute("""
                    INSERT INTO экзамены (id_дисц, id_преп, название_группы, дата_экзамена) 
                    VALUES (%s, %s, %s, %s)
                """, [
                    discipline_id[0],
                    teacher_id[0],
                    data['Название_группы'],
                    data['Дата_экзамена']
                ])
                conn.commit()
                return jsonify({'success': True})
            except Exception as e:
                print(f"Database error: {str(e)}")
                return jsonify({'success': False, 'error': 'Ошибка при сохранении в базу данных'}), 500
    except Exception as e:
        print(f"Error in add_exam: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@exams_api.route('/api/exams/<int:exam_id>', methods=['PUT'])
def update_exam(exam_id):
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id_дисц FROM дисциплина WHERE название = %s", [data['Дисциплина']])
            discipline_id = cursor.fetchone()
            if not discipline_id:
                return jsonify({'success': False, 'error': 'Дисциплина не найдена'}), 404
            cursor.execute("SELECT id_преп FROM преподаватели WHERE фио_преп = %s", [data['Преподаватель']])
            teacher_id = cursor.fetchone()
            if not teacher_id:
                return jsonify({'success': False, 'error': 'Преподаватель не найден'}), 404
            cursor.execute("""
                UPDATE экзамены 
                SET id_дисц = %s, id_преп = %s, название_группы = %s, дата_экзамена = %s
                WHERE id_экзамен = %s
            """, [
                discipline_id[0],
                teacher_id[0],
                data['Название_группы'],
                data['Дата_экзамена'],
                exam_id
            ])
            conn.commit()
            return jsonify({'success': True})
    except Exception as e:
        print(f"Error in update_exam: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@exams_api.route('/api/exams/<int:exam_id>', methods=['DELETE'])
def delete_exam(exam_id):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM экзамены WHERE id_экзамен = %s", [exam_id])
            conn.commit()
            return jsonify({'success': True})
    except Exception as e:
        print(f"Error in delete_exam: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
