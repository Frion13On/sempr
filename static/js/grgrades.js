document.addEventListener('DOMContentLoaded', function() {
    if (window.userRole === "2") {
        loadTeacherGroups();
        setupEventListeners();
    } else { 
        loadGroupGrades();
    }
});

function setupEventListeners() {
    const groupSelect = document.getElementById('groupSelect');
    if (groupSelect) {
        groupSelect.addEventListener('change', function() {
            if (this.value) {
                loadGroupGrades(this.value);
            }
        });
    }
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
            } else {
                document.getElementById('gradesTable').classList.remove('d-none');
                emptyState.classList.add('d-none');

                const groupNameResolved = (window.userRole === "2" ? (groupName || '') : (data.groupName || ''));
                const info = document.getElementById('studentGroupInfo');
                const name = document.getElementById('studentGroupName');
                if (window.userRole !== "2" && info && name && groupNameResolved) {
                    name.textContent = groupNameResolved;
                    info.style.display = '';
                }

                data.grades.forEach(grade => {
                    const row = document.createElement('tr');
                    if (parseFloat(grade.AverageGrade) < 3) {
                        row.classList.add('low-grade');
                    }
                    
                    const attendance = grade.AttendancePercent ?? grade.Attendance ?? grade.AttendanceRate;
                    let attendanceDisplay = (attendance || attendance === 0)
                        ? `${Number(attendance).toFixed(0)}%` : '-';

                    row.innerHTML = `
                        <td>${grade.DisciplineName}</td>
                        <td>${grade.AverageGrade}</td>
                        <td>${attendanceDisplay}</td>
                    `;
                    
                    tableBody.appendChild(row);
                });

                if (groupNameResolved) {
                    const rows = tableBody.querySelectorAll('tr');
                    rows.forEach((tr) => {
                        const disciplineName = tr.children[0]?.textContent?.trim();
                        const percentCell = tr.children[2];
                        if (percentCell && percentCell.textContent.trim() === '-') {
                            computeAttendancePercent(disciplineName, groupNameResolved)
                                .then((pct) => { percentCell.textContent = pct !== null ? `${pct}%` : '-'; })
                                .catch(() => {});
                        }
                    });
                }
            }

            document.getElementById('averageAbsences').textContent = data.averageAbsences;
            if (data.groupName) {
                const info = document.getElementById('studentGroupInfo');
                const name = document.getElementById('studentGroupName');
                if (info && name) {
                    name.textContent = data.groupName;
                    info.style.display = '';
                }
            }
            updateAbsencesVisual(Number(data.averageAbsences));
        })
        .catch(error => {
            console.error('Error loading grades:', error);
            alert('Ошибка при загрузке данных');
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