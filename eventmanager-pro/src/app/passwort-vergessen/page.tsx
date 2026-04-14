'use client';

import { useState } from 'react';
import Link from 'next/link';

export default function PasswortVergessenPage() {
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    await fetch('/api/auth/forgot-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    }).catch(() => null);
    setLoading(false);
    setSubmitted(true);
  }

  return (
    <main className="min-h-screen flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-md">
        <div className="card">
          <h1 className="text-xl font-semibold mb-4">Passwort zurücksetzen</h1>

          {submitted ? (
            <div className="space-y-4">
              <p className="text-base-300 text-sm">
                Falls ein Account mit dieser E-Mail existiert, haben wir einen
                Reset-Link verschickt. Prüfe dein Postfach (und den Spam-Ordner).
              </p>
              <Link href="/login" className="btn-secondary w-full">Zurück zum Login</Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <p className="text-base-300 text-sm">
                Gib deine E-Mail ein und wir senden dir einen Link zum Zurücksetzen.
              </p>
              <div>
                <label htmlFor="email" className="label">E-Mail</label>
                <input
                  id="email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="input"
                />
              </div>
              <button type="submit" disabled={loading} className="btn-primary w-full">
                {loading ? 'Senden…' : 'Reset-Link anfordern'}
              </button>
              <Link href="/login" className="btn-ghost w-full">Zurück</Link>
            </form>
          )}
        </div>
      </div>
    </main>
  );
}
