document.addEventListener('DOMContentLoaded', function() {
    if (window.userRole === "2") {
        loadTeacherGroups();
        setupEventListeners();
    } else { 
        loadGroupGrades();
    }
});

let ratingDisciplines = [];
let ratingIndex = 0;
let lastResolvedGroupName = '';

function setupEventListeners() {
    const groupSelect = document.getElementById('groupSelect');
    if (groupSelect) {
        groupSelect.addEventListener('change', function() {
            if (this.value) {
                loadGroupGrades(this.value);
            }
        });
    }

    const prevBtn = document.getElementById('ratingPrevBtn');
    const nextBtn = document.getElementById('ratingNextBtn');
    if (prevBtn) prevBtn.addEventListener('click', () => flipRating(-1));
    if (nextBtn) nextBtn.addEventListener('click', () => flipRating(1));
}

function loadTeacherGroups() {
    fetch(`/api/teacher/groups?teacher_id=${window.userId}`)
        .then(response => response.json())
        .then(data => {
            const select = document.getElementById('groupSelect');
            select.innerHTML = '<option value="">Выберите группу</option>';
            
            data.forEach(group => {
                const option = document.createElement('option');
                option.value = group;
                option.textContent = group;
                select.appendChild(option);
            });

            if (data.length > 0) {
                select.value = data[0];
                loadGroupGrades(data[0]);
            }
        })
        .catch(error => {
            console.error('Error loading groups:', error);
            alert('Ошибка при загрузке групп');
        });
}

function loadGroupGrades(groupName = null) {
    const url = window.userRole === "2"
        ? `/api/group/grades?group=${encodeURIComponent(groupName)}`
        : `/api/group/grades?student_id=${window.userId}`;

    fetch(url)
        .then(response => response.json())
        .then(data => {
            const tableBody = document.querySelector('#gradesTable tbody');
            const emptyState = document.getElementById('emptyState');

            tableBody.innerHTML = '';
            
            if (data.grades.length === 0) {
                document.getElementById('gradesTable').classList.add('d-none');
                emptyState.classList.remove('d-none');
                initRating([], '');
            } else {
                document.getElementById('gradesTable').classList.remove('d-none');
                emptyState.classList.add('d-none');

                const groupNameResolved = (window.userRole === "2" ? (groupName || '') : (data.groupName || ''));
                lastResolvedGroupName = groupNameResolved;
                const info = document.getElementById('studentGroupInfo');
                const name = document.getElementById('studentGroupName');
                if (window.userRole !== "2" && info && name && groupNameResolved) {
                    name.textContent = groupNameResolved;
                    info.style.display = '';
                }

                data.grades.forEach(grade => {
                    const row = document.createElement('tr');
                    
                    const avgGradeValue = grade.AverageGrade === 'н/а' ? null : parseFloat(grade.AverageGrade);
                    if (avgGradeValue !== null && avgGradeValue < 3) {
                        row.classList.add('low-grade');
                    }

                    const successRateValue = parseFloat(grade.SuccessRate) || 0;
                    
                    row.innerHTML = `
                        <td>${grade.DisciplineName}</td>
                        <td>${grade.AverageGrade}</td>
                        <td>${successRateValue.toFixed(1)}%</td>
                        <td>${grade.AbsenceRate}%</td>
                    `;
                    
                    tableBody.appendChild(row);
                });

                const disciplines = data.grades.map(g => String(g.DisciplineName || '').trim()).filter(Boolean);
                initRating(disciplines, groupNameResolved);
            }

            // Отображение среднего количества пропусков в %
            const avgAbsencesValue = parseFloat(data.averageAbsences) || 0;
            const absencesElement = document.getElementById('averageAbsences');
            absencesElement.textContent = `${avgAbsencesValue.toFixed(1)}%`;
            updateAbsencesVisual(avgAbsencesValue);
            
            if (data.groupName) {
                const info = document.getElementById('studentGroupInfo');
                const name = document.getElementById('studentGroupName');
                if (info && name) {
                    name.textContent = data.groupName;
                    info.style.display = '';
                }
            }
        })
        .catch(error => {
            console.error('Error loading grades:', error);
            alert('Ошибка при загрузке данных');
        });
}

