// ============================================================
// Dashboard App — Auth + Widgets + Data Sources
// ============================================================

(function () {
    'use strict';

    // --- Storage Helpers ---
    const DB = {
        get(key, fallback = null) {
            try {
                const raw = localStorage.getItem(key);
                return raw ? JSON.parse(raw) : fallback;
            } catch {
                return fallback;
            }
        },
        set(key, value) {
            localStorage.setItem(key, JSON.stringify(value));
        },
        remove(key) {
            localStorage.removeItem(key);
        }
    };

    // --- Simple password hashing (SHA-256) ---
    // For production, use a real backend with bcrypt/argon2.
    async function hashPassword(password) {
        const encoder = new TextEncoder();
        const data = encoder.encode(password);
        const hashBuffer = await crypto.subtle.digest('SHA-256', data);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    }

    // --- Auth Module ---
    const Auth = {
        getUsers() {
            return DB.get('dashboard_users', []);
        },

        saveUsers(users) {
            DB.set('dashboard_users', users);
        },

        getCurrentUser() {
            return DB.get('dashboard_current_user', null);
        },

        setCurrentUser(user) {
            DB.set('dashboard_current_user', user);
        },

        logout() {
            DB.remove('dashboard_current_user');
        },

        async register(name, email, password) {
            const users = this.getUsers();
            if (users.find(u => u.email === email)) {
                throw new Error('Ein Konto mit dieser E-Mail existiert bereits.');
            }
            const hashedPassword = await hashPassword(password);
            const user = {
                id: crypto.randomUUID ? crypto.randomUUID() : Date.now().toString(36),
                name,
                email,
                password: hashedPassword,
                createdAt: new Date().toISOString()
            };
            users.push(user);
            this.saveUsers(users);
            const sessionUser = { id: user.id, name: user.name, email: user.email };
            this.setCurrentUser(sessionUser);
            return sessionUser;
        },

        async login(email, password) {
            const users = this.getUsers();
            const hashedPassword = await hashPassword(password);
            const user = users.find(u => u.email === email && u.password === hashedPassword);
            if (!user) {
                throw new Error('E-Mail oder Passwort ist falsch.');
            }
            const sessionUser = { id: user.id, name: user.name, email: user.email };
            this.setCurrentUser(sessionUser);
            return sessionUser;
        },

        async changePassword(email, currentPassword, newPassword) {
            const users = this.getUsers();
            const hashedCurrent = await hashPassword(currentPassword);
            const user = users.find(u => u.email === email && u.password === hashedCurrent);
            if (!user) {
                throw new Error('Aktuelles Passwort ist falsch.');
            }
            user.password = await hashPassword(newPassword);
            this.saveUsers(users);
        },

        updateProfile(id, updates) {
            const users = this.getUsers();
            const user = users.find(u => u.id === id);
            if (user) {
                Object.assign(user, updates);
                this.saveUsers(users);
                const sessionUser = this.getCurrentUser();
                if (sessionUser && sessionUser.id === id) {
                    Object.assign(sessionUser, updates);
                    this.setCurrentUser(sessionUser);
                }
            }
        }
    };

    // --- Data Module (per-user) ---
    function userKey(userId, key) {
        return `dashboard_${userId}_${key}`;
    }

    const Data = {
        getWidgets(userId) {
            return DB.get(userKey(userId, 'widgets'), []);
        },
        saveWidgets(userId, widgets) {
            DB.set(userKey(userId, 'widgets'), widgets);
        },
        getSources(userId) {
            return DB.get(userKey(userId, 'sources'), []);
        },
        saveSources(userId, sources) {
            DB.set(userKey(userId, 'sources'), sources);
        }
    };

    // --- DOM Helpers ---
    const $ = (sel) => document.querySelector(sel);
    const $$ = (sel) => document.querySelectorAll(sel);

    function show(el) { el.hidden = false; }
    function hide(el) { el.hidden = true; }

    function showError(el, msg) {
        el.textContent = msg;
        show(el);
    }
    function hideError(el) {
        el.textContent = '';
        hide(el);
    }

    // --- Views ---
    const views = {
        login: $('#view-login'),
        register: $('#view-register'),
        dashboard: $('#view-dashboard')
    };

    function showView(name) {
        Object.values(views).forEach(v => hide(v));
        show(views[name]);
    }

    // --- Auth UI ---
    $('#show-register').addEventListener('click', e => {
        e.preventDefault();
        showView('register');
    });

    $('#show-login').addEventListener('click', e => {
        e.preventDefault();
        showView('login');
    });

    $('#login-form').addEventListener('submit', async e => {
        e.preventDefault();
        const errorEl = $('#login-error');
        hideError(errorEl);
        const email = $('#login-email').value.trim();
        const password = $('#login-password').value;
        try {
            const user = await Auth.login(email, password);
            e.target.reset();
            initDashboard(user);
        } catch (err) {
            showError(errorEl, err.message);
        }
    });

    $('#register-form').addEventListener('submit', async e => {
        e.preventDefault();
        const errorEl = $('#register-error');
        hideError(errorEl);
        const name = $('#register-name').value.trim();
        const email = $('#register-email').value.trim();
        const password = $('#register-password').value;
        const confirm = $('#register-password-confirm').value;

        if (password !== confirm) {
            showError(errorEl, 'Die Passwoerter stimmen nicht ueberein.');
            return;
        }
        try {
            const user = await Auth.register(name, email, password);
            e.target.reset();
            initDashboard(user);
        } catch (err) {
            showError(errorEl, err.message);
        }
    });

    $('#logout-btn').addEventListener('click', () => {
        Auth.logout();
        showView('login');
    });

    // --- Dashboard Init ---
    let currentUser = null;

    function initDashboard(user) {
        currentUser = user;
        showView('dashboard');

        // Update user info
        $('#user-name').textContent = user.name;
        $('#user-email').textContent = user.email;
        $('#user-avatar').textContent = user.name.charAt(0).toUpperCase();
        $('#topbar-user').textContent = user.name;

        // Settings
        $('#settings-name').value = user.name;
        $('#settings-email').value = user.email;

        renderWidgets();
        renderSources();
        navigateTo('overview');
    }

    // --- Navigation ---
    $$('.sidebar-link').forEach(link => {
        link.addEventListener('click', e => {
            e.preventDefault();
            const page = link.dataset.page;
            navigateTo(page);
            // Close sidebar on mobile
            $('#sidebar').classList.remove('open');
        });
    });

    $('#menu-btn').addEventListener('click', () => {
        $('#sidebar').classList.toggle('open');
    });

    $('#sidebar-toggle').addEventListener('click', () => {
        $('#sidebar').classList.remove('open');
    });

    const pageTitles = {
        'overview': 'Uebersicht',
        'data-sources': 'Datenquellen',
        'settings': 'Einstellungen'
    };

    function navigateTo(page) {
        $$('.page').forEach(p => hide(p));
        show($(`#page-${page}`));

        $$('.sidebar-link').forEach(l => l.classList.remove('active'));
        const activeLink = $(`.sidebar-link[data-page="${page}"]`);
        if (activeLink) activeLink.classList.add('active');

        $('#page-title').textContent = pageTitles[page] || page;
    }

    // --- Widgets ---
    function renderWidgets() {
        const widgets = Data.getWidgets(currentUser.id);
        const container = $('#widgets-container');
        const emptyState = $('#empty-widgets');

        // Update stats
        $('#stat-sources').textContent = Data.getSources(currentUser.id).length;
        $('#stat-widgets').textContent = widgets.length;
        $('#stat-updated').textContent = widgets.length > 0
            ? new Date().toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
            : '--';

        if (widgets.length === 0) {
            container.innerHTML = '';
            container.appendChild(createEmptyWidgets());
            return;
        }

        container.innerHTML = '';
        widgets.forEach(w => container.appendChild(createWidgetCard(w)));
    }

    function createEmptyWidgets() {
        const div = document.createElement('div');
        div.className = 'empty-state';
        div.innerHTML = `
            <div class="empty-icon">&#128202;</div>
            <h3>Noch keine Widgets</h3>
            <p>Fuege dein erstes Widget hinzu, um Daten anzuzeigen.</p>
            <button class="btn btn-primary" id="empty-add-widget">Widget hinzufuegen</button>
        `;
        div.querySelector('#empty-add-widget').addEventListener('click', () => openModal('modal-widget'));
        return div;
    }

    function createWidgetCard(widget) {
        const card = document.createElement('div');
        card.className = 'widget-card';
        card.setAttribute('data-color', widget.color || 'default');

        const typeLabels = { number: 'Zahl', text: 'Text', list: 'Liste', chart: 'Diagramm' };
        let bodyContent = '';

        switch (widget.type) {
            case 'number':
                bodyContent = `<div class="widget-number">${escapeHtml(widget.content)}</div>`;
                break;
            case 'list':
                const items = widget.content.split('\n').filter(i => i.trim());
                bodyContent = '<ul>' + items.map(i => `<li>${escapeHtml(i)}</li>`).join('') + '</ul>';
                break;
            case 'chart':
                bodyContent = '<div style="color:var(--color-text-muted);font-style:italic;">Diagramm-Platzhalter — Datenquelle verbinden</div>';
                break;
            default:
                bodyContent = `<div>${escapeHtml(widget.content)}</div>`;
        }

        card.innerHTML = `
            <div class="widget-header">
                <span class="widget-title">${escapeHtml(widget.title)}</span>
                <span class="widget-type">${typeLabels[widget.type] || widget.type}</span>
            </div>
            <div class="widget-body">${bodyContent}</div>
            <div class="widget-footer">
                <button class="widget-btn delete" title="Loeschen">&#128465; Loeschen</button>
            </div>
        `;

        card.querySelector('.delete').addEventListener('click', () => {
            if (confirm('Widget wirklich loeschen?')) {
                const widgets = Data.getWidgets(currentUser.id).filter(w => w.id !== widget.id);
                Data.saveWidgets(currentUser.id, widgets);
                renderWidgets();
            }
        });

        return card;
    }

    // --- Data Sources ---
    function renderSources() {
        const sources = Data.getSources(currentUser.id);
        const emptyEl = $('#empty-sources');
        const listEl = $('#sources-list');

        if (sources.length === 0) {
            show(emptyEl);
            hide(listEl);
            return;
        }

        hide(emptyEl);
        show(listEl);

        const typeIcons = { api: '&#127760;', csv: '&#128196;', database: '&#128451;', manual: '&#9998;', other: '&#128268;' };

        listEl.innerHTML = '';
        sources.forEach(s => {
            const card = document.createElement('div');
            card.className = 'source-card';
            card.innerHTML = `
                <div class="source-icon">${typeIcons[s.type] || '&#128268;'}</div>
                <div class="source-info">
                    <div class="source-name">${escapeHtml(s.name)}</div>
                    <div class="source-meta">${escapeHtml(s.type.toUpperCase())}${s.url ? ' — ' + escapeHtml(s.url) : ''}${s.notes ? ' — ' + escapeHtml(s.notes) : ''}</div>
                </div>
                <div class="source-actions">
                    <button class="btn btn-danger btn-sm delete-source">Loeschen</button>
                </div>
            `;
            card.querySelector('.delete-source').addEventListener('click', () => {
                if (confirm('Datenquelle wirklich loeschen?')) {
                    const updated = Data.getSources(currentUser.id).filter(src => src.id !== s.id);
                    Data.saveSources(currentUser.id, updated);
                    renderSources();
                    renderWidgets();
                }
            });
            listEl.appendChild(card);
        });
    }

    // --- Modals ---
    function openModal(id) {
        show($(`#${id}`));
    }

    function closeModal(id) {
        hide($(`#${id}`));
        const form = $(`#${id} form`);
        if (form) form.reset();
    }

    // Close buttons
    $$('[data-close]').forEach(btn => {
        btn.addEventListener('click', () => closeModal(btn.dataset.close));
    });

    // Close on overlay click
    $$('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', e => {
            if (e.target === overlay) closeModal(overlay.id);
        });
    });

    $('#add-widget-btn').addEventListener('click', () => openModal('modal-widget'));
    $('#add-source-btn').addEventListener('click', () => openModal('modal-source'));
    $('#change-password-btn').addEventListener('click', () => openModal('modal-password'));

    // --- Widget Form ---
    $('#widget-form').addEventListener('submit', e => {
        e.preventDefault();
        const widget = {
            id: crypto.randomUUID ? crypto.randomUUID() : Date.now().toString(36),
            title: $('#widget-title').value.trim(),
            type: $('#widget-type').value,
            content: $('#widget-content').value.trim(),
            color: $('#widget-color').value,
            createdAt: new Date().toISOString()
        };
        const widgets = Data.getWidgets(currentUser.id);
        widgets.push(widget);
        Data.saveWidgets(currentUser.id, widgets);
        closeModal('modal-widget');
        renderWidgets();
    });

    // --- Source Form ---
    $('#source-form').addEventListener('submit', e => {
        e.preventDefault();
        const source = {
            id: crypto.randomUUID ? crypto.randomUUID() : Date.now().toString(36),
            name: $('#source-name').value.trim(),
            type: $('#source-type').value,
            url: $('#source-url').value.trim(),
            notes: $('#source-notes').value.trim(),
            createdAt: new Date().toISOString()
        };
        const sources = Data.getSources(currentUser.id);
        sources.push(source);
        Data.saveSources(currentUser.id, sources);
        closeModal('modal-source');
        renderSources();
        renderWidgets();
    });

    // --- Settings Form ---
    $('#settings-form').addEventListener('submit', e => {
        e.preventDefault();
        const newName = $('#settings-name').value.trim();
        if (newName && currentUser) {
            Auth.updateProfile(currentUser.id, { name: newName });
            currentUser.name = newName;
            $('#user-name').textContent = newName;
            $('#user-avatar').textContent = newName.charAt(0).toUpperCase();
            $('#topbar-user').textContent = newName;
            alert('Profil gespeichert.');
        }
    });

    // --- Password Form ---
    $('#password-form').addEventListener('submit', async e => {
        e.preventDefault();
        const errorEl = $('#password-error');
        hideError(errorEl);

        const current = $('#current-password').value;
        const newPw = $('#new-password').value;
        const confirmPw = $('#confirm-new-password').value;

        if (newPw !== confirmPw) {
            showError(errorEl, 'Die neuen Passwoerter stimmen nicht ueberein.');
            return;
        }

        try {
            await Auth.changePassword(currentUser.email, current, newPw);
            closeModal('modal-password');
            alert('Passwort erfolgreich geaendert.');
        } catch (err) {
            showError(errorEl, err.message);
        }
    });

    // --- Utility ---
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // --- Init: Check for existing session ---
    const existingUser = Auth.getCurrentUser();
    if (existingUser) {
        initDashboard(existingUser);
    } else {
        showView('login');
    }

})();
