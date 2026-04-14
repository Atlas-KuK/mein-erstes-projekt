'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

export function LogoutButton({ className = 'btn-ghost text-sm' }: { className?: string }) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  async function handleLogout() {
    setLoading(true);
    await fetch('/api/auth/logout', { method: 'POST' }).catch(() => null);
    router.push('/login');
    router.refresh();
  }

  return (
    <button onClick={handleLogout} disabled={loading} className={className}>
      {loading ? 'Abmelden…' : 'Abmelden'}
    </button>
  );
}
