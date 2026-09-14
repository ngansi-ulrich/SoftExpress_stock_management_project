(function () {
    const storageKey = 'softexpress-theme';

    function applyTheme(theme) {
        const root = document.documentElement;
        const isDark = theme === 'dark';

        root.setAttribute('data-theme', isDark ? 'dark' : 'light');
        root.setAttribute('data-bs-theme', isDark ? 'dark' : 'light');
        root.classList.toggle('dark', isDark);
        root.classList.toggle('light', !isDark);

        const button = document.getElementById('themeToggle');
        if (!button) return;

        const icon = button.querySelector('i');
        if (icon) {
            icon.classList.toggle('bi-moon-stars-fill', !isDark);
            icon.classList.toggle('bi-sun-fill', isDark);
        }
        button.setAttribute('aria-label', isDark ? 'Switch to light theme' : 'Switch to dark theme');
        button.title = isDark ? 'Switch to light theme' : 'Switch to dark theme';
    }

    function getSavedTheme() {
        const saved = localStorage.getItem(storageKey);
        return saved === 'light' || saved === 'dark' ? saved : 'dark';
    }

    const initialTheme = getSavedTheme();
    applyTheme(initialTheme);

    document.addEventListener('DOMContentLoaded', function () {
        const button = document.getElementById('themeToggle');
        if (!button) return;

        button.addEventListener('click', function () {
            const current = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
            const next = current === 'dark' ? 'light' : 'dark';
            localStorage.setItem(storageKey, next);
            applyTheme(next);
        });
    });
})();
