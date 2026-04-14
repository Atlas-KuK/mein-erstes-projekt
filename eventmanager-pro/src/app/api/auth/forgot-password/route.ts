import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { prisma } from '@/lib/prisma';
import { generateResetToken } from '@/lib/auth';

const schema = z.object({ email: z.string().email() });

export async function POST(req: NextRequest) {
  const body = await req.json().catch(() => null);
  const parsed = schema.safeParse(body);
  if (!parsed.success) {
    // Keine Info rausgeben, ob E-Mail existiert
    return NextResponse.json({ ok: true });
  }

  const user = await prisma.user.findUnique({
    where: { email: parsed.data.email.toLowerCase() },
  });

  if (user && user.aktiv) {
    const { token, expires } = generateResetToken();
    await prisma.user.update({
      where: { id: user.id },
      data: { passwortResetToken: token, passwortResetBis: expires },
    });

    // E-Mail-Versand ist in Phase 1 noch nicht konfiguriert.
    // In Entwicklung Link in der Konsole ausgeben, damit man testen kann.
    const appUrl = process.env.APP_URL ?? 'http://localhost:3000';
    const link = `${appUrl}/passwort-zuruecksetzen?token=${token}`;
    // eslint-disable-next-line no-console
    console.log(`[Passwort-Reset] Link für ${user.email}: ${link}`);

    await prisma.auditLog.create({
      data: { userId: user.id, aktion: 'Passwort-Reset angefordert' },
    });
  }

  // Immer identische Antwort
  return NextResponse.json({ ok: true });
}
