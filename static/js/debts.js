document.addEventListener('DOMContentLoaded', function() {
    loadDebts();
});

function loadDebts() {
    fetch(`/api/student/debts?student_id=${window.studentId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            const tableBody = document.querySelector('#debtsTable tbody');
            const emptyState = document.getElementById('emptyState');

            tableBody.innerHTML = '';
            
            if (!data || !Array.isArray(data) || data.length === 0) {
                document.getElementById('debtsTable').classList.add('d-none');
                emptyState.classList.remove('d-none');
            } else {
                document.getElementById('debtsTable').classList.remove('d-none');
                emptyState.classList.add('d-none');
                data.forEach(debt => {
                    const row = document.createElement('tr');
                    row.classList.add('failed');
                    
                    row.innerHTML = `
                        <td>${debt.disciplinename || 'Не указано'}</td>
                        <td>${formatDate(debt.examdate)}</td>
                        <td>${debt.grade || 'Не указано'}</td>
                    `;
                    
                    tableBody.appendChild(row);
                });
            }
        })
        .catch(error => {
            console.error('Error loading debts:', error);
            alert('Ошибка при загрузке задолженностей');
        });
}

function formatDate(dateString) {
    if (!dateString || dateString === 'null' || dateString === 'undefined') {
        return 'Не указано';
    }
    
    const date = new Date(dateString);
    if (isNaN(date.getTime())) {
        return 'Неверная дата';
    }
    
    return date.toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
} 