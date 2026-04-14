import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { Rolle } from '@prisma/client';
import { prisma } from '@/lib/prisma';
import {
  authErrorResponse,
  getCurrentUserFromRequest,
  requireRole,
} from '@/lib/session';

const updateSchema = z.object({
  name: z.string().min(1).optional(),
  email: z.string().email().optional(),
  rolle: z.nativeEnum(Rolle).optional(),
  telefon: z.string().nullable().optional(),
  firma: z.string().nullable().optional(),
  aktiv: z.boolean().optional(),
});

type Ctx = { params: { id: string } };

// PUT /api/users/:id — bearbeiten (Admin)
export async function PUT(req: NextRequest, { params }: Ctx) {
  try {
    const me = requireRole(getCurrentUserFromRequest(req), Rolle.Admin);

    const body = await req.json().catch(() => null);
    const parsed = updateSchema.safeParse(body);
    if (!parsed.success) {
      return NextResponse.json(
        { error: parsed.error.issues[0]?.message ?? 'Ungültige Eingabe' },
        { status: 400 },
      );
    }

    const data = { ...parsed.data };
    if (data.email) data.email = data.email.toLowerCase();

    const user = await prisma.user.update({
      where: { id: params.id },
      data,
      select: {
        id: true, email: true, name: true, rolle: true,
        telefon: true, firma: true, aktiv: true,
      },
    });

    await prisma.auditLog.create({
      data: { userId: me.sub, aktion: 'Benutzer bearbeitet', details: { zielUser: params.id } },
    });

    return NextResponse.json({ user });
  } catch (err) {
    return authErrorResponse(err);
  }
}

// DELETE /api/users/:id — deaktivieren (Admin) - soft delete, Audit-Log bleibt
export async function DELETE(req: NextRequest, { params }: Ctx) {
  try {
    const me = requireRole(getCurrentUserFromRequest(req), Rolle.Admin);

    if (me.sub === params.id) {
      return NextResponse.json(
        { error: 'Admin kann sich nicht selbst deaktivieren' },
        { status: 400 },
      );
    }

    await prisma.user.update({
      where: { id: params.id },
      data: { aktiv: false, refreshTokenHash: null, refreshTokenExpires: null },
    });

    await prisma.auditLog.create({
      data: { userId: me.sub, aktion: 'Benutzer deaktiviert', details: { zielUser: params.id } },
    });

    return NextResponse.json({ ok: true });
  } catch (err) {
    return authErrorResponse(err);
  }
}
