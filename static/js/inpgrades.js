document.addEventListener('DOMContentLoaded', function() {
    const disciplineSelect = document.getElementById('disciplineSelect');
    const groupInput = document.getElementById('groupInput');
    const loadDataBtn = document.getElementById('loadDataBtn');
    const saveDataBtn = document.getElementById('saveDataBtn');
    const gradesTable = document.getElementById('gradesTable');
    const emptyState = document.getElementById('emptyState');

    loadDataBtn.addEventListener('click', loadGradeTable);
    saveDataBtn.addEventListener('click', saveGrades);

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

    function loadGradeTable() {
        const discipline = disciplineSelect.value;
        const group = groupInput.value;

        if (!discipline || !group) {
            alert('Пожалуйста, заполните поля "Дисциплина" и "Группа"');
            return;
        }

        fetch(`/api/grades/table?discipline=${encodeURIComponent(discipline)}&group=${encodeURIComponent(group)}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Received data:', data); // Debug
                if (!data.numberOfLessons || !data.students || data.students.length === 0) {
                    showEmptyState();
                    return;
                }

                hideEmptyState();
                createGradeTable(data.numberOfLessons, data.students);
            })
            .catch(error => {
                console.error('Error loading grade table:', error);
                alert('Ошибка при загрузке данных: ' + error.message);
            });
    }

    function createGradeTable(numberOfLessons, students) {
        console.log('Creating table with students:', students); // Debug

        const thead = gradesTable.querySelector('thead tr');
        thead.innerHTML = '<th class="student-name">ФИО студента</th>';

        for (let i = 1; i <= numberOfLessons; i++) {
            const th = document.createElement('th');
            th.textContent = i;
            thead.appendChild(th);
        }

        const thAbsences = document.createElement('th');
        thAbsences.textContent = 'Пропуски';
        thAbsences.className = 'absences-cell';
        thead.appendChild(thAbsences);

        const tbody = gradesTable.querySelector('tbody');
        tbody.innerHTML = '';

        students.forEach(student => {
            console.log('Processing student:', student); // Debug
            const tr = document.createElement('tr');
            
            const tdName = document.createElement('td');
            tdName.className = 'student-name';
            tdName.textContent = student.name;
            tr.appendChild(tdName);

            for (let i = 1; i <= numberOfLessons; i++) {
                const td = document.createElement('td');
                td.className = 'lesson-cell';
                
                const input = document.createElement('input');
                input.type = 'text';
                input.className = 'grade-input';
                input.maxLength = 1;
                input.dataset.lessonNumber = i;

                const lessonKey = i.toString();
                const grade = student.grades[lessonKey];
                input.value = grade !== undefined ? grade : '';

                if (student.teachers && student.teachers[lessonKey]) {
                    input.title = `Поставил: ${student.teachers[lessonKey]}`;
                } else if (grade) {
                    input.title = `Оценка: ${grade}`;
                }
                
                input.addEventListener('input', (e) => {
                    validateGradeInput(e);
                    applyGradeColorForInput(e.target);
                });
                td.appendChild(input);
                tr.appendChild(td);
            }

            const tdAbsences = document.createElement('td');
            tdAbsences.className = 'absences-cell';
            tdAbsences.textContent = student.absences || calculateAbsences(student.grades);
            tr.appendChild(tdAbsences);

            tbody.appendChild(tr);
        });

        tbody.querySelectorAll('.grade-input').forEach(applyGradeColorForInput);
    }

    function calculateAbsences(grades) {
        return Object.values(grades).filter(grade => grade === 'Н').length;
    }

    function validateGradeInput(event) {
        const input = event.target;
        const normalized = normalizeGradeValue(input.value);
        input.value = normalized;
        updateAbsences(input);
    }

    function applyGradeColorForInput(input) {
        const td = input.closest('td');
        if (!td) return;
        applyGradeClass(td, input.value);
    }

    function updateAbsences(input) {
        const row = input.closest('tr');
        const inputs = row.querySelectorAll('.grade-input');
        const absencesCell = row.querySelector('.absences-cell');
        const absences = Array.from(inputs).filter(input => input.value === 'Н').length;
        absencesCell.textContent = absences;
    }

    function saveGrades() {
        const discipline = disciplineSelect.value;
        const group = groupInput.value;
    
        if (!discipline || !group) {
            alert('Пожалуйста, заполните поля "Дисциплина" и "Группа"');
            return;
        }
    
        if (!window.userId) {
            alert('Ошибка: ID пользователя не найден. Пожалуйста, перезагрузите страницу.');
            return;
        }
    
        const rows = gradesTable.querySelectorAll('tbody tr');
        if (rows.length === 0) {
            alert('Нет данных для сохранения. Сначала загрузите таблицу оценок.');
            return;
        }
    
        const grades = [];
    
        rows.forEach(row => {
            const studentName = row.querySelector('.student-name').textContent.trim();
            const inputs = row.querySelectorAll('.grade-input');
            const studentGrades = {};
    
            inputs.forEach(input => {
                const grade = normalizeGradeValue(input.value);
                studentGrades[input.dataset.lessonNumber] = grade || null;
            });
    
            grades.push({
                studentName,
                grades: studentGrades
            });
        });
    
        saveDataBtn.disabled = true;
        saveDataBtn.textContent = 'Сохранение...';
    
        const payload = { discipline, group, teacherId: window.userId, grades };
        console.log('Payload to send:', payload);
    
        fetch('/api/grades/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(async response => {
            const text = await response.text();
            try {
                const data = JSON.parse(text);
                if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
                alert('Оценки успешно сохранены');
                return data;
            } catch(e) {
                throw new Error(`Server returned non-JSON: ${text}`);
            }
        })
        .catch(err => {
            console.error('Error saving grades:', err);
            alert('Ошибка при сохранении оценок: ' + err.message);
        })
        .finally(() => {
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