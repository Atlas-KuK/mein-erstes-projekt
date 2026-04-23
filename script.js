// Seite nur fuer eingeloggte User
(async () => {
    const user = await window.auth.requireLogin();
    if (!user) return;

    const emailEl = document.getElementById('user-email');
    const nameEl = document.getElementById('user-name');
    if (emailEl) emailEl.textContent = user.email;
    if (nameEl) {
        const vorname = (user.user_metadata && user.user_metadata.vorname) || '';
        nameEl.textContent = vorname ? ', ' + vorname : '';
    }
})();

// Logout
const logoutLink = document.getElementById('logout-link');
if (logoutLink) {
    logoutLink.addEventListener('click', e => {
        e.preventDefault();
        window.auth.logout();
    });
}

// Smooth scrolling fuer Anker-Links
document.querySelectorAll('nav a').forEach(link => {
    const href = link.getAttribute('href');
    if (href && href.startsWith('#')) {
        link.addEventListener('click', e => {
            e.preventDefault();
            const target = document.querySelector(href);
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    }
});

// Schnellnotiz im LocalStorage
const notizFeld = document.getElementById('notiz-feld');
if (notizFeld) {
    notizFeld.value = localStorage.getItem('dashboard-notiz') || '';
    notizFeld.addEventListener('input', () => {
        localStorage.setItem('dashboard-notiz', notizFeld.value);
    });
}

// Platzhalter fuer "Neues Projekt"
const kachelNeu = document.getElementById('kachel-neu');
if (kachelNeu) {
    kachelNeu.addEventListener('click', e => {
        e.preventDefault();
        alert('Hier kommt spaeter der Dialog zum Anlegen eines neuen Projekts.');
    });
}

const btnNeu = document.getElementById('neues-projekt');
if (btnNeu) {
    btnNeu.addEventListener('click', () => {
        alert('Hier kommt spaeter der Dialog zum Anlegen eines neuen Projekts.');
    });
}
