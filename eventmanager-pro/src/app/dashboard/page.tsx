import { redirect } from 'next/navigation';
import Link from 'next/link';
import { prisma } from '@/lib/prisma';
import { getCurrentUser } from '@/lib/session';
import { LogoutButton } from '@/components/LogoutButton';

// Minimales Phase-1-Dashboard. Volles Dashboard folgt in Phase 2.
export default async function DashboardPage() {
  const payload = await getCurrentUser();
  if (!payload) redirect('/login');

  const user = await prisma.user.findUnique({
    where: { id: payload.sub },
    select: { id: true, name: true, email: true, rolle: true },
  });
  if (!user) redirect('/login');

  const [anzahlEvents, anzahlBestaetigt, anzahlOffen, anzahlUser] = await Promise.all([
    prisma.event.count(),
    prisma.event.count({ where: { status: 'Bestaetigt' } }),
    prisma.event.count({ where: { status: 'Offen' } }),
    prisma.user.count(),
  ]);

  return (
    <main className="min-h-screen px-4 py-6 sm:px-6 sm:py-8 max-w-6xl mx-auto">
      <header className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold">EventManager Pro</h1>
          <p className="text-base-400 text-sm mt-1">
            Hallo {user.name} <span className="text-accent">· {user.rolle}</span>
          </p>
        </div>
        <LogoutButton />
      </header>

      <section className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4 mb-8">
        <Kachel label="Events gesamt" wert={anzahlEvents} />
        <Kachel label="Bestätigt"      wert={anzahlBestaetigt} farbe="text-status-bestaetigt" />
        <Kachel label="Offen"          wert={anzahlOffen}       farbe="text-status-offen" />
        <Kachel label="Benutzer"       wert={anzahlUser} />
      </section>

      <section className="card">
        <h2 className="text-lg font-semibold mb-3">Phase 1 abgeschlossen</h2>
        <p className="text-base-300 text-sm mb-4">
          Fundament steht: Auth, Benutzerverwaltung, Datenbank-Schema, Seed-Daten.
          Die Event-Oberflächen (Jahresübersicht, Detail-Tabs, Monatsansicht) folgen in Phase 2.
        </p>
        {user.rolle === 'Admin' && (
          <div className="flex flex-wrap gap-2">
            <Link href="/benutzer" className="btn-secondary text-sm">Benutzer verwalten</Link>
          </div>
        )}
      </section>
    </main>
  );
}

function Kachel({
  label, wert, farbe = 'text-base-50',
}: { label: string; wert: number; farbe?: string }) {
  return (
    <div className="card">
      <p className="text-xs uppercase tracking-wide text-base-400">{label}</p>
      <p className={`text-3xl font-bold mt-1 ${farbe}`}>{wert}</p>
    </div>
  );
}
