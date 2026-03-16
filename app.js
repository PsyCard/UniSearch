let universities = [];
let currentUser = null;

const STATIC_HOSTS = ['github.io'];
const isStaticHost = STATIC_HOSTS.some((host) => window.location.hostname.endsWith(host)) || window.location.protocol === 'file:';
const API_BASE = isStaticHost ? 'https://unisearch-1sv1.onrender.com' : '';
const useBackend = true;

const admins = [
  'jgmejia@unibarranquilla.edu.co',
  'erjaimes@unibarranquilla.edu.co'
];
const adminPassword = '22412620IUB';

const $results = document.getElementById('results');
const $search = document.getElementById('search');
const $type = document.getElementById('filterType');
const $city = document.getElementById('filterCity');

const $openLoginBtn = document.getElementById('open-login-btn');
const $signupBtn = document.getElementById('signup-btn');
const $logoutBtn = document.getElementById('logout-btn');
const $dashboardBtn = document.getElementById('dashboard-btn');
const $adminBtn = document.getElementById('admin-btn');
const $userInfo = document.getElementById('user-info');
const $authButtons = document.getElementById('auth-buttons');
const $userName = document.getElementById('user-name');

const $authModal = document.getElementById('auth-modal');
const $modalTitle = document.getElementById('modal-title');
const $authForm = document.getElementById('login-form');
const $nameField = document.getElementById('name-field');
const $nameInput = document.getElementById('name');
const $lastNameField = document.getElementById('lastname-field');
const $lastNameInput = document.getElementById('lastname');
const $authMessage = document.getElementById('auth-message');
const $modalClose = document.querySelector('.close');

let signUpMode = false;

function toText(value) {
  return String(value || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
}

function capitalizeWords(value) {
  return String(value || '')
    .trim()
    .toLowerCase()
    .split(/\s+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

function formatType(value) {
  const clean = String(value || '').trim();
  if (!clean) return 'N/A';
  if (toText(clean) === 'publica') return 'P¿blica';
  return clean;
}

function displayName(user) {
  if (!user) return '';
  if (user.name && user.name.trim()) return user.name.trim();
  if (user.email && user.email.includes('@')) return user.email.split('@')[0];
  return user.email || 'Usuario';
}

function loadUsers() {
  try {
    return JSON.parse(localStorage.getItem('users')) || [];
  } catch {
    return [];
  }
}

function saveUsers(users) {
  localStorage.setItem('users', JSON.stringify(users));
}

function saveCurrentUser(user) {
  localStorage.setItem('currentUser', JSON.stringify(user));
}

function getCurrentUser() {
  try {
    return JSON.parse(localStorage.getItem('currentUser'));
  } catch {
    return null;
  }
}

function getCurrentUserEmail() {
  const user = getCurrentUser();
  return user && user.email ? String(user.email).trim() : '';
}

function clearCurrentUser() {
  localStorage.removeItem('currentUser');
}

function getLocalUniversities() {
  try {
    return JSON.parse(localStorage.getItem('universities')) || [];
  } catch {
    return [];
  }
}

function setLocalUniversities(list) {
  localStorage.setItem('universities', JSON.stringify(list));
}

function syncAuthUI() {
  currentUser = getCurrentUser();
  if (currentUser) {
    if ($userName) $userName.textContent = displayName(currentUser);
    if ($userInfo) $userInfo.style.display = 'block';
    if ($authButtons) $authButtons.style.display = 'none';
  } else {
    if ($userInfo) $userInfo.style.display = 'none';
    if ($authButtons) $authButtons.style.display = 'block';
  }
}

function openAuthModal(isSignUp) {
  if (!$authModal || !$modalTitle || !$nameField || !$authMessage || !$authForm) return;
  signUpMode = isSignUp;
  $modalTitle.textContent = isSignUp ? 'Registrarse' : 'Iniciar sesi¿n';
  $nameField.style.display = isSignUp ? 'block' : 'none';
  if ($lastNameField) $lastNameField.style.display = isSignUp ? 'block' : 'none';
  $authMessage.textContent = '';
  $authForm.reset();
  $authModal.style.display = 'block';
}

function closeAuthModal() {
  if ($authModal) $authModal.style.display = 'none';
}

function registerUser(name, lastName, email, password) {
  const normalizedEmail = toText(email).trim();
  if (!normalizedEmail || !password.trim()) {
    return { success: false, message: 'Completa correo y contrase¿a.' };
  }
  if (!String(name || '').trim() || !String(lastName || '').trim()) {
    return { success: false, message: 'Completa nombre y apellido.' };
  }
  if (admins.includes(normalizedEmail)) {
    return { success: false, message: 'Este correo es de administrador.' };
  }

  const users = loadUsers();
  if (users.some((u) => toText(u.email) === normalizedEmail)) {
    return { success: false, message: 'Este correo ya está registrado.' };
  }

  const fullName = `${capitalizeWords(name)} ${capitalizeWords(lastName)}`.trim();
  users.push({
    name: fullName,
    email: normalizedEmail,
    password
  });
  saveUsers(users);
  return { success: true, message: 'Registro exitoso. Ahora inicia sesi¿n.' };
}

function loginUser(email, password) {
  const normalizedEmail = toText(email).trim();

  if (admins.includes(normalizedEmail)) {
    if (password !== adminPassword) {
      return { success: false, message: 'contrase¿a de administrador incorrecta.' };
    }
    const adminUser = { name: 'Administrador', email: normalizedEmail, role: 'admin' };
    saveCurrentUser(adminUser);
    syncAuthUI();
    return { success: true };
  }

  const users = loadUsers();
  const found = users.find((u) => toText(u.email) === normalizedEmail && u.password === password);
  if (!found) {
    return { success: false, message: 'Correo o contrase¿a incorrectos.' };
  }

  saveCurrentUser({
    name: found.name || displayName(found),
    email: found.email,
    role: 'user'
  });
  syncAuthUI();
  return { success: true };
}

function logoutUser() {
  clearCurrentUser();
  syncAuthUI();
}

function formatCurrency(n) {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    maximumFractionDigits: 0
  }).format(n);
}

async function apiRequest(path, options = {}) {
  if (!useBackend) {
    throw new Error('Sin backend disponible');
  }

  const response = await fetch(`${API_BASE}${path}`, {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    },
    ...options
  });

  if (!response.ok) {
    let message = 'No se pudo completar la solicitud.';
    try {
      const data = await response.json();
      if (data?.message) message = data.message;
    } catch {
      // Keep fallback message when the response is not JSON.
    }
    throw new Error(message);
  }

  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    return response.json();
  }
  return null;
}

