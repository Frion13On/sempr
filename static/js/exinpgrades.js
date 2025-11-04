document.addEventListener('DOMContentLoaded', function() {
    const disciplineSelect = document.getElementById('disciplineSelect');
    const groupInput = document.getElementById('groupInput');
    const loadDataBtn = document.getElementById('loadDataBtn');
    const saveDataBtn = document.getElementById('saveDataBtn');
    const gradesTable = document.getElementById('gradesTable');
    const emptyState = document.getElementById('emptyState');

    loadDataBtn.addEventListener('click', loadExamGrades);
    saveDataBtn.addEventListener('click', saveExamGrades);
    loadTeacherDisciplines();
    loadGroups();

    function loadTeacherDisciplines() {
        fetch(`/api/teacher/disciplines?teacher_id=${window.userId}`)
            .then(response => response.json())
            .then(disciplines => {
                disciplineSelect.innerHTML = '<option value="">Выберите дисциплину</option>';
                disciplines.forEach(discipline => {
                    const option = document.createElement('option');
                    option.value = discipline;
                    option.textContent = discipline;
                    disciplineSelect.appendChild(option);
                });
            })
            .catch(error => {
                console.error('Error loading disciplines:', error);
                alert('Ошибка при загрузке дисциплин');
            });
    }

    function loadGroups() {
        fetch('/api/groups')
            .then(response => response.json())
            .then(data => {
                const datalist = document.getElementById('groupsList');
                datalist.innerHTML = '';
                data.forEach(group => {
                    const option = document.createElement('option');
                    option.value = group.название_группы;
                    datalist.appendChild(option);
                });
            })
            .catch(error => {
                console.error('Error loading groups:', error);
                alert('Ошибка при загрузке групп');
            });
    }

    function loadExamGrades() {
        const discipline = disciplineSelect.value;
        const group = groupInput.value;

        if (!discipline || !group) {
            alert('Пожалуйста, заполните поля "Дисциплина" и "Группа"');
            return;
        }

        fetch(`/api/exam/grades/table?discipline=${encodeURIComponent(discipline)}&group=${encodeURIComponent(group)}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Received data:', data);
                if (!data.students || data.students.length === 0) {
                    showEmptyState();
                    return;
                }

                hideEmptyState();
                createGradeTable(data.students);
            })
            .catch(error => {
                console.error('Error loading exam grades:', error);
                alert('Ошибка при загрузке данных: ' + error.message);
            });
    }

    function createGradeTable(students) {
        console.log('Creating table with students:', students);
        
        const tbody = gradesTable.querySelector('tbody');
        tbody.innerHTML = '';

        students.forEach((student, index) => {
            const tr = document.createElement('tr');
            
            // Номер ячейки
            const tdNumber = document.createElement('td');
            tdNumber.className = 'number-cell';
            tdNumber.textContent = index + 1;
            tr.appendChild(tdNumber);
            
            // Ячейка с именем студента
            const tdName = document.createElement('td');
            tdName.className = 'student-name';
            tdName.textContent = student.name;
            tr.appendChild(tdName);

            // Ячейка с оценкой
            const tdGrade = document.createElement('td');
            tdGrade.className = 'grade-cell';
            const input = document.createElement('input');
            input.type = 'text';
            input.className = 'grade-input';
            input.maxLength = 1;
            input.value = student.grade || '';
            
            input.addEventListener('input', (e) => {
                validateGradeInput(e);
                applyGradeColorForInput(e.target);
            });
            tdGrade.appendChild(input);
            tr.appendChild(tdGrade);

            tbody.appendChild(tr);
        });
        // initial coloring
        tbody.querySelectorAll('.grade-input').forEach(applyGradeColorForInput);
    }

    function validateGradeInput(event) {
        const input = event.target;
        const value = input.value.toUpperCase();
        
        if (value && !isValidGrade(value)) {
            input.value = '';
            return;
        }
        
        input.value = value;
    }

    function isValidGrade(grade) {
        return grade === 'Н' || (grade >= '1' && grade <= '5');
    }

    function applyGradeColorForInput(input) {
        const td = input.closest('td');
        if (!td) return;
        td.classList.remove('grade-good', 'grade-mid', 'grade-warn', 'grade-bad', 'grade-absent');
        const v = input.value.toUpperCase();
        if (!v) return;
        if (v === 'Н') { td.classList.add('grade-absent'); return; }
        const num = parseFloat(v);
        if (Number.isNaN(num)) return;
        if (num >= 5) td.classList.add('grade-good');
        else if (num >= 4) td.classList.add('grade-mid');
        else if (num >= 3) td.classList.add('grade-warn');
        else td.classList.add('grade-bad');
    }

    function saveExamGrades() {
        const discipline = disciplineSelect.value;
        const group = groupInput.value;

        if (!discipline || !group) {
            alert('Пожалуйста, заполните поля "Дисциплина" и "Группа"');
            return;
        }

        // Проверяем, что window.userId существует
        if (!window.userId) {
            alert('Ошибка: ID пользователя не найден. Пожалуйста, перезагрузите страницу.');
            return;
        }

        const grades = [];
        const rows = gradesTable.querySelectorAll('tbody tr');

        if (rows.length === 0) {
            alert('Нет данных для сохранения. Сначала загрузите таблицу оценок.');
            return;
        }

        rows.forEach(row => {
            const studentName = row.querySelector('.student-name').textContent;
            const gradeInput = row.querySelector('.grade-input');
            const grade = gradeInput.value.trim();
            
            if (grade && !isValidGrade(grade)) {
                alert(`Некорректная оценка "${grade}" для студента ${studentName}. Допустимые значения: 1-5, Н`);
                return;
            }
            
            grades.push({
                studentName,
                grade: grade
            });
        });

        // Показываем индикатор загрузки
        saveDataBtn.disabled = true;
        saveDataBtn.textContent = 'Сохранение...';

        console.log('Sending exam data:', {
            discipline,
            group,
            teacherId: window.userId,
            gradesCount: grades.length
        });

        fetch('/api/exam/grades/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                discipline,
                group,
                teacherId: window.userId,
                grades
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(result => {
            if (result.success) {
                alert('Оценки успешно сохранены');
            } else {
                throw new Error(result.error || 'Ошибка при сохранении');
            }
        })
        .catch(error => {
            console.error('Error saving grades:', error);
            alert('Ошибка при сохранении оценок: ' + error.message);
        })
        .finally(() => {
            // Восстанавливаем кнопку
            saveDataBtn.disabled = false;
            saveDataBtn.textContent = 'Сохранить оценки';
        });
    }

    function showEmptyState() {
        gradesTable.style.display = 'none';
        emptyState.classList.remove('d-none');
    }

    function hideEmptyState() {
        gradesTable.style.display = 'table';
        emptyState.classList.add('d-none');
    }
}); 