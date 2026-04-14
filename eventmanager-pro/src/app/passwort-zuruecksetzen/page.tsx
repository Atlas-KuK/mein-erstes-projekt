'use client';

import { Suspense, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';

function ResetForm() {
  const router = useRouter();
  const params = useSearchParams();
  const token = params.get('token') ?? '';

  const [neuesPasswort, setNeuesPasswort] = useState('');
  const [wiederholung, setWiederholung] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [ok, setOk] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (neuesPasswort !== wiederholung) {
      setError('Die Passwörter stimmen nicht überein');
      return;
    }
    setLoading(true);
    const res = await fetch('/api/auth/reset-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token, neuesPasswort }),
    });
    setLoading(false);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      setError(data.error ?? 'Fehler beim Zurücksetzen');
      return;
    }
    setOk(true);
    setTimeout(() => router.push('/login'), 2000);
  }

  if (!token) {
    return (
      <div className="card">
        <p className="text-status-abgelehnt">Ungültiger Reset-Link.</p>
        <Link href="/passwort-vergessen" className="btn-secondary w-full mt-4">Neuen Link anfordern</Link>
      </div>
    );
  }

  return (
    <div className="card">
      <h1 className="text-xl font-semibold mb-4">Neues Passwort setzen</h1>

      {ok ? (
        <p className="text-status-bestaetigt text-sm">
          Passwort erfolgreich gesetzt. Du wirst weitergeleitet…
        </p>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="pw1" className="label">Neues Passwort</label>
            <input
              id="pw1"
              type="password"
              minLength={8}
              required
              value={neuesPasswort}
              onChange={(e) => setNeuesPasswort(e.target.value)}
              className="input"
            />
            <p className="text-xs text-base-400 mt-1">Mindestens 8 Zeichen</p>
          </div>
          <div>
            <label htmlFor="pw2" className="label">Passwort wiederholen</label>
            <input
              id="pw2"
              type="password"
              minLength={8}
              required
              value={wiederholung}
              onChange={(e) => setWiederholung(e.target.value)}
              className="input"
            />
          </div>

          {error && (
            <div className="rounded-md bg-status-abgelehnt/10 border border-status-abgelehnt/30 text-status-abgelehnt px-3 py-2 text-sm">
              {error}
            </div>
          )}

          <button type="submit" disabled={loading} className="btn-primary w-full">
            {loading ? 'Speichern…' : 'Passwort setzen'}
          </button>
        </form>
      )}
    </div>
  );
}

export default function Page() {
  return (
    <main className="min-h-screen flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-md">
        <Suspense fallback={<div className="card">Lade…</div>}>
          <ResetForm />
        </Suspense>
      </div>
    </main>
  );
}