function renderStars(rating) {
  const round = Math.round(Number(rating) || 0);
  return `<span class="stars">${'*'.repeat(round)}${'*'.repeat(5 - round)}</span>`;
}

async function loadUniversities() {
  try {
    if (useBackend) {
      universities = await apiRequest('/api/universities');
      setLocalUniversities(universities);
    } else {
      const cached = getLocalUniversities();
      if (cached.length) {
        universities = cached;
      } else {
        const response = await fetch('data.json', { cache: 'no-store' });
        if (!response.ok) throw new Error('No se pudo cargar data.json');
        const data = await response.json();
        universities = Array.isArray(data) ? data : [];
        setLocalUniversities(universities);
      }
    }
  } catch (err) {
    console.error('Error cargando universidades:', err);
    universities = getLocalUniversities();
  }

  populateCities();
  applyFilters();
}

function populateCities() {
  if (!$city) return;
  const cities = Array.from(new Set(universities.map((u) => u.city).filter(Boolean))).sort();
  $city.innerHTML = '<option value="">Ciudad: Todas</option>';
  cities.forEach((city) => {
    const option = document.createElement('option');
    option.value = city;
    option.textContent = city;
    $city.appendChild(option);
  });
}

function render(list) {
  if (!$results) return;
  $results.innerHTML = '';
  if (!list.length) {
    $results.innerHTML = '<div class="card">No se encontraron universidades con esos criterios.</div>';
    return;
  }

  const fragment = document.createDocumentFragment();

  list.forEach((u) => {
    const article = document.createElement('article');
    article.className = 'uni-card card';

    const reviews = Array.isArray(u.reviews) ? u.reviews : [];
    const avg = reviews.length
      ? reviews.reduce((sum, rv) => sum + (Number(rv.rating) || 0), 0) / reviews.length
      : Number(u.rating) || 0;

    const careers = Array.isArray(u.careers) ? u.careers : [];
    const careersHtml = careers
      .slice(0, 3)
      .map((career) => {
        const name = typeof career === 'string' ? career : career.name;
        const price = typeof career === 'object' ? career.price : null;
        let priceHtml = '';
        if (price) {
          priceHtml = `<span class="price">${typeof price === 'number' ? formatCurrency(price) : price}</span>`;
        }
        return `<div class="career-chip"><strong>${name}</strong>${priceHtml}</div>`;
      })
      .join('');

    const hiddenCareers = careers.slice(3);
    const hiddenCareersHtml = hiddenCareers
      .map((career) => {
        const name = typeof career === 'string' ? career : career.name;
        const price = typeof career === 'object' ? career.price : null;
        let priceHtml = '';
        if (price) {
          priceHtml = `<span class="price">${typeof price === 'number' ? formatCurrency(price) : price}</span>`;
        }
        return `<div class="career-chip"><strong>${name}</strong>${priceHtml}</div>`;
      })
      .join('');

    const expandBtn = hiddenCareers.length ? `<button class="btn expand-careers" data-id="${u.id}">Mostrar más (${hiddenCareers.length})</button>`
      : '';

    article.innerHTML = `
      <h3>${u.name} <small class="rating">${renderStars(avg)} ${avg ? avg.toFixed(1) : 'N/A'}</small></h3>
      <div class="meta">${formatType(u.type)} ¿ ${u.city || 'N/A'} ¿ ${u.address || 'Sin direcci¿n'}</div>
      <div class="meta">Tel: ${u.phone || 'N/A'}</div>
      ${u.email ? `<div class="meta">Correo electrónico: <a href="mailto:${u.email}">${u.email}</a></div>` : ''}
      <div class="careers-section">
        <p class="careers-title">Carreras disponibles:</p>
        <div class="careers-list">${careersHtml}</div>
        ${expandBtn}
        ${hiddenCareers.length ? `<div class="hidden-careers" id="hidden-careers-${u.id}" style="display:none;">${hiddenCareersHtml}</div>` : ''}
      </div>
      <div class="actions">
        <a class="btn view" target="_blank" rel="noopener" href="https://www.google.com/maps/search/${encodeURIComponent(`${u.name || ''} ${u.city || ''}`)}">Ver en mapa</a>
        <a class="btn info" target="_blank" rel="noopener" href="${u.website || '#'}">Sitio web</a>
        <button class="btn info" data-id="${u.id}">Ver rese¿as</button>
      </div>
      <div class="reviews" id="reviews-${u.id}"></div>
      <div class="add-review-form" id="form-${u.id}" style="margin-top:10px;">
        <select class="rev-role" style="width:100%;margin-bottom:4px">\n          <option value="estudiante">Estudiante</option>\n          <option value="maestro">Maestro</option>\n        </select>
        <select class="rev-rating" style="margin-bottom:4px">
          <option value="1">1</option>
          <option value="2">2</option>
          <option value="3">3</option>
          <option value="4">4</option>
          <option value="5" selected>5</option>
        </select>
        <textarea class="rev-text" placeholder="Comentario" style="width:100%;height:60px;margin-bottom:4px"></textarea>
        <button class="btn submit-review" data-id="${u.id}">Enviar rese¿a</button>
      </div>
    `;

    fragment.appendChild(article);
  });

  $results.appendChild(fragment);
  bindCardActions();
}

