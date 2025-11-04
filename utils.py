"""
Вспомогательные функции для приложения
"""

def validate_grade(grade):
    """
    Проверяет валидность оценки
    Возвращает True если оценка валидна, False в противном случае
    """
    if not grade:
        return True  
    
    grade = grade.strip()
    if grade == 'Н':  
        return True
    if grade.isdigit() and 1 <= int(grade) <= 5:
        return True
    
    return False

def format_date(date_obj):
    """
    Форматирует дату в строку YYYY-MM-DD
    """
    if date_obj:
        return date_obj.strftime('%Y-%m-%d')
    return None

def calculate_average_grade(grades):
    """
    Вычисляет среднюю оценку из списка оценок
    Исключает неявки (Н) и нечисловые значения
    """
    numeric_grades = []
    for grade in grades:
        if grade and grade.strip().isdigit():
            numeric_grades.append(int(grade.strip()))
    
    if numeric_grades:
        return sum(numeric_grades) / len(numeric_grades)
    return None

def count_absences(grades):
    """
    Подсчитывает количество неявок в списке оценок
    """
    return sum(1 for grade in grades if grade and grade.strip() == 'Н')

def is_valid_email(email):
    """
    Простая проверка валидности email
    """
    if not email:
        return False
    return '@' in email and '.' in email.split('@')[-1]

def is_valid_phone(phone):
    """
    Простая проверка валидности телефона
    """
    if not phone:
        return False
    digits_only = ''.join(filter(str.isdigit, phone))
    return len(digits_only) >= 10
