(function() {
    const html = document.documentElement;
    const savedTheme = localStorage.getItem('theme') || 'light';
    html.setAttribute('data-theme', savedTheme);

    document.addEventListener('DOMContentLoaded', () => {
        const toggleBtn = document.getElementById('theme-toggle');
        if (!toggleBtn) return;
        const icon = document.createElement('i');
        icon.id = 'theme-icon';
        icon.className = savedTheme === 'light' ? 'bi bi-moon fs-4' : 'bi bi-sun fs-4';
        icon.setAttribute('aria-label', savedTheme === 'light' ? 'Тёмная тема' : 'Светлая тема');
        toggleBtn.appendChild(icon);

        toggleBtn.addEventListener('click', () => {
            const currentTheme = html.getAttribute('data-theme') || 'light';
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';

            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);

            icon.className = newTheme === 'light' ? 'bi bi-moon fs-4' : 'bi bi-sun fs-4';
            icon.setAttribute('aria-label', newTheme === 'light' ? 'Тёмная тема' : 'Светлая тема');
        });
    });
})();
