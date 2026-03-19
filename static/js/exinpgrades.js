document.addEventListener('DOMContentLoaded', function() {
    const disciplineSelect = document.getElementById('disciplineSelect');
    const groupInput = document.getElementById('groupInput');
    const loadDataBtn = document.getElementById('loadDataBtn');
    const saveDataBtn = document.getElementById('saveDataBtn');
    const gradesTable = document.getElementById('gradesTable');
    const emptyState = document.getElementById('emptyState');

    loadDataBtn.addEventListener('click', loadExamGrades);
    saveDataBtn.addEventListener('click', saveExamGrades);
    const exportBtn = document.getElementById('exportBtn');
    if (exportBtn) {
        exportBtn.addEventListener('click', function() {
            console.log('Export button clicked');
            console.log('XLSX available:', typeof XLSX !== 'undefined');
            exportToExcel();
        });
    } else {
        console.warn('Export button not found');
    }
    loadTeacherDisciplinesIntoSelect(disciplineSelect, window.userId);
    loadGroupsIntoDatalist(document.getElementById('groupsList'));

    function loadExamGrades() {
        const discipline = disciplineSelect.value;
        const group = groupInput.value;

        if (!discipline || !group) {
            showError('Пожалуйста, заполните поля "Дисциплина" и "Группа"');
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
                    showEmptyStateForTable(gradesTable, emptyState);
                    return;
                }

                hideEmptyStateForTable(gradesTable, emptyState);
                createGradeTable(data.students);
            })
            .catch(error => {
                console.error('Error loading exam grades:', error);
                showError('Ошибка при загрузке данных: ' + error.message);
            });
    }

    function createGradeTable(students) {
        console.log('Creating table with students:', students);
        
        const tbody = gradesTable.querySelector('tbody');
        tbody.innerHTML = '';

        students.forEach((student, index) => {
            const tr = document.createElement('tr');
            
            const tdNumber = document.createElement('td');
            tdNumber.className = 'number-cell';
            tdNumber.textContent = index + 1;
            tr.appendChild(tdNumber);
            
            const tdName = document.createElement('td');
            tdName.className = 'student-name';
            tdName.textContent = student.name;
            tr.appendChild(tdName);

            const tdGrade = document.createElement('td');
            tdGrade.className = 'grade-cell';
            const input = document.createElement('input');
            input.type = 'text';
            input.className = 'grade-input';
            input.maxLength = 1;
            input.value = student.grade || '';
            
            input.addEventListener('input', (e) => {
                validateGradeInput(e);
                applyGradeColorForInputElement(e.target);
            });
            tdGrade.appendChild(input);
            tr.appendChild(tdGrade);

            tbody.appendChild(tr);
        });
        tbody.querySelectorAll('.grade-input').forEach(applyGradeColorForInputElement);
    }

    function validateGradeInput(event) {
        const input = event.target;
        const normalized = normalizeGradeValue(input.value);
        input.value = normalized;
    }

    function saveExamGrades() {
        const discipline = disciplineSelect.value;
        const group = groupInput.value;

        if (!discipline || !group) {
            showError('Пожалуйста, заполните поля "Дисциплина" и "Группа"');
            return;
        }

        if (!window.userId) {
            showError('Ошибка: ID пользователя не найден. Пожалуйста, перезагрузите страницу.');
            return;
        }

        const grades = [];
        const rows = gradesTable.querySelectorAll('tbody tr');

        if (rows.length === 0) {
            showError('Нет данных для сохранения. Сначала загрузите таблицу оценок.');
            return;
        }

        rows.forEach(row => {
            const studentName = row.querySelector('.student-name').textContent;
            const gradeInput = row.querySelector('.grade-input');
            const grade = normalizeGradeValue(gradeInput.value);
            
            grades.push({
                studentName,
                grade: grade
            });
        });

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
                ...window.withCsrfHeader({ 'Content-Type': 'application/json' }),
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
                showMessage('Оценки успешно сохранены');
            } else {
                throw new Error(result.error || 'Ошибка при сохранении');
            }
        })
        .catch(error => {
            console.error('Error saving grades:', error);
            showError('Ошибка при сохранении оценок: ' + error.message);
        })
        .finally(() => {
            saveDataBtn.disabled = false;
            saveDataBtn.textContent = 'Сохранить оценки';
        });
    }

    function exportToExcel() {
        console.log('exportToExcel function started');
        const discipline = disciplineSelect.value;
        const group = groupInput.value;

        if (!discipline || !group) {
            showError('Пожалуйста, заполните поля "Дисциплина" и "Группа"');
            return;
        }

        if (!gradesTable.querySelector('tbody').rows || gradesTable.querySelector('tbody').rows.length === 0) {
            showError('Нет данных для экспорта. Сначала загрузите таблицу оценок.');
            return;
        }

        // Extract data using utility function
        const data = extractTableData(gradesTable, { skipColumns: [] });
        
        // Calculate column widths
        const headers = data[0] || [];
        const columnWidths = headers.map(h => ({ wch: Math.max(h.length + 2, 15) }));
        if (columnWidths.length > 1) {
            columnWidths[1] = { wch: 25 };
        }

        // Generate filename
        const date = new Date().toISOString().split('T')[0];
        const filename = `экзамены_${discipline}_${group}_${date}.xlsx`;
        
        // Export using utility function
        exportTableToExcel(data, filename, 'Экзамены', columnWidths);
    }
}); 