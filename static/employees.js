/* ══════════════════════════════════════════
   i18n DICTIONARY
══════════════════════════════════════════ */
const DICT = {
  fr: {
    pageTitle:    'Employés',
    pageSub:      'Gestion Multi-Agences',
    btnAdd:       'Ajouter',
    statTotal:    'Total employés',
    searchPh:     'Rechercher un employé…',
    filterAll:    'Toutes les agences',
    filterRole:   'Tous les rôles',
    colId:        'ID',
    colName:      'Nom',
    colRole:      'Rôle',
    colAgency:    'Agence',
    colActions:   'Actions',
    emptyState:   'Aucun employé trouvé',
    modalAddTitle:'Ajouter un employé',
    modalEditTitle:'Modifier l\'employé',
    fieldFirstName:'Prénom',
    fieldLastName: 'Nom de famille',
    phFirstName:  'Prénom',
    phLastName:   'Nom',
    btnCancel:    'Annuler',
    btnSave:      'Enregistrer',
    toastAdded:   '✓ Employé ajouté',
    toastUpdated: '✓ Employé mis à jour',
    toastDeleted: '✗ Employé supprimé',
    docTitle:     'Employés — Gestion de Stock',
    editTitle:    'Modifier',
    deleteTitle:  'Supprimer',
  },
  en: {
    pageTitle:    'Employees',
    pageSub:      'Multi-Agency Management',
    btnAdd:       'Add',
    statTotal:    'Total employees',
    searchPh:     'Search an employee…',
    filterAll:    'All agencies',
    filterRole:   'All roles',
    colId:        'ID',
    colName:      'Name',
    colRole:      'Role',
    colAgency:    'Agency',
    colActions:   'Actions',
    emptyState:   'No employee found',
    modalAddTitle:'Add employee',
    modalEditTitle:'Edit employee',
    fieldFirstName:'First name',
    fieldLastName: 'Last name',
    phFirstName:  'First name',
    phLastName:   'Last name',
    btnCancel:    'Cancel',
    btnSave:      'Save',
    toastAdded:   '✓ Employee added',
    toastUpdated: '✓ Employee updated',
    toastDeleted: '✗ Employee deleted',
    docTitle:     'Employees — Stock Management',
    editTitle:    'Edit',
    deleteTitle:  'Delete',
  }
};

/* ══════════════════════════════════════════
   STATE
══════════════════════════════════════════ */
let lang        = 'fr';
let theme       = 'dark';

/* ══════════════════════════════════════════
   LANGUAGE SWITCHER
══════════════════════════════════════════ */
function setLang(l) {
  if (l === lang) return;
  lang = l;
  const t = DICT[l];
  document.body.classList.add('fading');
  setTimeout(() => {
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const k = el.getAttribute('data-i18n');
      if (t[k] != null) el.textContent = t[k];
    });
    document.querySelectorAll('[data-i18n-ph]').forEach(el => {
      const k = el.getAttribute('data-i18n-ph');
      if (t[k] != null) el.placeholder = t[k];
    });
    /* filter select first options */
    const af = document.getElementById('agencyFilter');
    if (af) af.options[0].textContent = t.filterAll;
    const rf = document.getElementById('roleFilter');
    if (rf) rf.options[0].textContent = t.filterRole;

    document.title = t.docTitle;
    document.documentElement.lang = l;
    document.getElementById('btnFR').classList.toggle('active', l === 'fr');
    document.getElementById('btnEN').classList.toggle('active', l === 'en');
    document.body.classList.remove('fading');   /* re-render for action button titles */
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
(function initTheme() {
  const saved = localStorage.getItem('smTheme');
  if (saved) { theme = saved; document.documentElement.setAttribute('data-theme', theme); }
})();
/* ══════════════════════════════════════════
   FILTER + SORT + RENDER
══════════════════════════════════════════ */

function sortTable(key) {
}

function filterTable() {
    const search = document
        .getElementById("searchInput")
        .value
        .toLowerCase();

    const rows = document.querySelectorAll("#tableBody tr");

    rows.forEach(row => {
        const text = row.textContent.toLowerCase();

        if (text.includes(search)) {
            row.style.display = "";
        } else {
            row.style.display = "none";
        }
    });
}

function filterTable() {
    const search = document
        .getElementById("searchInput")
        .value
        .toLowerCase();

    const rows = document.querySelectorAll("#tableBody tr");
    let visibleRows = 0;

    rows.forEach(row => {
        const text = row.textContent.toLowerCase();

        if (text.includes(search)) {
            row.style.display = "";
            visibleRows++;
        } else {
            row.style.display = "none";
        }
    });

    const empty = document.getElementById("emptyState");

    if (visibleRows === 0) {
        empty.style.display = "block";
    } else {
        empty.style.display = "none";
    }
}
