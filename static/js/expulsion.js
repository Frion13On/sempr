document.addEventListener('DOMContentLoaded', function() {
    const expulsionTable = document.getElementById('expulsionTable').getElementsByTagName('tbody')[0];
    const selectAllCheckbox = document.getElementById('selectAll');
    const expelBtn = document.getElementById('expelBtn');
    const reloadBtn = document.getElementById('reloadBtn');

    let sortState = { index: window.userRole === "1" ? 1 : 0, dir: 'asc' };
    loadData();

    if (window.userRole === "1") {
        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', function() {
                const checkboxes = expulsionTable.querySelectorAll('input[type="checkbox"]');
                checkboxes.forEach(checkbox => checkbox.checked = this.checked);
                updateSelectedRows();
            });
        }

        if (expelBtn) {
            expelBtn.addEventListener('click', expelStudents);
        }
    }

    if (reloadBtn) {
        reloadBtn.addEventListener('click', loadData);
    }

    function loadData() {
        fetch('/api/expulsion')
            .then(response => {
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                return response.json();
            })
            .then(data => {
                expulsionTable.innerHTML = '';
                data.forEach(student => {
                    const row = expulsionTable.insertRow();
                    let cellIndex = 0;

                    if (window.userRole === "1") {
                        const checkboxCell = row.insertCell(cellIndex++);
                        checkboxCell.innerHTML = `
                            <div class="form-check">
                                <input class="form-check-input student-checkbox" type="checkbox" value="${student.id_студ}">
                            </div>
                        `;
                    }

                    row.insertCell(cellIndex++).textContent = student.ФИО;
                    row.insertCell(cellIndex++).textContent = student.название_группы;
                    row.insertCell(cellIndex).textContent = student.Количество_долгов;
                });

                if (window.userRole === "1") {
                    expulsionTable.querySelectorAll('.student-checkbox').forEach(checkbox => {
                        checkbox.addEventListener('change', updateSelectedRows);
                    });
                }
                attachHeaderSorting();
                applySort();
            })
            .catch(error => showError('Ошибка при загрузке данных: ' + error.message));
    }

    function updateSelectedRows() {
        const checkboxes = expulsionTable.querySelectorAll('.student-checkbox');
        const checkedBoxes = expulsionTable.querySelectorAll('.student-checkbox:checked');
        
        if (selectAllCheckbox) {
            selectAllCheckbox.checked = checkboxes.length === checkedBoxes.length;
        }
        
        checkboxes.forEach(checkbox => {
            const row = checkbox.closest('tr');
            if (checkbox.checked) {
                row.classList.add('selected');
            } else {
                row.classList.remove('selected');
            }
        });

        if (expelBtn) {
            expelBtn.disabled = checkedBoxes.length === 0;
        }
    }

    function expelStudents() {
        const selectedIds = Array.from(expulsionTable.querySelectorAll('.student-checkbox:checked'))
            .map(checkbox => checkbox.value);

        if (!selectedIds.length) {
            showError('Выберите студентов для отчисления');
            return;
        }

        if (!confirm(`Отчислить выбранных студентов (${selectedIds.length})?`)) return;

        fetch('/api/expulsion', {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ student_ids: selectedIds })
        })
        .then(response => {
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return response.json();
        })
        .then(result => {
            if (result.success) {
                showInfo('Студенты отчислены');
                loadData();
            } else {
                throw new Error(result.error || 'Ошибка при отчислении');
            }
        })
        .catch(error => showError('Ошибка при отчислении: ' + error.message));
    }

    function showInfo(message) {
        alert(message);
    }

    function showError(message) {
        alert(message);
    }

    function attachHeaderSorting() {
        const thead = document.querySelector('#expulsionTable thead tr');
        if (!thead) return;
        Array.from(thead.children).forEach((th, idx) => {

            if (window.userRole === "1" && idx === 0) return;
            th.style.cursor = 'pointer';
            th.dataset.index = String(idx);

            let ind = th.querySelector('.sort-ind');
            if (!ind) {
                ind = document.createElement('span');
                ind.className = 'ms-1 sort-ind';
                ind.style.fontSize = '0.8em';
                th.appendChild(ind);
            }
            th.addEventListener('click', () => {
                const visibleIdx = window.userRole === "1" ? idx - 1 : idx;
                if (sortState.index !== visibleIdx) {
                    sortState = { index: visibleIdx, dir: 'asc' };
                } else {
                    sortState.dir = sortState.dir === 'asc' ? 'desc' : 'asc';
                }
                applySort();
                updateIndicators();
            });
        });
        updateIndicators();
    }

    function updateIndicators() {
        const thead = document.querySelector('#expulsionTable thead tr');
        if (!thead) return;
        Array.from(thead.children).forEach((th, idx) => {
            if (window.userRole === "1" && idx === 0) return;
            const ind = th.querySelector('.sort-ind');
            if (ind) ind.textContent = '';
        });
        const targetIdx = (window.userRole === "1") ? sortState.index + 1 : sortState.index;
        const active = thead.children[targetIdx];
        if (active) {
            const ind = active.querySelector('.sort-ind');
            if (ind) ind.textContent = sortState.dir === 'asc' ? '▲' : '▼';
        }
    }

    function applySort() {
        const tbody = document.querySelector('#expulsionTable tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const idx = sortState.index;
        const dirMul = sortState.dir === 'asc' ? 1 : -1;
        const collator = new Intl.Collator('ru', { numeric: true, sensitivity: 'base' });
        rows.sort((a, b) => {
            const offset = window.userRole === "1" ? 1 : 0;
            const va = (a.cells[idx + offset] ? a.cells[idx + offset].textContent.trim() : '') || '';
            const vb = (b.cells[idx + offset] ? b.cells[idx + offset].textContent.trim() : '') || '';
            const na = parseFloat(va.replace(',', '.'));
            const nb = parseFloat(vb.replace(',', '.'));
            const isNum = !isNaN(na) && !isNaN(nb) && va !== '' && vb !== '';
            let cmp = 0;
            if (isNum) cmp = na === nb ? 0 : (na < nb ? -1 : 1);
            else cmp = collator.compare(va, vb);
            return cmp * dirMul;
        });
        const frag = document.createDocumentFragment();
        rows.forEach(r => frag.appendChild(r));
        tbody.appendChild(frag);
    }
}); 