function loadReviewsByUniversity(id) {
  const uni = universities.find((u) => String(u.id) === String(id));
  return uni && Array.isArray(uni.reviews) ? uni.reviews : [];
}

function findReviewByEmail(uni, email) {
  if (!uni || !Array.isArray(uni.reviews)) return null;
  const normalized = toText(email);
  return uni.reviews.find((r) => toText(r.author_email || '') === normalized) || null;
}

function upsertReviewLocal(id, review) {
  const uni = universities.find((u) => String(u.id) === String(id));
  if (!uni) return;
  if (!Array.isArray(uni.reviews)) uni.reviews = [];

  const normalized = toText(review.author_email || '');
  const index = uni.reviews.findIndex((r) => toText(r.author_email || '') === normalized);

  if (index >= 0) {
    uni.reviews[index] = { ...uni.reviews[index], ...review };
  } else {
    uni.reviews.unshift(review);
  }

  setLocalUniversities(universities);
}

function removeReviewLocal(id, authorEmail) {
  const uni = universities.find((u) => String(u.id) === String(id));
  if (!uni || !Array.isArray(uni.reviews)) return;
  const normalized = toText(authorEmail || '');
  uni.reviews = uni.reviews.filter((r) => toText(r.author_email || '') !== normalized);
  setLocalUniversities(universities);
}

