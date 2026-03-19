function _showErrorFallback(message) {
  if (typeof showError === 'function') return showError(message);
  alert(message);
}

function loadTeacherDisciplinesIntoSelect(disciplineSelect, teacherId) {
  if (!disciplineSelect) return;
  return fetch(`/api/teacher/disciplines?teacher_id=${encodeURIComponent(teacherId)}`)
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
      _showErrorFallback('Ошибка при загрузке дисциплин');
    });
}

function loadGroupsIntoDatalist(datalistEl) {
  if (!datalistEl) return;
  return fetch('/api/groups')
    .then(response => response.json())
    .then(data => {
      datalistEl.innerHTML = '';
      data.forEach(group => {
        const option = document.createElement('option');
        option.value = group.название_группы;
        datalistEl.appendChild(option);
      });
    })
    .catch(error => {
      console.error('Error loading groups:', error);
      _showErrorFallback('Ошибка при загрузке групп');
    });
}

function showEmptyStateForTable(tableEl, emptyStateEl) {
  if (tableEl) tableEl.style.display = 'none';
  if (emptyStateEl) emptyStateEl.classList.remove('d-none');
}

function hideEmptyStateForTable(tableEl, emptyStateEl) {
  if (tableEl) tableEl.style.display = 'table';
  if (emptyStateEl) emptyStateEl.classList.add('d-none');
}

function applyGradeColorForInputElement(inputEl) {
  if (!inputEl) return;
  const td = inputEl.closest('td');
  if (!td) return;
  applyGradeClass(td, inputEl.value);
}

