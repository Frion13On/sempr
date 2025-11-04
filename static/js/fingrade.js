document.addEventListener('DOMContentLoaded', function() {
    loadTeacherDisciplines();
    loadGroups();
    setupEventListeners();
});

function setupEventListeners() {
    const loadDataBtn = document.getElementById('loadDataBtn');
    if (loadDataBtn) {
        loadDataBtn.addEventListener('click', loadFinalGrades);
    }
}

function loadTeacherDisciplines() {
    fetch(`/api/teacher/disciplines?teacher_id=${window.userId}`)
        .then(response => response.json())
        .then(data => {
            const select = document.getElementById('disciplineSelect');
            select.innerHTML = '<option value="">Выберите дисциплину</option>';
            
            data.forEach(discipline => {
                const option = document.createElement('option');
                option.value = discipline;
                option.textContent = discipline;
                select.appendChild(option);
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

function loadFinalGrades() {
    const discipline = document.getElementById('disciplineSelect').value;
    const group = document.getElementById('groupInput').value;

    if (!discipline || !group) {
        alert('Заполните поля "Дисциплина" и "Группа"');
        return;
    }

    fetch(`/api/final/grades?discipline=${encodeURIComponent(discipline)}&group=${encodeURIComponent(group)}`)
        .then(response => response.json())
        .then(data => {
            const tableBody = document.querySelector('#gradesTable tbody');
            const emptyState = document.getElementById('emptyState');

            tableBody.innerHTML = '';
            
            if (data.length === 0) {
                document.getElementById('gradesTable').classList.add('d-none');
                emptyState.classList.remove('d-none');
            } else {
                document.getElementById('gradesTable').classList.remove('d-none');
                emptyState.classList.add('d-none');
                
                data.forEach(student => {
                    const row = document.createElement('tr');
                    const gradeNum = parseFloat(student.finalGrade);
                    if (student.finalGrade === 'н/а' || (!Number.isNaN(gradeNum) && gradeNum < 3)) {
                        row.classList.add('low-grade');
                    }

                    const nameTd = document.createElement('td');
                    nameTd.textContent = student.studentName;
                    const gradeTd = document.createElement('td');
                    gradeTd.textContent = student.finalGrade;
                    applyGradeColorClass(gradeTd, student.finalGrade);

                    row.appendChild(nameTd);
                    row.appendChild(gradeTd);
                    tableBody.appendChild(row);
                });
            }
        })
        .catch(error => {
            console.error('Error loading final grades:', error);
            alert('Ошибка при загрузке итоговых оценок');
        });
} 

function applyGradeColorClass(cell, value) {
    cell.classList.remove('grade-good', 'grade-mid', 'grade-warn', 'grade-bad', 'grade-absent');
    const v = String(value).trim();
    if (v.toLowerCase() === 'н/а') { cell.classList.add('grade-bad'); return; }
    if (v.toUpperCase() === 'Н') { cell.classList.add('grade-absent'); return; }
    const num = parseFloat(v);
    if (Number.isNaN(num)) return;
    if (num >= 5) cell.classList.add('grade-good');
    else if (num >= 4) cell.classList.add('grade-mid');
    else if (num >= 3) cell.classList.add('grade-warn');
    else cell.classList.add('grade-bad');
}