function renderReviewPage(container, reviews, page = 0, uniId = null) {
  const perPage = 5;
  const start = page * perPage;
  const slice = reviews.slice(start, start + perPage);
  const currentEmail = getCurrentUserEmail();

  const html = slice
    .map((r) => {
      const canEdit = currentEmail && toText(r.author_email || '') === toText(currentEmail);
      const actions = canEdit
        ? `<div class="review-actions" style="margin-top:6px;display:flex;gap:6px;">
            <button class="btn edit-review" data-id="${uniId}">Editar</button>
            <button class="btn delete-review" data-id="${uniId}">Eliminar</button>
          </div>`
        : '';
      return `<div class="review"><strong>${r.author || 'Anónimo'}</strong> <span class="rating">(${r.role || 'usuario'} ¿ ${'*'.repeat(Number(r.rating) || 0)})</span><div style="margin-top:6px">${r.text || ''}</div>${actions}</div>`;
    })
    .join('');

  if (page === 0) {
    container.innerHTML = html;
  } else {
    container.innerHTML += html;
  }

  const previousMore = container.querySelector('.load-more');
  if (previousMore) previousMore.remove();

  if ((page + 1) * perPage < reviews.length) {
    const moreButton = document.createElement('button');
    moreButton.textContent = 'Mostrar más';
    moreButton.className = 'btn load-more';
    moreButton.addEventListener('click', () => renderReviewPage(container, reviews, page + 1, uniId));
    container.appendChild(moreButton);
  }

  container.querySelectorAll('.edit-review').forEach((btn) => {
    btn.addEventListener('click', () => {
      const id = btn.getAttribute('data-id');
      const email = getCurrentUserEmail();
      if (!email) return;
      const uni = universities.find((u) => String(u.id) === String(id));
      const review = findReviewByEmail(uni, email);
      if (!review) return;

      const form = document.getElementById(`form-${id}`);
      if (!form) return;
      form.querySelector('.rev-role').value = review.role || 'estudiante';
      form.querySelector('.rev-rating').value = String(review.rating || 5);
      form.querySelector('.rev-text').value = review.text || '';
      form.querySelector('.rev-text').focus();
    });
  });

  container.querySelectorAll('.delete-review').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const id = btn.getAttribute('data-id');
      const email = getCurrentUserEmail();
      if (!email) return;
      const confirmed = window.confirm('¿Seguro que quieres eliminar tu rese¿a?');
      if (!confirmed) return;

      try {
        await deleteReview(id, email);
        removeReviewLocal(id, email);
        applyFilters();
        showReviewsFor(id);
      } catch (error) {
        alert(error.message || 'No se pudo eliminar la rese¿a.');
      }
    });
  });
}

function showReviewsFor(id) {
  const box = document.getElementById(`reviews-${id}`);
  if (!box) return;

  const reviews = loadReviewsByUniversity(id);
  renderReviewPage(box, reviews, 0, id);
  box.classList.add('show');

  const btn = document.querySelector(`.actions button[data-id="${id}"]`);
  if (btn) btn.textContent = 'Ocultar rese¿as';
}

async function updateReview(id, payload) {
  if (useBackend) {
    const data = await apiRequest(`/api/universities/${id}/reviews`, {
      method: 'PUT',
      body: JSON.stringify(payload)
    });
    return data;
  }
  upsertReviewLocal(id, payload);
  return { success: true, review: payload };
}

async function deleteReview(id, authorEmail) {
  if (useBackend) {
    const data = await apiRequest(`/api/universities/${id}/reviews`, {
      method: 'DELETE',
      body: JSON.stringify({ author_email: authorEmail })
    });
    return data;
  }
  removeReviewLocal(id, authorEmail);
  return { success: true };
}

async function submitReview(id, role, rating, text) {
  const email = getCurrentUserEmail();
  if (!email) {
    openAuthModal(false);
    if ($authMessage) $authMessage.textContent = 'Debes iniciar sesi¿n para dejar una rese¿a.';
    throw new Error('Debes iniciar sesi¿n para dejar una rese¿a.');
  }

  const authorName = currentUser ? displayName(currentUser) : email;
  const uni = universities.find((u) => String(u.id) === String(id));
  const existing = findReviewByEmail(uni, email);
  const payload = {
    role: role || 'estudiante',
    author: authorName,
    author_email: email,
    rating: Number(rating) || 5,
    text: text.trim()
  };

  try {
    const data = existing
      ? await updateReview(id, payload)
      : (useBackend
          ? await apiRequest(`/api/universities/${id}/reviews`, { method: 'POST', body: JSON.stringify(payload) })
          : { success: true, review: payload });

    const review = data.review || payload;
    upsertReviewLocal(id, review);
    return { mode: 'api', action: existing ? 'update' : 'create' };
  } catch (error) {
    // Fallback when the API is unavailable: persist locally.
    upsertReviewLocal(id, payload);
    return { mode: 'local', error };
  }
}

