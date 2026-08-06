/* ══════════════════════════════════════════
   i18n DICTIONARY
══════════════════════════════════════════ */
const DICT = {
  fr: {
    appSub:      'Gestion Multi-Agences',
    sectionLabel:'Connexion',
    errorText:   'Identifiants incorrects. Veuillez réessayer.',
    labelAgency: 'Agence',
    agencyPh:    'Sélectionner une agence…',
    Yaounde:    'Agence Yaoundé',
    Douala:    'Agence Douala',
    Bafoussam:    'Agence Bafoussam',
    labelUser:   'Identifiant',
    userPh:      'Votre identifiant',
    labelPw:     'Mot de passe',
    toggleTitle: 'Afficher / Masquer',
    rememberMe:  'Se souvenir de moi',
    forgotPw:    'Mot de passe oublié ?',
    btnLogin:    'Se connecter',
    btnOk:       '✓ Connecté',
    divider:     'Sécurisé par VPN',
    footer1:     'Plateforme réservée aux',
    footer2:     ' utilisateurs autorisés',
    footer3:     'Toute tentative non autorisée sera enregistrée',
    docTitle:    'Connexion — Gestion de Stock',
  },
  en: {
    appSub:      'Multi-Agency Management',
    sectionLabel:'Sign In',
    errorText:   'Incorrect credentials. Please try again.',
    labelAgency: 'Agency',
    agencyPh:    'Select an agency…',
    Yaounde:    'Yaounde agency',
    Douala:    'Douala agency ',
    Bafoussam:    'Bafoussam agency',
    labelUser:   'Username',
    userPh:      'Your username',
    labelPw:     'Password',
    toggleTitle: 'Show / Hide',
    rememberMe:  'Remember me',
    forgotPw:    'Forgot password?',
    btnLogin:    'Sign In',
    btnOk:       '✓ Signed In',
    divider:     'Secured by VPN',
    footer1:     'Platform reserved for',
    footer2:     ' authorized users',
    footer3:     'Any unauthorized attempt will be recorded',
    docTitle:    'Login — Stock Management',
  }
};

/* ══════════════════════════════════════════
   STATE
══════════════════════════════════════════ */
let lang  = 'fr';
let theme = 'dark';

/* ══════════════════════════════════════════
   LANGUAGE SWITCHER
══════════════════════════════════════════ */
function setLang(l) {
  if (l === lang) return;
  lang = l;
  const t = DICT[l];

  document.body.classList.add('fading');
  setTimeout(() => {
    /* text content nodes */
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const k = el.getAttribute('data-i18n');
      if (t[k] != null) el.textContent = t[k];
    });
    /* input placeholders */
    document.querySelectorAll('[data-i18n-ph]').forEach(el => {
      const k = el.getAttribute('data-i18n-ph');
      if (t[k] != null) el.placeholder = t[k];
    });
    /* agency first option */
    const sel = document.getElementById('agency');
    if (sel && sel.options[0]) sel.options[0].textContent = t.agencyPh;
    /* password toggle title */
    const tpb = document.getElementById('togglePwBtn');
    if (tpb) tpb.title = t.toggleTitle;
    /* page title & html lang */
    document.title = t.docTitle;
    document.documentElement.lang = l;
    /* active button state */
    document.getElementById('btnFR').classList.toggle('active', l === 'fr');
    document.getElementById('btnEN').classList.toggle('active', l === 'en');

    document.body.classList.remove('fading');
  }, 130);
}

/* ══════════════════════════════════════════
   THEME SWITCHER
══════════════════════════════════════════ */
function toggleTheme() {
  theme = theme === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('smTheme', theme);
}

/* Restore saved theme on load */
(function initTheme() {
  const saved = localStorage.getItem('smTheme');
  if (saved && saved !== theme) {
    theme = saved;
    document.documentElement.setAttribute('data-theme', theme);
  }
})();

/* ══════════════════════════════════════════
   PASSWORD VISIBILITY TOGGLE
══════════════════════════════════════════ */
function togglePw() {
  const pw   = document.getElementById('password');
  const icon = document.getElementById('eyeIcon');
  if (pw.type === 'password') {
    pw.type = 'text';
    icon.innerHTML = `
      <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94"/>
      <path d="M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19"/>
      <line x1="1" y1="1" x2="23" y2="23"/>`;
  } else {
    pw.type = 'password';
    icon.innerHTML = `
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
      <circle cx="12" cy="12" r="3"/>`;
  }
}

/* ══════════════════════════════════════════
   LOGIN FORM HANDLER
══════════════════════════════════════════ */
function handleLogin(e) {
  e.preventDefault();
  const btn = document.getElementById('btnLogin');
  const err = document.getElementById('errorMsg');

  err.classList.remove('show');
  btn.classList.add('loading');

  setTimeout(() => {
    btn.classList.remove('loading');
    const user = document.getElementById('username').value;
    const pass = document.getElementById('password').value;

    if (user === 'admin' && pass === 'admin') {
      btn.style.background = 'linear-gradient(135deg,#1a7a3a,#27ae60)';
      btn.querySelector('.btn-text').textContent = DICT[lang].btnOk;
    } else {
      document.getElementById('errorText').textContent = DICT[lang].errorText;
      err.classList.add('show');
      document.getElementById('password').value = '';
      document.getElementById('password').focus();
    }
  }, 1600);
}
