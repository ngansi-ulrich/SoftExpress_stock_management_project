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
let currentPage = 1;
const PER_PAGE  = 8;
let sortKey     = '';
let sortDir     = 'asc';
let editingId   = null;

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
    document.body.classList.remove('fading');

    renderTable();   /* re-render for action button titles */
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
   STATS
══════════════════════════════════════════ */
function updateStats() {
  document.getElementById('statTotal').textContent     = employees.length;
  document.getElementById('statDouala').textContent    = employees.filter(e => e.agency === 'Douala').length;
  document.getElementById('statYaounde').textContent   = employees.filter(e => e.agency === 'Yaoundé').length;
  document.getElementById('statBafoussam').textContent = employees.filter(e => e.agency === 'Bafoussam').length;
}

/* ══════════════════════════════════════════
   FILTER + SORT + RENDER
══════════════════════════════════════════ */
function getFiltered() {
  const q  = (document.getElementById('searchInput')?.value || '').toLowerCase();
  const ag = document.getElementById('agencyFilter')?.value || '';
  const ro = document.getElementById('roleFilter')?.value || '';

  let list = employees.filter(e => {
    const name = `${e.first_name} ${e.last_name}`.toLowerCase();
    const matchQ  = !q  || name.includes(q) || e.employee_id.toLowerCase().includes(q) || e.role.toLowerCase().includes(q);
    const matchAg = !ag || e.agency === ag;
    const matchRo = !ro || e.role === ro;
    return matchQ && matchAg && matchRo;
  });

  if (sortKey) {
    list = list.sort((a, b) => {
      let va = sortKey === 'name' ? `${a.first_name} ${a.last_name}` : a[sortKey] || a.employee_id;
      let vb = sortKey === 'name' ? `${b.first_name} ${b.last_name}` : b[sortKey] || b.employee_id;
      return sortDir === 'asc' ? va.localeCompare(vb) : vb.localeCompare(va);
    });
  }
  return list;
}

function filterTable() {
  currentPage = 1;
  renderTable();
}

function sortTable(key) {
  if (sortKey === key) {
    sortDir = sortDir === 'asc' ? 'desc' : 'asc';
  } else {
    sortKey = key; sortDir = 'asc';
  }
  /* update sort icons */
  document.querySelectorAll('th.sortable').forEach(th => {
    th.classList.remove('sort-asc','sort-desc');
  });
  const keyMap = { id:'id', name:'name', role:'role', agency:'agency' };
  const idx    = ['id','name','role','agency'].indexOf(key);
  const headers = document.querySelectorAll('th.sortable');
  if (headers[idx]) headers[idx].classList.add(sortDir === 'asc' ? 'sort-asc' : 'sort-desc');

  renderTable();
}

function roleBadgeClass(role) {
  const map = { Admin:'role-admin', Manager:'role-manager', Agent:'role-agent', Caissier:'role-caissier' };
  return map[role] || 'role-agent';
}

function initials(first, last) {
  return `${first[0] || ''}${last[0] || ''}`.toUpperCase();
}

function renderTable() {
  const t       = DICT[lang];
  const filtered = getFiltered();
  const total    = filtered.length;
  const pages    = Math.ceil(total / PER_PAGE) || 1;
  if (currentPage > pages) currentPage = pages;

  const slice = filtered.slice((currentPage - 1) * PER_PAGE, currentPage * PER_PAGE);
  const tbody = document.getElementById('tableBody');
  const empty = document.getElementById('emptyState');

  if (slice.length === 0) {
    tbody.innerHTML = '';
    empty.style.display = 'block';
  } else {
    empty.style.display = 'none';
    tbody.innerHTML = slice.map(e => `
      <tr>
        <td><span class="badge-id">${e.employee_id}</span></td>
        <td>
          <div class="name-cell">
            <div class="emp-avatar">${initials(e.first_name, e.last_name)}</div>
            <span class="emp-name">${e.first_name} ${e.last_name}</span>
          </div>
        </td>
        <td><span class="badge-role ${roleBadgeClass(e.role)}">${e.role}</span></td>
        <td>
          <div class="badge-agency">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/>
              <polyline points="9 22 9 12 15 12 15 22"/>
            </svg>
            ${e.agency}
          </div>
        </td>
        <td>
          <div class="action-btns">
            <button class="btn-edit" onclick="editEmployee('${e.employee_id}')" title="${t.editTitle}">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
                <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
              </svg>
            </button>
            <button class="btn-delete" onclick="deleteEmployee('${e.employee_id}')" title="${t.deleteTitle}">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="3 6 5 6 21 6"/>
                <path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/>
                <path d="M10 11v6"/><path d="M14 11v6"/>
                <path d="M9 6V4a1 1 0 011-1h4a1 1 0 011 1v2"/>
              </svg>
            </button>
          </div>
        </td>
      </tr>
    `).join('');
  }

  renderPagination(pages);
  updateStats();
}