function bindCardActions() {
  document.querySelectorAll('.actions button[data-id]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const id = btn.getAttribute('data-id');
      const box = document.getElementById(`reviews-${id}`);
      if (!box) return;

      if (!box.classList.contains('show')) {
        const reviews = loadReviewsByUniversity(id);
        renderReviewPage(box, reviews, 0, id);
      }

      box.classList.toggle('show');
      btn.textContent = box.classList.contains('show') ? 'Ocultar rese¿as' : 'Ver rese¿as';
    });
  });

  document.querySelectorAll('.expand-careers').forEach((btn) => {
    btn.addEventListener('click', () => {
      const id = btn.getAttribute('data-id');
      const hidden = document.getElementById(`hidden-careers-${id}`);
      if (!hidden) return;

      if (hidden.style.display === 'none') {
        hidden.style.display = 'block';
        btn.textContent = 'Mostrar menos';
      } else {
        hidden.style.display = 'none';
        btn.textContent = `Mostrar más (${hidden.querySelectorAll('.career-chip').length})`;
      }
    });
  });

  document.querySelectorAll('.submit-review').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const id = btn.getAttribute('data-id');
      const form = document.getElementById(`form-${id}`);
      if (!form) return;

      const role = form.querySelector('.rev-role').value;
      const rating = form.querySelector('.rev-rating').value;
      const text = form.querySelector('.rev-text').value.trim();

      if (!text) {
        alert('Escribe un comentario.');
        return;
      }

      try {
        await submitReview(id, role, rating, text);
        form.querySelector('.rev-role').value = 'estudiante';
        form.querySelector('.rev-rating').value = '5';
        form.querySelector('.rev-text').value = '';
        applyFilters();
        showReviewsFor(id);
      } catch (error) {
        alert(error.message || 'No se pudo enviar la rese¿a.');
      }
    });
  });
}

function applyFilters() {
  const q = toText($search ? $search.value : '');
  const selectedType = $type ? $type.value : '';
  const selectedCity = $city ? $city.value : '';

  let filtered = [...universities];
  if (selectedType) filtered = filtered.filter((u) => toText(u.type) === toText(selectedType));
  if (selectedCity) filtered = filtered.filter((u) => u.city === selectedCity);

  if (q) {
    filtered = filtered.filter((u) => {
      const careersText = (u.careers || []).map((c) => (typeof c === 'string' ? c : c.name || '')).join(' ');
      return toText(`${u.name || ''} ${u.address || ''} ${u.barrio || ''} ${u.city || ''} ${careersText}`).includes(q);
    });
  }

  render(filtered);
}

if ($search) $search.addEventListener('input', applyFilters);
if ($type) $type.addEventListener('change', applyFilters);
if ($city) $city.addEventListener('change', applyFilters);

if ($openLoginBtn) $openLoginBtn.addEventListener('click', () => openAuthModal(false));
if ($signupBtn) $signupBtn.addEventListener('click', () => openAuthModal(true));
if ($modalClose) $modalClose.addEventListener('click', closeAuthModal);

window.addEventListener('click', (e) => {
  if (e.target === $authModal) closeAuthModal();
});

if ($authForm) {
  $authForm.addEventListener('submit', (e) => {
    e.preventDefault();

    const name = $nameInput ? $nameInput.value : '';
    const lastName = $lastNameInput ? $lastNameInput.value : '';
    const email = document.getElementById('loginEmail')?.value || '';
    const password = document.getElementById('loginPassword')?.value || '';

    if (signUpMode) {
      const result = registerUser(name, lastName, email, password);
      $authMessage.textContent = result.message;
      if (result.success) {
        signUpMode = false;
        $modalTitle.textContent = 'Iniciar sesi¿n';
        $nameField.style.display = 'none';
        if ($lastNameField) $lastNameField.style.display = 'none';
      }
      return;
    }

    const result = loginUser(email, password);
    if (!result.success) {
      $authMessage.textContent = result.message;
      return;
    }

    closeAuthModal();
  });
}