function initRating(disciplines, groupName) {
    ratingDisciplines = Array.isArray(disciplines) ? disciplines : [];
    ratingIndex = 0;
    renderRatingHeader();
    if (!groupName || ratingDisciplines.length === 0) {
        renderRatingTable([]);
        return;
    }
    loadRatingForCurrent();
}

function flipRating(delta) {
    if (!ratingDisciplines.length) return;
    ratingIndex = (ratingIndex + delta + ratingDisciplines.length) % ratingDisciplines.length;
    renderRatingHeader();
    loadRatingForCurrent();
}

function currentRatingDiscipline() {
    if (!ratingDisciplines.length) return '';
    return ratingDisciplines[ratingIndex] || '';
}

function renderRatingHeader() {
    const textSpan = document.getElementById('ratingDisciplineBtn');
    const prevBtn = document.getElementById('ratingPrevBtn');
    const nextBtn = document.getElementById('ratingNextBtn');
    const d = currentRatingDiscipline();
    if (textSpan) textSpan.textContent = d || '-';
    const disabled = !d;
    if (prevBtn) prevBtn.disabled = disabled;
    if (nextBtn) nextBtn.disabled = disabled;
}

function loadRatingForCurrent() {
    const group = lastResolvedGroupName;
    const discipline = currentRatingDiscipline();
    if (!group || !discipline) {
        renderRatingTable([]);
        return;
    }
    fetch(`/api/group/rating?group=${encodeURIComponent(group)}&discipline=${encodeURIComponent(discipline)}`)
        .then(r => r.json())
        .then(data => {
            const rating = Array.isArray(data.rating) ? data.rating : [];
            renderRatingTable(rating);
        })
        .catch(() => renderRatingTable([]));
}

function renderRatingTable(rating) {
    const table = document.getElementById('ratingTable');
    const tbody = table ? table.querySelector('tbody') : null;
    const empty = document.getElementById('ratingEmptyState');
    if (!tbody) return;
    tbody.innerHTML = '';

    if (!Array.isArray(rating) || rating.length === 0) {
        if (table) table.classList.add('d-none');
        if (empty) empty.classList.remove('d-none');
        return;
    }

    if (table) table.classList.remove('d-none');
    if (empty) empty.classList.add('d-none');
    rating.forEach(item => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${item.place}</td>
            <td>${item.studentName}</td>
            <td>${item.averageGrade}</td>
        `;
        tbody.appendChild(tr);
    });
}

async function computeAttendancePercent(discipline, group) {
    try {
        const url = `/api/grades/table?discipline=${encodeURIComponent(discipline)}&group=${encodeURIComponent(group)}`;
        const res = await fetch(url);
        if (!res.ok) return null;
        const data = await res.json();
        const students = Array.isArray(data.students) ? data.students : [];
        if (students.length === 0) return null;

        let conductedLessons = 0;
        students.forEach(st => {
            const grades = st.grades || {};
            Object.entries(grades).forEach(([lessonKey, val]) => {
                if (val && String(val).trim() !== '') {
                    const n = parseInt(lessonKey, 10);
                    if (!Number.isNaN(n)) conductedLessons = Math.max(conductedLessons, n);
                }
            });
        });
        if (conductedLessons <= 0) return 0;

        let presentCount = 0;
        students.forEach(st => {
            const grades = st.grades || {};
            for (let i = 1; i <= conductedLessons; i++) {
                const v = grades[String(i)];
                if (v && v !== 'Н') presentCount += 1;
            }
        });
        const totalCount = conductedLessons * students.length;
        const pct = Math.round((presentCount / totalCount) * 100);
        return isFinite(pct) ? Math.max(0, Math.min(100, pct)) : null;
    } catch (_) {
        return null;
    }
}