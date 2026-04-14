import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { prisma } from '@/lib/prisma';
import { hashPassword, verifyPassword } from '@/lib/auth';
import { getCurrentUserFromRequest } from '@/lib/session';

const schema = z.object({
  aktuellesPasswort: z.string().min(1),
  neuesPasswort: z.string().min(8, 'Passwort muss mindestens 8 Zeichen haben'),
});

export async function POST(req: NextRequest) {
  const payload = getCurrentUserFromRequest(req);
  if (!payload) {
    return NextResponse.json({ error: 'Nicht authentifiziert' }, { status: 401 });
  }

  const body = await req.json().catch(() => null);
  const parsed = schema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json(
      { error: parsed.error.issues[0]?.message ?? 'Ungültige Eingabe' },
      { status: 400 },
    );
  }

  const user = await prisma.user.findUnique({ where: { id: payload.sub } });
  if (!user || !user.aktiv) {
    return NextResponse.json({ error: 'Account nicht verfügbar' }, { status: 401 });
  }

  const ok = await verifyPassword(parsed.data.aktuellesPasswort, user.passwortHash);
  if (!ok) {
    return NextResponse.json({ error: 'Aktuelles Passwort ist falsch' }, { status: 400 });
  }

  await prisma.user.update({
    where: { id: user.id },
    data: { passwortHash: await hashPassword(parsed.data.neuesPasswort) },
  });

  await prisma.auditLog.create({
    data: { userId: user.id, aktion: 'Passwort geändert' },
  });

  return NextResponse.json({ ok: true });
}