if ($logoutBtn) {
  $logoutBtn.addEventListener('click', () => {
    logoutUser();
  });
}

if ($dashboardBtn) {
  $dashboardBtn.addEventListener('click', (e) => {
    if (!getCurrentUser()) {
      e.preventDefault();
      openAuthModal(false);
      if ($authMessage) $authMessage.textContent = 'Debes iniciar sesi¿n para abrir el dashboard.';
    }
  });
}

if ($adminBtn) {
  $adminBtn.addEventListener('click', (e) => {
    const user = getCurrentUser();

    if (!user) {
      e.preventDefault();
      openAuthModal(false);
      if ($authMessage) $authMessage.textContent = 'Debes iniciar sesi¿n como administrador.';
      return;
    }

    if (!isAdminUser(user)) {
      e.preventDefault();
      alert('No tienes acceso al panel de administrador.');
    }
  });
}

function isAdminUser(user) {
  if (!user || user.role !== 'admin') return false;
  const normalizedEmail = toText(user.email).trim();
  return admins.includes(normalizedEmail);
}

function showTab(tabId) {
  const tabs = document.querySelectorAll('.tab');
  const contents = document.querySelectorAll('.tab-content');

  tabs.forEach((tab) => tab.classList.remove('active'));
  contents.forEach((content) => {
    content.classList.remove('active');
    content.style.display = 'none';
  });

  const target = document.getElementById(tabId);
  if (target) {
    target.classList.add('active');
    target.style.display = 'block';
  }

  tabs.forEach((tab) => {
    if (tab.getAttribute('onclick') === `showTab('${tabId}')`) {
      tab.classList.add('active');
    }
  });
}

window.showTab = showTab;

function renderAdminDashboard(list) {
  const container = document.getElementById('universities-list');
  const totalUnis = document.getElementById('total-unis');
  const totalReviews = document.getElementById('total-reviews');

  if (totalUnis) totalUnis.textContent = list.length;
  if (totalReviews) {
    const reviewsCount = list.reduce((acc, uni) => acc + (Array.isArray(uni.reviews) ? uni.reviews.length : 0), 0);
    totalReviews.textContent = reviewsCount;
  }

  if (!container) return;
  if (!list.length) {
    container.innerHTML = '<article class="card">No hay universidades para mostrar.</article>';
    return;
  }

  container.innerHTML = list
    .map((u) => {
      const reviewCount = Array.isArray(u.reviews) ? u.reviews.length : 0;
      return `
        <article class="card">
          <div class="card-title">${u.name || 'Universidad'}</div>
          <div class="info-row"><span class="info-label">Tipo:</span> ${formatType(u.type)}</div>
          <div class="info-row"><span class="info-label">Ciudad:</span> ${u.city || 'N/A'}</div>
          <div class="info-row"><span class="info-label">Tel¿fono:</span> ${u.phone || 'N/A'}</div>
          <div class="info-row"><span class="info-label">Rese¿as:</span> ${reviewCount}</div>
          <div style="margin-top:12px;">
            <button type="button" class="btn-danger delete-uni-btn" data-id="${u.id}">Eliminar universidad</button>
          </div>
        </article>
      `;
    })
    .join('');

  bindAdminDeleteActions();
}

function renderAdminTable(list) {
  const body = document.getElementById('db-table-body');
  const count = document.getElementById('db-table-count');
  if (!body) return;

  if (count) count.textContent = `Total de registros: ${list.length}`;

  if (!list.length) {
    body.innerHTML = '<tr><td colspan="8">No hay datos para mostrar.</td></tr>';
    return;
  }

  body.innerHTML = list
    .map((u) => {
      const reviewsCount = Array.isArray(u.reviews) ? u.reviews.length : 0;
      const website = u.website ? `<a href="${u.website}" target="_blank" rel="noopener">${u.website}</a>` : 'N/A';
      const email = u.email ? `<a href="mailto:${u.email}">${u.email}</a>` : 'N/A';
      return `
        <tr>
          <td>${u.id ?? ''}</td>
          <td>${u.name || 'Universidad'}</td>
          <td>${formatType(u.type)}</td>
          <td>${u.city || 'N/A'}</td>
          <td>${u.phone || 'N/A'}</td>
          <td>${email}</td>
          <td>${website}</td>
          <td>${reviewsCount}</td>
        </tr>
      `;
    })
    .join('');
}

