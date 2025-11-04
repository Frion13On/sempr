document.addEventListener('DOMContentLoaded', function() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    loadUserData();

    document.getElementById('changePasswordBtn').addEventListener('click', changePassword);
});

function loadUserData() {
    const endpoint = window.userRole === "2" ? '/api/account/teacher' : '/api/account/student';
    
    fetch(`${endpoint}?user_id=${window.userId}`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('userName').textContent = data.name || 'Н/Д';
            document.getElementById('groups').textContent = data.groups || 'Н/Д';
            document.getElementById('department').textContent = data.department || 'Н/Д';
            document.getElementById('faculty').textContent = data.faculty || 'Н/Д';

            if (window.userRole === "3") {
                document.getElementById('specialty').textContent = data.specialty || 'Н/Д';
            }
            if (data.department_info) {
                const deptTooltip = `Заведующий: ${data.department_info.head}\nТелефон: ${data.department_info.phone}\nПочта: ${data.department_info.email}`;
                document.getElementById('department').setAttribute('title', deptTooltip);
            }

            if (data.faculty_info) {
                const facTooltip = `Декан: ${data.faculty_info.dean}\nТелефон: ${data.faculty_info.phone}\nПочта: ${data.faculty_info.email}`;
                document.getElementById('faculty').setAttribute('title', facTooltip);
            }
            var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.forEach(function (tooltipTriggerEl) {
                var tooltip = bootstrap.Tooltip.getInstance(tooltipTriggerEl);
                if (tooltip) {
                    tooltip.dispose();
                }
                new bootstrap.Tooltip(tooltipTriggerEl);
            });
        })
        .catch(error => {
            console.error('Error loading user data:', error);
            document.getElementById('errorAlert').textContent = 'Ошибка при загрузке данных пользователя';
            document.getElementById('errorAlert').style.display = 'block';
        });
}

function changePassword() {
    const newPassword = document.getElementById('newPassword').value;
    
    if (!newPassword) {
        document.getElementById('errorAlert').textContent = 'Введите новый пароль';
        document.getElementById('errorAlert').style.display = 'block';
        return;
    }

    const endpoint = window.userRole === "2" ? '/api/account/teacher/password' : '/api/account/student/password';
    
    fetch(endpoint, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            user_id: window.userId,
            new_password: newPassword
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('successAlert').style.display = 'block';
            document.getElementById('errorAlert').style.display = 'none';
            document.getElementById('newPassword').value = '';
            setTimeout(() => {
                document.getElementById('successAlert').style.display = 'none';
            }, 3000);
        } else {
            throw new Error(data.error || 'Ошибка при изменении пароля');
        }
    })
    .catch(error => {
        document.getElementById('errorAlert').textContent = error.message;
        document.getElementById('errorAlert').style.display = 'block';
        document.getElementById('successAlert').style.display = 'none';
    });
} 