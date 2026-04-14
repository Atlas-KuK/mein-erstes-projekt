import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { clearSession, getCurrentUserFromRequest } from '@/lib/session';

export async function POST(req: NextRequest) {
  const payload = getCurrentUserFromRequest(req);
  const res = NextResponse.json({ ok: true });

  if (payload) {
    // Refresh-Token in DB invalidieren
    await prisma.user
      .update({
        where: { id: payload.sub },
        data: { refreshTokenHash: null, refreshTokenExpires: null },
      })
      .catch(() => null);

    await prisma.auditLog.create({
      data: { userId: payload.sub, aktion: 'Logout' },
    });
  }

  clearSession(res);
  return res;
}
