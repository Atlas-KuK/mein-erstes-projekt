import { redirect } from 'next/navigation';
import { prisma } from '@/lib/prisma';
import { getCurrentUser } from '@/lib/session';
import { BenutzerClient } from './BenutzerClient';

export default async function BenutzerPage() {
  const payload = await getCurrentUser();
  if (!payload) redirect('/login');
  if (payload.rolle !== 'Admin') redirect('/dashboard');

  const users = await prisma.user.findMany({
    orderBy: { erstelltAm: 'desc' },
    select: {
      id: true, email: true, name: true, rolle: true,
      telefon: true, firma: true, aktiv: true, letzterLogin: true,
    },
  });

  return (
    <main className="min-h-screen px-4 py-6 sm:px-6 sm:py-8 max-w-6xl mx-auto">
      <header className="mb-6">
        <h1 className="text-2xl font-bold">Benutzerverwaltung</h1>
        <p className="text-base-400 text-sm mt-1">Konten anlegen, Rollen vergeben, deaktivieren</p>
      </header>
      <BenutzerClient initialUsers={users} />
    </main>
  );
}
