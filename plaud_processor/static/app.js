'use strict';

// Automatisch alle 30 Sekunden neu laden, wenn ausstehende Aufnahmen vorhanden
(function autoreload() {
  const pendingCards = document.querySelectorAll('.card-pending');
  if (pendingCards.length > 0) {
    setTimeout(() => location.reload(), 30_000);
  }
})();

// Formular-Submit: Button deaktivieren, um Doppel-Submit zu verhindern
document.querySelectorAll('form').forEach((form) => {
  form.addEventListener('submit', () => {
    form.querySelectorAll('button[type="submit"]').forEach((btn) => {
      btn.disabled = true;
      btn.textContent = 'Bitte warten...';
    });
  });
});
