// Zentrale Auth-Helfer fuer das Dashboard
// Erwartet, dass vorher geladen wurden:
//   <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
//   <script src="config.js"></script>

(function () {
    const client = window.supabase.createClient(
        window.SUPABASE_CONFIG.url,
        window.SUPABASE_CONFIG.anonKey
    );

    // Pfad zur login.html relativ zur aktuellen Seite
    const loginPath = window.location.pathname.includes('/projekte/')
        ? '../login.html'
        : 'login.html';
    const dashboardPath = window.location.pathname.includes('/projekte/')
        ? '../index.html'
        : 'index.html';

    async function requireLogin() {
        const { data: { session } } = await client.auth.getSession();
        if (!session) {
            window.location.href = loginPath;
            return null;
        }
        return session.user;
    }

    async function logout() {
        await client.auth.signOut();
        window.location.href = loginPath;
    }

    async function login(email, password) {
        return await client.auth.signInWithPassword({ email, password });
    }

    window.auth = {
        client,
        requireLogin,
        logout,
        login,
        loginPath,
        dashboardPath
    };
})();
