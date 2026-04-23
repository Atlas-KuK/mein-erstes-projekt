// Supabase-Konfiguration
//
// So kommst du an die Werte:
// 1. https://supabase.com -> Projekt anlegen
// 2. Im Projekt: Settings -> API
// 3. "Project URL" und "anon public" key hier eintragen
//
// WICHTIG: Der anon key ist oeffentlich (darf im Browser stehen).
// Der "service_role" key NIEMALS hier eintragen!

window.SUPABASE_CONFIG = {
    url: 'https://DEIN-PROJEKT.supabase.co',
    anonKey: 'DEIN-ANON-KEY'
};
