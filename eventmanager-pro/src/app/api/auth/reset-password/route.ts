import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { prisma } from '@/lib/prisma';
import { hashPassword } from '@/lib/auth';

const schema = z.object({
  token: z.string().min(10),
  neuesPasswort: z.string().min(8, 'Passwort muss mindestens 8 Zeichen haben'),
});

export async function POST(req: NextRequest) {
  const body = await req.json().catch(() => null);
  const parsed = schema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json(
      { error: parsed.error.issues[0]?.message ?? 'Ungültige Eingabe' },
      { status: 400 },
    );
  }

  const user = await prisma.user.findFirst({
    where: {
      passwortResetToken: parsed.data.token,
      passwortResetBis: { gt: new Date() },
      aktiv: true,
    },
  });

  if (!user) {
    return NextResponse.json(
      { error: 'Reset-Link ist ungültig oder abgelaufen' },
      { status: 400 },
    );
  }

  const passwortHash = await hashPassword(parsed.data.neuesPasswort);
  await prisma.user.update({
    where: { id: user.id },
    data: {
      passwortHash,
      passwortResetToken: null,
      passwortResetBis: null,
      refreshTokenHash: null, // alle aktiven Sessions invalidieren
      refreshTokenExpires: null,
    },
  });

  await prisma.auditLog.create({
    data: { userId: user.id, aktion: 'Passwort zurückgesetzt' },
  });

  return NextResponse.json({ ok: true });
}
