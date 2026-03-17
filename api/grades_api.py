from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from models import get_db_connection
from datetime import datetime
from api_access import require_roles, require_same_user_id

grades_api = Blueprint('grades_api', __name__)

@grades_api.route('/api/student/debts')
@login_required
@require_roles(3)
@require_same_user_id(param='student_id', user_attr='student_id', sources=('args',))
def get_student_debts():
    try:
        student_id = request.args.get('student_id') or getattr(current_user, 'student_id', None)
        if not student_id:
            return jsonify({'success': False, 'error': 'Student ID not found in session'}), 400
        query = """
            SELECT d.название AS DisciplineName, 
                   e.дата_экзамена AS ExamDate,
                   ej.оценка AS Grade 
            FROM электронный_журнал ej
            INNER JOIN экзамены e ON ej.id_экзамен = e.id_экзамен 
            INNER JOIN дисциплина d ON ej.id_дисц = d.id_дисц
            WHERE ej.id_студ = %s AND ej.оценка = '2'
        """ 
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, [student_id])
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
        print(f"Error in get_student_debts: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@grades_api.route('/api/student/disciplines')
@login_required
@require_roles(3)
@require_same_user_id(param='student_id', user_attr='student_id', sources=('args',))
def get_student_disciplines():
    try:
        student_id = request.args.get('student_id') or getattr(current_user, 'student_id', None)
        if not student_id:
            return jsonify({'success': False, 'error': 'Student ID not found in session'}), 400
        query = """
            SELECT DISTINCT d.название 
            FROM электронный_журнал ej 
            INNER JOIN дисциплина d ON ej.id_дисц = d.id_дисц 
            WHERE ej.id_студ = %s
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, [student_id])
            disciplines = [row[0] for row in cursor.fetchall()]
            return jsonify(disciplines)

    except Exception as e:
        print(f"Error in get_student_disciplines: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@grades_api.route('/api/student/grades')
@login_required
@require_roles(3)
@require_same_user_id(param='student_id', user_attr='student_id', sources=('args',))
def get_student_grades():
    try:
        student_id = request.args.get('student_id') or getattr(current_user, 'student_id', None)
        discipline = request.args.get('discipline')
        if not student_id or not discipline:
            return jsonify({'success': False, 'error': 'Missing required parameters'}), 400
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id_дисц FROM дисциплина WHERE название = %s", [discipline])
            discipline_id = cursor.fetchone()
            if not discipline_id:
                return jsonify({'success': False, 'error': 'Discipline not found'}), 404
            query = """ 
            SELECT номер_занятия AS LessonNumber, оценка AS Grade 
                FROM электронный_журнал 
                WHERE id_дисц = %s AND id_студ = %s 
            """
            cursor.execute(query, [discipline_id[0], student_id])
            grades = []
            count_grades = 0
            sum_grades = 0
            count_absences = 0
            for row in cursor.fetchall():
                lesson_number = row[0]
                grade = row[1]
                if lesson_number:
                    grade_data = {
                        'LessonNumber': lesson_number,
                        'Grade': grade
                    }
                    grades.append(grade_data)
                    if grade == 'Н':
                        count_absences += 1
                    elif grade and grade.isdigit():
                        count_grades += 1
                        sum_grades += int(grade)
            final_grade = 'н/а'
            if count_grades > 0 and count_absences <= count_grades:
                final_grade = f"{sum_grades / count_grades:.2f}"
            return jsonify({
                'grades': grades,
                'stats': {
                    'finalGrade': final_grade,
                    'gradesCount': count_grades,
                    'absencesCount': count_absences
                }
            })
    except Exception as e:
        print(f"Error in get_student_grades: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@grades_api.route('/api/teacher/groups')
@login_required
@require_roles(2)
@require_same_user_id(param='teacher_id', user_attr='teacher_id', sources=('args',))
def get_teacher_groups():
    try:
        teacher_id = request.args.get('teacher_id') or getattr(current_user, 'teacher_id', None)
        if not teacher_id:
            return jsonify({'success': False, 'error': 'Teacher ID not found in session'}), 400
        query = "SELECT название_группы FROM группы WHERE куратор = %s"
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, [teacher_id])
            groups = [row[0] for row in cursor.fetchall()]
            return jsonify(groups)
    except Exception as e:
        print(f"Error in get_teacher_groups: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@grades_api.route('/api/group/grades')
@login_required
def get_group_grades():
    try:
        student_id = request.args.get('student_id')
        group_name = request.args.get('group')
        if not current_app.config.get("LOGIN_DISABLED"):
            # Student can only access their own group stats; teachers/admins must pass explicit group.
            if int(getattr(current_user, "role_id", -1)) == 3:
                if student_id and str(student_id) != str(getattr(current_user, "student_id", "")):
                    return jsonify({'success': False, 'error': 'Access denied'}), 403
                student_id = getattr(current_user, "student_id", None)
            elif int(getattr(current_user, "role_id", -1)) not in (1, 2):
                return jsonify({'success': False, 'error': 'Access denied'}), 403
        if student_id and not group_name:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT название_группы FROM студенты WHERE id_студ = %s", [student_id])
                result = cursor.fetchone()
                if not result:
                    return jsonify({'success': False, 'error': 'Student not found'}), 404
                group_name = result[0]
        if not group_name:
            return jsonify({'success': False, 'error': 'Group name not provided'}), 400
        query = """
            SELECT d.название AS DisciplineName,
                   AVG(CASE WHEN ej.оценка = 'н/а' THEN 2 WHEN ej.оценка NOT IN ('Н') AND ej.оценка ~ '^[0-9]+$'
                       THEN CAST(ej.оценка AS REAL) ELSE 2 
                   END) AS AverageGrade,
                   SUM(CASE WHEN ej.оценка = 'Н' THEN 1 ELSE 0 END) AS TotalAbsences
            FROM электронный_журнал ej INNER JOIN дисциплина d ON ej.id_дисц = d.id_дисц INNER JOIN студенты s ON ej.id_студ = s.id_студ
            WHERE s.название_группы = %s
            GROUP BY d.название
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, [group_name])
            grades = []
            total_absences = 0
            discipline_count = 0
            for row in cursor.fetchall():
                discipline_name = row[0]
                average_grade = row[1]
                total_absences_count = row[2]
                grade_data = {
                    'DisciplineName': discipline_name,
                    'AverageGrade': f"{float(average_grade):.2f}" if average_grade else 'н/д'
                }
                grades.append(grade_data)
                total_absences += total_absences_count or 0
                discipline_count += 1
            average_absences = f"{total_absences / discipline_count:.2f}" if discipline_count > 0 else "0"

            return jsonify({
                'grades': grades,
                'averageAbsences': average_absences,
                'groupName': group_name
            })
    except Exception as e:
        print(f"Error in get_group_grades: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@grades_api.route('/api/teacher/disciplines')
@login_required
@require_roles(2)
@require_same_user_id(param='teacher_id', user_attr='teacher_id', sources=('args',))
def get_teacher_disciplines():
    try:
        teacher_id = request.args.get('teacher_id') or getattr(current_user, 'teacher_id', None)
        if not teacher_id:
            return jsonify({'success': False, 'error': 'Teacher ID not found in session'}), 400

        query = """
            SELECT DISTINCT d.название 
            FROM дисц_преп dp 
            JOIN дисциплина d ON dp.id_дисц = d.id_дисц 
            WHERE dp.id_преп = %s
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, [teacher_id])
            disciplines = [row[0] for row in cursor.fetchall()]
            return jsonify(disciplines)
    except Exception as e:
        print(f"Error in get_teacher_disciplines: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@grades_api.route('/api/final/grades')
@login_required
def get_final_grades():
    try:
        discipline = request.args.get('discipline')
        group = request.args.get('group')
        if not discipline or not group:
            return jsonify({'success': False, 'error': 'Missing required parameters'}), 400

        query = """
            SELECT s.фио_студ AS studentName,
                   SUM(CASE WHEN ej.оценка = 'Н' THEN 1 ELSE 0 END) AS absences,
                   COUNT(ej.оценка) AS totalLessons,
                   AVG(CASE 
                       WHEN ej.оценка ~ '^[0-9]+$'
                       THEN CAST(ej.оценка AS REAL) 
                       ELSE NULL 
                   END) AS avgGrade
            FROM электронный_журнал ej
            JOIN студенты s ON ej.id_студ = s.id_студ
            JOIN дисциплина d ON ej.id_дисц = d.id_дисц
            WHERE d.название = %s AND ej.название_группы = %s
            GROUP BY s.фио_студ
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, [discipline, group])
            results = []
            for row in cursor.fetchall():
                student_name = row[0]
                absences = row[1] or 0
                total_lessons = row[2] or 0
                avg_grade = row[3]
                final_grade = 'н/а' if (total_lessons > 0 and absences > total_lessons / 2) else \
                            f"{float(avg_grade):.2f}" if avg_grade else 'нет данных'
                results.append({
                    'studentName': student_name,
                    'finalGrade': final_grade
                })
            return jsonify(results)
    except Exception as e:
        print(f"Error in get_final_grades: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@grades_api.route('/api/grades/table')
@login_required
@require_roles(2)
def get_grades_table():
    try:
        discipline = request.args.get('discipline')
        group = request.args.get('group')
        if not discipline or not group:
            return jsonify({'success': False, 'error': 'Missing required parameters'}), 400
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT количество_занятий FROM дисциплина WHERE название = %s", [discipline])
            result = cursor.fetchone()
            if not result:
                return jsonify({'success': False, 'error': 'Discipline not found'}), 404
            number_of_lessons = result[0]
            cursor.execute("SELECT id_дисц FROM дисциплина WHERE название = %s", [discipline])
            discipline_id = cursor.fetchone()[0]
            query = """
                SELECT s.фио_студ, TRIM(CAST(ej.номер_занятия as TEXT)) as Номер_занятия, 
                       ej.оценка, p.фио_преп 
                FROM студенты s 
                LEFT JOIN электронный_журнал ej ON s.id_студ = ej.id_студ 
                    AND ej.id_дисц = %s AND ej.название_группы = %s
                LEFT JOIN преподаватели p ON ej.id_преп = p.id_преп 
                WHERE s.название_группы = %s
                ORDER BY s.фио_студ, ej.номер_занятия
            """
            cursor.execute(query, [discipline_id, group, group])
            students = {}
            for row in cursor.fetchall():
                student_name = row[0]
                lesson_number = row[1].strip() if row[1] else None
                grade = row[2]
                teacher_name = row[3]
                if student_name not in students:
                    students[student_name] = {
                        'name': student_name,
                        'grades': {},
                        'teachers': {}
                    }
                if lesson_number is not None:
                    lesson_key = str(lesson_number)
                    students[student_name]['grades'][lesson_key] = grade or ''
                    if teacher_name:
                        students[student_name]['teachers'][lesson_key] = teacher_name

            for student_data in students.values():
                for i in range(1, number_of_lessons + 1):
                    lesson_key = str(i)
                    if lesson_key not in student_data['grades']:
                        student_data['grades'][lesson_key] = ''
                absences = sum(1 for grade in student_data['grades'].values() if grade == 'Н')
                student_data['absences'] = absences
            print("Sending data:", {'numberOfLessons': number_of_lessons, 'students': list(students.values())})  # Debug log
            return jsonify({
                'numberOfLessons': number_of_lessons,
                'students': list(students.values())
            })
    except Exception as e:
        print(f"Error in get_grades_table: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@grades_api.route('/api/grades/save', methods=['POST'])
@login_required
@require_roles(2)
def save_grades():
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        required_fields = ['discipline', 'group', 'teacherId', 'grades']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing {field}'}), 400
        if not current_app.config.get("LOGIN_DISABLED"):
            if str(data.get("teacherId")) != str(getattr(current_user, "teacher_id", "")):
                return jsonify({'success': False, 'error': 'Access denied'}), 403
            data["teacherId"] = getattr(current_user, "teacher_id", data["teacherId"])
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id_дисц FROM дисциплина WHERE название = %s", [data['discipline']])
            discipline_id = cursor.fetchone()
            if not discipline_id:
                return jsonify({'success': False, 'error': 'Discipline not found'}), 404
            discipline_id = discipline_id[0]
            for student in data['grades']:
                cursor.execute("SELECT id_студ FROM студенты WHERE фио_студ = %s", [student['studentName']])
                student_id = cursor.fetchone()
                if not student_id:
                    continue
                student_id = student_id[0]
                for lesson_number, grade in student['grades'].items():
                    grade = grade.strip() if grade else ''
                    lesson_number = lesson_number.strip()
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM электронный_журнал 
                        WHERE id_дисц = %s AND название_группы = %s 
                        AND id_студ = %s AND TRIM(CAST(номер_занятия as TEXT)) = %s
                    """, [discipline_id, data['group'], student_id, lesson_number])
                    grade_exists = cursor.fetchone()[0] > 0
                    if grade_exists:
                        if grade:
                            if not (grade == 'Н' or (grade.isdigit() and 1 <= int(grade) <= 5)):
                                return jsonify({
                                    'success': False, 
                                    'error': f'Invalid grade "{grade}" for student {student["studentName"]}'
                                }), 400

                            cursor.execute("""
                                UPDATE электронный_журнал 
                                SET оценка = %s, id_преп = %s 
                                WHERE id_дисц = %s AND название_группы = %s 
                                AND id_студ = %s AND TRIM(CAST(номер_занятия as TEXT)) = %s
                            """, [grade, data['teacherId'], discipline_id, data['group'], student_id, lesson_number])
                        else:
                            cursor.execute("""
                                DELETE FROM электронный_журнал 
                                WHERE id_дисц = %s AND название_группы = %s 
                                AND id_студ = %s AND TRIM(CAST(номер_занятия as TEXT)) = %s
                            """, [discipline_id, data['group'], student_id, lesson_number])
                    elif grade:
                        if not (grade == 'Н' or (grade.isdigit() and 1 <= int(grade) <= 5)):
                            return jsonify({
                                'success': False, 
                                'error': f'Invalid grade "{grade}" for student {student["studentName"]}'
                            }), 400

                        cursor.execute("""
                            INSERT INTO электронный_журнал 
                            (id_дисц, название_группы, id_студ, id_преп, оценка, номер_занятия)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, [discipline_id, data['group'], student_id, data['teacherId'], grade, lesson_number])

            conn.commit()
            return jsonify({'success': True})
    except Exception as e:
        print(f"Error in save_grades: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@grades_api.route('/api/exam/grades/table')
@login_required
@require_roles(2)
def get_exam_grades_table():
    try:
        discipline = request.args.get('discipline')
        group = request.args.get('group')
        if not discipline or not group:
            return jsonify({'success': False, 'error': 'Missing required parameters'}), 400
        with get_db_connection() as conn:
            cursor = conn.cursor()
            exam_query = """
                SELECT e.id_экзамен 
                FROM экзамены e
                JOIN дисциплина d ON e.id_дисц = d.id_дисц
                WHERE d.название = %s AND e.название_группы = %s
            """
            cursor.execute(exam_query, [discipline, group])
            exam_result = cursor.fetchone()
            if not exam_result:
                return jsonify({'success': False, 'error': 'Экзамен не найден'}), 404
            exam_id = exam_result[0]
            query = """
                SELECT s.фио_студ, ej.оценка
                FROM студенты s 
                LEFT JOIN электронный_журнал ej ON s.id_студ = ej.id_студ 
                    AND ej.id_экзамен = %s
                WHERE s.название_группы = %s
                ORDER BY s.фио_студ
            """
            cursor.execute(query, [exam_id, group])
            students = []
            for row in cursor.fetchall():
                students.append({
                    'name': row[0],
                    'grade': row[1] if row[1] is not None else ''
                })

            return jsonify({
                'students': students
            })
    except Exception as e:
        print(f"Error in get_exam_grades_table: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@grades_api.route('/api/exam/grades/save', methods=['POST'])
@login_required
@require_roles(2)
def save_exam_grades():
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        required_fields = ['discipline', 'group', 'teacherId', 'grades']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing {field}'}), 400
        if not current_app.config.get("LOGIN_DISABLED"):
            if str(data.get("teacherId")) != str(getattr(current_user, "teacher_id", "")):
                return jsonify({'success': False, 'error': 'Access denied'}), 403
            data["teacherId"] = getattr(current_user, "teacher_id", data["teacherId"])
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id_дисц FROM дисциплина WHERE название = %s", [data['discipline']])
            discipline_id = cursor.fetchone()
            if not discipline_id:
                return jsonify({'success': False, 'error': 'Discipline not found'}), 404
            discipline_id = discipline_id[0]
            cursor.execute("""
                SELECT id_экзамен 
                FROM экзамены 
                WHERE id_дисц = %s AND название_группы = %s
            """, [discipline_id, data['group']])
            exam_id = cursor.fetchone()
            if not exam_id:
                return jsonify({'success': False, 'error': 'Exam not found'}), 404
            exam_id = exam_id[0]
            for grade_data in data['grades']: 
                cursor.execute("SELECT id_студ FROM студенты WHERE фио_студ = %s", [grade_data['studentName']])
                student_id = cursor.fetchone()
                if not student_id:
                    continue
                student_id = student_id[0]
                grade = grade_data['grade'].strip()
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM электронный_журнал 
                    WHERE id_студ = %s AND id_экзамен = %s
                """, [student_id, exam_id])
                grade_exists = cursor.fetchone()[0] > 0
                if grade_exists:
                    if grade:
                        if not (grade == 'Н' or (grade.isdigit() and 1 <= int(grade) <= 5)):
                            return jsonify({
                                'success': False,
                                'error': f'Invalid grade "{grade}" for student {grade_data["studentName"]}'
                            }), 400
                        cursor.execute("""
                            UPDATE электронный_журнал 
                            SET оценка = %s, id_преп = %s 
                            WHERE id_студ = %s AND id_экзамен = %s
                        """, [grade, data['teacherId'], student_id, exam_id])
                    else:
                        cursor.execute("""
                            DELETE FROM электронный_журнал 
                            WHERE id_студ = %s AND id_экзамен = %s
                        """, [student_id, exam_id])
                elif grade:
                    if not (grade == 'Н' or (grade.isdigit() and 1 <= int(grade) <= 5)):
                        return jsonify({
                            'success': False,
                            'error': f'Invalid grade "{grade}" for student {grade_data["studentName"]}'
                        }), 400
                    cursor.execute("""
                        INSERT INTO электронный_журнал 
                        (id_дисц, название_группы, id_студ, id_преп, оценка, id_экзамен)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, [discipline_id, data['group'], student_id, data['teacherId'], grade, exam_id])
            conn.commit()
            return jsonify({'success': True})
    except Exception as e:
        print(f"Error in save_exam_grades: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
