import { NextRequest, NextResponse } from 'next/server';
import { Rolle } from '@prisma/client';
import { prisma } from '@/lib/prisma';
import {
  authErrorResponse,
  getCurrentUserFromRequest,
  requireRole,
} from '@/lib/session';

type Ctx = { params: { id: string } };

// GET /api/users/:id/export — DSGVO Datenexport (Admin)
export async function GET(req: NextRequest, { params }: Ctx) {
  try {
    const me = requireRole(getCurrentUserFromRequest(req), Rolle.Admin);

    const user = await prisma.user.findUnique({
      where: { id: params.id },
      include: {
        auftraggeberEvents: { include: { catering: true, ablauf: true, marketing: true } },
        bearbeiteteEvents: true,
        erstellteEvents: true,
        auditLogs: true,
      },
    });
    if (!user) {
      return NextResponse.json({ error: 'Benutzer nicht gefunden' }, { status: 404 });
    }

    // Passwort-Hash & Token entfernen
    const {
      passwortHash, refreshTokenHash, passwortResetToken, twoFactorSecret,
      ...safe
    } = user;
    void passwortHash; void refreshTokenHash; void passwortResetToken; void twoFactorSecret;

    await prisma.auditLog.create({
      data: {
        userId: me.sub,
        aktion: 'DSGVO-Export',
        details: { zielUser: params.id },
      },
    });

    return new NextResponse(JSON.stringify(safe, null, 2), {
      headers: {
        'Content-Type': 'application/json; charset=utf-8',
        'Content-Disposition': `attachment; filename="user-${params.id}.json"`,
      },
    });
  } catch (err) {
    return authErrorResponse(err);
  }
}
