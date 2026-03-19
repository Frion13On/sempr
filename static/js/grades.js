document.addEventListener('DOMContentLoaded', function() {
    loadDisciplines();
    setupEventListeners();
});

function setupEventListeners() {
    document.getElementById('loadGradesBtn').addEventListener('click', loadGrades);
}

async function loadDisciplines() {
    try {
        const data = await apiGetJson(`/api/student/disciplines?student_id=${window.studentId}`);
        const select = document.getElementById('disciplineSelect');
        select.innerHTML = '<option value="">Выберите дисциплину</option>';
        data.forEach(discipline => {
            const option = document.createElement('option');
            option.value = discipline;
            option.textContent = discipline;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading disciplines:', error);
        notifyError('Ошибка при загрузке дисциплин');
    }
}

async function loadGrades() {
    const disciplineName = document.getElementById('disciplineSelect').value;
    if (!disciplineName) {
        alert('Выберите дисциплину');
        return;
    }

    try {
        const data = await apiGetJson(`/api/student/grades?student_id=${window.studentId}&discipline=${encodeURIComponent(disciplineName)}`);
        const tableBody = document.querySelector('#gradesTable tbody');
        const emptyState = document.getElementById('emptyState');

        tableBody.innerHTML = '';

        if (data.grades.length === 0) {
            document.getElementById('gradesTable').classList.add('d-none');
            emptyState.classList.remove('d-none');
        } else {
            document.getElementById('gradesTable').classList.remove('d-none');
            emptyState.classList.add('d-none');

            data.grades.forEach(grade => {
                const row = document.createElement('tr');
                const tdNum = document.createElement('td');
                tdNum.textContent = grade.LessonNumber;
                const tdGrade = document.createElement('td');
                tdGrade.textContent = grade.Grade;
                applyGradeCellClass(tdGrade, grade.Grade);

                row.appendChild(tdNum);
                row.appendChild(tdGrade);
                tableBody.appendChild(row);
            });
        }

        updateStats(data.stats);
    } catch (error) {
        console.error('Error loading grades:', error);
        notifyError('Ошибка при загрузке оценок');
    }
}

function updateStats(stats) {
    document.getElementById('finalGrade').textContent = stats.finalGrade;
    document.getElementById('gradesCount').textContent = stats.gradesCount;
    document.getElementById('absencesCount').textContent = stats.absencesCount;
} 

function applyGradeCellClass(cell, value) {
    applyGradeClass(cell, value);
}