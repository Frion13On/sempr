from flask import Blueprint, request, jsonify
from models import get_db_connection

expulsion_api = Blueprint('expulsion_api', __name__)

@expulsion_api.route('/api/expulsion')
def get_expulsion_list():
    try:
        query = """
            SELECT студенты.id_студ, студенты.фио_студ AS ФИО, 
                   студенты.название_группы,
                   COUNT(электронный_журнал.оценка) AS Количество_долгов 
            FROM электронный_журнал
            INNER JOIN студенты ON электронный_журнал.id_студ = студенты.id_студ
            LEFT JOIN экзамены ON электронный_журнал.id_экзамен = экзамены.id_экзамен
            WHERE (электронный_журнал.оценка = '2' OR электронный_журнал.оценка = 'Н') 
            AND (экзамены.id_экзамен IS NOT NULL)
            GROUP BY студенты.id_студ, студенты.фио_студ, студенты.название_группы
            HAVING COUNT(электронный_журнал.оценка) >= 3
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
        print(f"Error in get_expulsion_list: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@expulsion_api.route('/api/expulsion', methods=['DELETE'])
def expel_students():
    try:
        data = request.json
        if not data or 'student_ids' not in data:
            return jsonify({'success': False, 'error': 'No student IDs provided'}), 400
        student_ids = data['student_ids']
        if not student_ids:
            return jsonify({'success': False, 'error': 'Empty student IDs list'}), 400
        with get_db_connection() as conn:
            cursor = conn.cursor()
            for student_id in student_ids:
                cursor.execute("DELETE FROM студенты WHERE id_студ = %s", [student_id])
            conn.commit()
            return jsonify({'success': True})
    except Exception as e:
        print(f"Error in expel_students: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
