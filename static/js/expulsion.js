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
            headers: window.withCsrfHeader({ 'Content-Type': 'application/json' }),
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
        showMessage(message);
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
        const offset = window.userRole === "1" ? 1 : 0;
        const sorted = sortRows(
            rows,
            row => (row.cells[idx + offset] ? row.cells[idx + offset].textContent : ''),
            sortState.dir
        );
        reattachRows(tbody, sorted);
    }

    function exportToExcel() {
        console.log('exportToExcel function started');
        const expulsionTable = document.getElementById('expulsionTable');
        const tbody = expulsionTable.querySelector('tbody');

        if (!tbody || tbody.rows.length === 0) {
            console.error('No data to export');
            showError('Нет данных для экспорта');
            return;
        }

        // Determine which columns to skip (checkbox column for admin)
        const skipColumns = window.userRole === "1" ? [0] : [];

        // Extract data using utility function
        const data = extractTableData(expulsionTable, { skipColumns });
        
        // Calculate column widths
        const columnWidths = [
            { wch: 25 },  // ФИО
            { wch: 15 },  // Группа
            { wch: 12 }   // Долги
        ];

        // Generate filename
        const date = new Date().toISOString().split('T')[0];
        const filename = `список_на_отчисление_${date}.xlsx`;
        
        console.log('Writing file:', filename);
        // Export using utility function
        exportTableToExcel(data, filename, 'На отчисление', columnWidths);
    }
}); 