import { NextRequest, NextResponse } from 'next/server';
import { Rolle } from '@prisma/client';
import { prisma } from '@/lib/prisma';
import { generateInitialPassword, hashPassword } from '@/lib/auth';
import {
  authErrorResponse,
  getCurrentUserFromRequest,
  requireRole,
} from '@/lib/session';

type Ctx = { params: { id: string } };

// POST /api/users/:id/reset-password — Admin setzt Passwort zurück
export async function POST(req: NextRequest, { params }: Ctx) {
  try {
    const me = requireRole(getCurrentUserFromRequest(req), Rolle.Admin);

    const neuesPasswort = generateInitialPassword();
    await prisma.user.update({
      where: { id: params.id },
      data: {
        passwortHash: await hashPassword(neuesPasswort),
        passwortResetToken: null,
        passwortResetBis: null,
        refreshTokenHash: null,
        refreshTokenExpires: null,
      },
    });

    await prisma.auditLog.create({
      data: {
        userId: me.sub,
        aktion: 'Passwort durch Admin zurückgesetzt',
        details: { zielUser: params.id },
      },
    });

    return NextResponse.json({ neuesPasswort });
  } catch (err) {
    return authErrorResponse(err);
  }
}
