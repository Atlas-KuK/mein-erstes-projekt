import { NextRequest, NextResponse } from 'next/server';
import { Rolle } from '@prisma/client';
import { prisma } from '@/lib/prisma';
import {
  authErrorResponse,
  getCurrentUserFromRequest,
  requireRole,
} from '@/lib/session';

type Ctx = { params: { id: string } };

// DELETE /api/users/:id/data — DSGVO-Löschung (Admin)
// Löscht personenbezogene Daten. Events bleiben bestehen, Relationen werden auf null gesetzt.
export async function DELETE(req: NextRequest, { params }: Ctx) {
  try {
    const me = requireRole(getCurrentUserFromRequest(req), Rolle.Admin);

    if (me.sub === params.id) {
      return NextResponse.json(
        { error: 'Admin kann sich nicht selbst löschen' },
        { status: 400 },
      );
    }

    await prisma.$transaction([
      prisma.auditLog.deleteMany({ where: { userId: params.id } }),
      prisma.user.delete({ where: { id: params.id } }),
    ]);

    await prisma.auditLog.create({
      data: {
        userId: me.sub,
        aktion: 'DSGVO-Löschung',
        details: { zielUser: params.id },
      },
    });

    return NextResponse.json({ ok: true });
  } catch (err) {
    return authErrorResponse(err);
  }
}
