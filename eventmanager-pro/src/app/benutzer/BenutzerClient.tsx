'use client';

import { useState } from 'react';
import Link from 'next/link';
import type { Rolle } from '@prisma/client';

type UserRow = {
  id: string;
  email: string;
  name: string;
  rolle: Rolle;
  telefon: string | null;
  firma: string | null;
  aktiv: boolean;
  letzterLogin: Date | null;
};

const ROLLEN: Rolle[] = ['Admin', 'Teamleitung', 'Mitarbeiter', 'Kunde', 'Partner'];

export function BenutzerClient({ initialUsers }: { initialUsers: UserRow[] }) {
  const [users, setUsers] = useState(initialUsers);
  const [showForm, setShowForm] = useState(false);
  const [banner, setBanner] = useState<{ text: string; passwort?: string } | null>(null);

  async function handleCreate(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    const res = await fetch('/api/users', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: f.get('name'),
        email: f.get('email'),
        rolle: f.get('rolle'),
        telefon: f.get('telefon') || undefined,
        firma: f.get('firma') || undefined,
      }),
    });
    const data = await res.json();
    if (!res.ok) {
      setBanner({ text: data.error ?? 'Fehler beim Anlegen' });
      return;
    }
    setUsers([data.user, ...users]);
    setShowForm(false);
    setBanner({
      text: `Benutzer ${data.user.name} angelegt. Passwort weitergeben:`,
      passwort: data.initialesPasswort,
    });
  }

  async function handleResetPw(id: string, name: string) {
    if (!confirm(`Passwort für ${name} zurücksetzen?`)) return;
    const res = await fetch(`/api/users/${id}/reset-password`, { method: 'POST' });
    const data = await res.json();
    if (!res.ok) {
      setBanner({ text: data.error ?? 'Fehler' });
      return;
    }
    setBanner({ text: `Neues Passwort für ${name}:`, passwort: data.neuesPasswort });
  }

  async function handleDeactivate(id: string, name: string) {
    if (!confirm(`${name} deaktivieren?`)) return;
    const res = await fetch(`/api/users/${id}`, { method: 'DELETE' });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      setBanner({ text: data.error ?? 'Fehler' });
      return;
    }
    setUsers(users.map((u) => (u.id === id ? { ...u, aktiv: false } : u)));
  }

  return (
    <>
      {banner && (
        <div className="card mb-4 border-accent/40 bg-accent/5">
          <p className="text-sm">{banner.text}</p>
          {banner.passwort && (
            <p className="mt-2 font-mono text-lg text-accent break-all select-all">
              {banner.passwort}
            </p>
          )}
          <button onClick={() => setBanner(null)} className="btn-ghost text-xs mt-2">
            Schließen
          </button>
        </div>
      )}

      <div className="flex items-center justify-between mb-4">
        <Link href="/dashboard" className="btn-ghost text-sm">← Dashboard</Link>
        <button onClick={() => setShowForm(!showForm)} className="btn-primary text-sm">
          {showForm ? 'Abbrechen' : '+ Neuer Benutzer'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="card mb-6 space-y-3">
          <div className="grid sm:grid-cols-2 gap-3">
            <div>
              <label className="label">Name *</label>
              <input name="name" required className="input" />
            </div>
            <div>
              <label className="label">E-Mail *</label>
              <input name="email" type="email" required className="input" />
            </div>
            <div>
              <label className="label">Rolle *</label>
              <select name="rolle" required className="input" defaultValue="Mitarbeiter">
                {ROLLEN.map((r) => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>
            <div>
              <label className="label">Telefon</label>
              <input name="telefon" className="input" />
            </div>
            <div className="sm:col-span-2">
              <label className="label">Firma</label>
              <input name="firma" className="input" />
            </div>
          </div>
          <button type="submit" className="btn-primary">Anlegen (Passwort wird generiert)</button>
        </form>
      )}

      <div className="card p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-base-800 text-base-300 text-xs uppercase">
              <tr>
                <th className="text-left px-3 py-2">Name</th>
                <th className="text-left px-3 py-2">E-Mail</th>
                <th className="text-left px-3 py-2">Rolle</th>
                <th className="text-left px-3 py-2">Status</th>
                <th className="text-left px-3 py-2">Letzter Login</th>
                <th className="text-right px-3 py-2">Aktionen</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-t border-base-800">
                  <td className="px-3 py-2">{u.name}</td>
                  <td className="px-3 py-2 text-base-300">{u.email}</td>
                  <td className="px-3 py-2"><span className="text-accent">{u.rolle}</span></td>
                  <td className="px-3 py-2">
                    {u.aktiv
                      ? <span className="text-status-bestaetigt">aktiv</span>
                      : <span className="text-status-storniert">deaktiviert</span>}
                  </td>
                  <td className="px-3 py-2 text-base-400">
                    {u.letzterLogin ? new Date(u.letzterLogin).toLocaleString('de-DE') : '—'}
                  </td>
                  <td className="px-3 py-2 text-right whitespace-nowrap">
                    <button
                      onClick={() => handleResetPw(u.id, u.name)}
                      className="text-xs text-accent hover:text-accent-hover mr-3"
                    >Passwort</button>
                    {u.aktiv && (
                      <button
                        onClick={() => handleDeactivate(u.id, u.name)}
                        className="text-xs text-status-abgelehnt hover:underline"
                      >Deaktivieren</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
