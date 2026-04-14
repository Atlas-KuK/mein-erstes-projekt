'use client';

import { Suspense, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';

function LoginForm() {
  const router = useRouter();
  const params = useSearchParams();
  const redirectTo = params.get('redirect') || '/dashboard';

  const [email, setEmail] = useState('');
  const [passwort, setPasswort] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, passwort }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error ?? 'Login fehlgeschlagen');
        return;
      }
      router.push(redirectTo);
      router.refresh();
    } catch {
      setError('Netzwerkfehler – bitte erneut versuchen');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card">
      <h2 className="text-xl font-semibold mb-5">Anmelden</h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="email" className="label">E-Mail</label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="input"
            placeholder="name@firma.de"
          />
        </div>

        <div>
          <label htmlFor="passwort" className="label">Passwort</label>
          <input
            id="passwort"
            type="password"
            autoComplete="current-password"
            required
            value={passwort}
            onChange={(e) => setPasswort(e.target.value)}
            className="input"
            placeholder="••••••••"
          />
        </div>

        {error && (
          <div className="rounded-md bg-status-abgelehnt/10 border border-status-abgelehnt/30 text-status-abgelehnt px-3 py-2 text-sm">
            {error}
          </div>
        )}

        <button type="submit" disabled={loading} className="btn-primary w-full">
          {loading ? 'Anmelden…' : 'Anmelden'}
        </button>
      </form>

      <div className="mt-5 text-center">
        <Link href="/passwort-vergessen" className="text-sm text-accent hover:text-accent-hover">
          Passwort vergessen?
        </Link>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <main className="min-h-screen flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-base-50">EventManager Pro</h1>
          <p className="text-base-400 mt-2 text-sm">Lucky Event · Mettgenpin 1877 · Schänke 1998</p>
        </div>

        <Suspense fallback={<div className="card">Lade…</div>}>
          <LoginForm />
        </Suspense>

        <p className="mt-6 text-center text-xs text-base-500">
          Mit der Anmeldung akzeptierst du die{' '}
          <Link href="/datenschutz" className="underline hover:text-base-300">Datenschutzerklärung</Link>.
        </p>
      </div>
    </main>
  );
}
