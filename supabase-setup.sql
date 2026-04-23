-- ============================================================
-- Supabase-Setup fuer das Dashboard
-- ============================================================
-- So fuehrst du das aus:
-- 1. https://supabase.com  ->  neues Projekt anlegen (kostenlos)
-- 2. Links im Menue: "SQL Editor"
-- 3. Diesen ganzen Inhalt reinkopieren und "Run" druecken
-- 4. Settings -> API -> Project URL + anon key in config.js eintragen
-- 5. Authentication -> Users -> "Add user" fuer dich, Vater, Bruder
-- ============================================================

-- Tabelle: Unternehmungen
create table if not exists unternehmungen (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    beschreibung text,
    created_at timestamptz default now()
);

-- Tabelle: Cashflow-Eintraege
create table if not exists cashflow (
    id uuid primary key default gen_random_uuid(),
    unternehmung_id uuid references unternehmungen(id) on delete cascade,
    datum date not null default current_date,
    typ text not null check (typ in ('einnahme', 'ausgabe')),
    betrag numeric(12, 2) not null,
    beschreibung text,
    created_by uuid references auth.users(id) default auth.uid(),
    created_at timestamptz default now()
);

-- Row Level Security aktivieren
alter table unternehmungen enable row level security;
alter table cashflow enable row level security;

-- Policies: alle angemeldeten User duerfen lesen und schreiben
-- (Spaeter kann man hier Rollen feiner trennen, z.B. Steuerberater nur lesen)
create policy "auth_select_unternehmungen" on unternehmungen
    for select using (auth.role() = 'authenticated');
create policy "auth_insert_unternehmungen" on unternehmungen
    for insert with check (auth.role() = 'authenticated');
create policy "auth_update_unternehmungen" on unternehmungen
    for update using (auth.role() = 'authenticated');
create policy "auth_delete_unternehmungen" on unternehmungen
    for delete using (auth.role() = 'authenticated');

create policy "auth_select_cashflow" on cashflow
    for select using (auth.role() = 'authenticated');
create policy "auth_insert_cashflow" on cashflow
    for insert with check (auth.role() = 'authenticated');
create policy "auth_update_cashflow" on cashflow
    for update using (auth.role() = 'authenticated');
create policy "auth_delete_cashflow" on cashflow
    for delete using (auth.role() = 'authenticated');

-- Index fuer schnellere Abfragen
create index if not exists cashflow_unternehmung_idx on cashflow(unternehmung_id, datum desc);
