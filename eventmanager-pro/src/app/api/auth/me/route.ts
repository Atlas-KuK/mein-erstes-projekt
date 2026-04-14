import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { getCurrentUserFromRequest } from '@/lib/session';

export async function GET(req: NextRequest) {
  const payload = getCurrentUserFromRequest(req);
  if (!payload) {
    return NextResponse.json({ error: 'Nicht authentifiziert' }, { status: 401 });
  }

  const user = await prisma.user.findUnique({
    where: { id: payload.sub },
    select: {
      id: true,
      email: true,
      name: true,
      rolle: true,
      telefon: true,
      firma: true,
      aktiv: true,
      twoFactorEnabled: true,
      letzterLogin: true,
    },
  });

  if (!user || !user.aktiv) {
    return NextResponse.json({ error: 'Account nicht verfügbar' }, { status: 401 });
  }
  return NextResponse.json({ user });
}
