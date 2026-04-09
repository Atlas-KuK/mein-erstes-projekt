/* Plaud Audio Processor - JavaScript */

// Auto-Refresh Dashboard alle 30 Sekunden
(function() {
    if (window.location.pathname === '/') {
        setTimeout(function() {
            location.reload();
        }, 30000);
    }
})();

// Status-Check
async function checkStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        return data;
    } catch(err) {
        console.error('Status-Check fehlgeschlagen:', err);
        return null;
    }
}
