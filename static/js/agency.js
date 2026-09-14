// --- Theme & Language ---
const themeStorageKey = 'softexpress-theme';
let theme = localStorage.getItem(themeStorageKey) || 'dark';
document.documentElement.setAttribute('data-theme', theme);
document.documentElement.setAttribute('data-bs-theme', theme);
document.documentElement.classList.toggle('dark', theme === 'dark');
document.documentElement.classList.toggle('light', theme === 'light');

function toggleTheme() {
    theme = theme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', theme);
    document.documentElement.setAttribute('data-bs-theme', theme);
    document.documentElement.classList.toggle('dark', theme === 'dark');
    document.documentElement.classList.toggle('light', theme === 'light');
    localStorage.setItem(themeStorageKey, theme);
}

function setLang(l) {
    localStorage.setItem('softexpress-language', l);
    // Basic i18n switcher - adds class for transition effect
    document.body.classList.add('fading');
    setTimeout(() => {
        document.documentElement.lang = l;
        // In a real app, you'd trigger a reload or update text via a JSON dictionary
        document.body.classList.remove('fading');
    }, 150);
}

// --- Modal Logic ---
function openModal() { document.getElementById('modal').style.display = 'block'; }
window.onclick = function(event) {
    const modal = document.getElementById('modal');
    if (event.target === modal) modal.style.display = 'none';
}