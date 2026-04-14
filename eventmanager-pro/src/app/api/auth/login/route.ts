import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { prisma } from '@/lib/prisma';
import { verifyPassword } from '@/lib/auth';
import { issueSession } from '@/lib/session';

const schema = z.object({
  email: z.string().email('Ungültige E-Mail-Adresse'),
  passwort: z.string().min(1, 'Passwort erforderlich'),
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

  const { email, passwort } = parsed.data;
  const user = await prisma.user.findUnique({ where: { email: email.toLowerCase() } });

  // Einheitliche Fehlermeldung, damit man keine E-Mails erraten kann
  const invalid = () =>
    NextResponse.json({ error: 'E-Mail oder Passwort ist falsch' }, { status: 401 });

  if (!user || !user.aktiv) return invalid();
  const ok = await verifyPassword(passwort, user.passwortHash);
  if (!ok) return invalid();

  const res = NextResponse.json({
    user: { id: user.id, email: user.email, name: user.name, rolle: user.rolle },
  });
  await issueSession(res, { id: user.id, email: user.email, rolle: user.rolle });

  await prisma.auditLog.create({
    data: {
      userId: user.id,
      aktion: 'Login',
      ipAdresse: req.headers.get('x-forwarded-for') ?? req.headers.get('x-real-ip') ?? null,
    },
  });

  return res;
}