/* ══════════════════════════════════════════
   PAGINATION
══════════════════════════════════════════ */
function renderPagination(pages) {
  const pg = document.getElementById('pagination');
  if (pages <= 1) { pg.innerHTML = ''; return; }
  let html = `<button class="page-btn" onclick="goPage(${currentPage-1})" ${currentPage===1?'disabled':''}>‹</button>`;
  for (let i = 1; i <= pages; i++) {
    html += `<button class="page-btn ${i===currentPage?'active':''}" onclick="goPage(${i})">${i}</button>`;
  }
  html += `<button class="page-btn" onclick="goPage(${currentPage+1})" ${currentPage===pages?'disabled':''}>›</button>`;
  pg.innerHTML = html;
}
function goPage(p) { currentPage = p; renderTable(); }

/* ══════════════════════════════════════════
   MODAL
══════════════════════════════════════════ */
function openModal(emp = null) {
  const t = DICT[lang];
  editingId = emp ? emp.employee_id : null;
  document.getElementById('modalTitle').textContent = emp ? t.modalEditTitle : t.modalAddTitle;
  document.getElementById('fId').value     = emp ? emp.employee_id  : '';
  document.getElementById('fFirst').value  = emp ? emp.first_name   : '';
  document.getElementById('fLast').value   = emp ? emp.last_name    : '';
  document.getElementById('fRole').value   = emp ? emp.role         : '';
  document.getElementById('fAgency').value = emp ? emp.agency       : '';
  document.getElementById('fId').disabled  = !!emp;
  document.getElementById('modalOverlay').classList.add('open');
}

function closeModal() {
  document.getElementById('modalOverlay').classList.remove('open');
  document.getElementById('employeeForm').reset();
  editingId = null;
}

function closeModalOutside(e) {
  if (e.target === document.getElementById('modalOverlay')) closeModal();
}

function editEmployee(id) {
  const emp = employees.find(e => e.employee_id === id);
  if (emp) openModal(emp);
}

/* ══════════════════════════════════════════
   SAVE (add / edit)
══════════════════════════════════════════ */
function saveEmployee(e) {
  e.preventDefault();
  const t = DICT[lang];
  const newEmp = {
    employee_id: document.getElementById('fId').value.trim(),
    first_name:  document.getElementById('fFirst').value.trim(),
    last_name:   document.getElementById('fLast').value.trim(),
    role:        document.getElementById('fRole').value,
    agency:      document.getElementById('fAgency').value,
  };

  if (editingId) {
    const idx = employees.findIndex(emp => emp.employee_id === editingId);
    if (idx !== -1) employees[idx] = { ...employees[idx], ...newEmp };
    showToast(t.toastUpdated);
  } else {
    employees.push(newEmp);
    showToast(t.toastAdded);
  }

  closeModal();
  renderTable();
}

/* ══════════════════════════════════════════
   DELETE
══════════════════════════════════════════ */
function deleteEmployee(id) {
  const t = DICT[lang];
  employees = employees.filter(e => e.employee_id !== id);
  showToast(t.toastDeleted);
  renderTable();
}

/* ══════════════════════════════════════════
   TOAST
══════════════════════════════════════════ */
function showToast(msg) {
  const toast = document.getElementById('toast');
  toast.textContent = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 2800);
}

/* ══════════════════════════════════════════
   INIT
══════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', () => {
  renderTable();
  updateStats();
});