function bindAdminDeleteActions() {
  document.querySelectorAll('.delete-uni-btn').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const id = btn.getAttribute('data-id');
      if (!id) return;

      const target = universities.find((u) => String(u.id) === String(id));
      const name = target?.name || 'esta universidad';
      const confirmed = window.confirm(`¿Seguro que quieres eliminar ${name}?`);
      if (!confirmed) return;

      try {
        if (useBackend) {
          await apiRequest(`/api/universities/${id}`, { method: 'DELETE' });
          await loadUniversities();
        } else {
          universities = universities.filter((u) => String(u.id) !== String(id));
          setLocalUniversities(universities);
        }
        renderAdminDashboard(universities);
        renderAdminTable(universities);
      } catch (error) {
        alert(error.message || 'No se pudo eliminar la universidad.');
      }
    });
  });
}

function setupAdminForm() {
  const form = document.getElementById('add-uni-form');
  if (!form || form.dataset.bound === '1') return;
  form.dataset.bound = '1';

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const name = document.getElementById('uni-name')?.value.trim();
    const type = document.getElementById('uni-type')?.value || 'Privada';
    const city = document.getElementById('uni-city')?.value.trim();
    const phone = document.getElementById('uni-phone')?.value.trim() || '';
    const email = document.getElementById('uni-email')?.value.trim() || '';
    const website = document.getElementById('uni-website')?.value.trim() || '';
    const careersRaw = document.getElementById('uni-careers')?.value || '';

    if (!name || !city) {
      alert('Completa al menos nombre y ciudad.');
      return;
    }

    const careers = careersRaw
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean);

    const payload = {
      name,
      type,
      city,
      phone,
      email,
      website,
      careers
    };

    const adminEmail = getCurrentUserEmail();
    if (adminEmail) payload.owner_email = adminEmail;

    try {
      if (useBackend) {
        await apiRequest('/api/universities', {
          method: 'POST',
          body: JSON.stringify(payload)
        });
        await loadUniversities();
      } else {
        const nextId = universities.reduce((max, u) => Math.max(max, Number(u.id) || 0), 0) + 1;
        universities = [
          ...universities,
          {
            id: nextId,
            ...payload,
            reviews: []
          }
        ];
        setLocalUniversities(universities);
      }

      renderAdminDashboard(universities);
      renderAdminTable(universities);
      form.reset();
      alert('Universidad agregada correctamente.');
    } catch (error) {
      alert(error.message || 'No se pudo guardar la universidad.');
    }
  });
}

async function checkAdmin() {
  const authWarning = document.getElementById('auth-warning');
  if (!authWarning) return;

  const user = getCurrentUser();
  const tabs = document.querySelector('.tabs');
  const sections = document.querySelectorAll('.tab-content');
  const userInfo = document.getElementById('user-info');
  const userName = document.getElementById('user-name');
  const userEmail = document.getElementById('user-email');

  const denyAccess = (message) => {
    authWarning.textContent = message;
    authWarning.style.display = 'block';

    if (tabs) tabs.style.display = 'none';
    sections.forEach((section) => {
      section.style.display = 'none';
    });

    if (userInfo) userInfo.style.display = 'none';
  };

  if (!user) {
    denyAccess('Debes iniciar sesi¿n para acceder al panel de administrador.');
    return;
  }

  if (!isAdminUser(user)) {
    denyAccess('No tienes acceso al panel de administrador.');
    return;
  }

  authWarning.style.display = 'none';
  if (tabs) tabs.style.display = 'flex';

  sections.forEach((section) => {
    section.style.display = section.classList.contains('active') ? 'block' : 'none';
  });

  if (userInfo) userInfo.style.display = 'block';
  if (userName) userName.textContent = displayName(user);
  if (userEmail) userEmail.textContent = user.email || '';

  await loadUniversities();
  renderAdminDashboard(universities);
  renderAdminTable(universities);
  showTab('universities');
  setupAdminForm();
}

function logout() {
  logoutUser();
  window.location.href = './';
}

document.addEventListener('DOMContentLoaded', async () => {
  const isHome = window.location.pathname === '/' || window.location.pathname.endsWith('/index.html') || window.location.pathname.endsWith('index.html');
  if (isHome) {
    clearCurrentUser();
  }
  syncAuthUI();
  await loadUniversities();
});





