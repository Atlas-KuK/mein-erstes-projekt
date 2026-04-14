import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { Rolle } from '@prisma/client';
import { prisma } from '@/lib/prisma';
import { generateInitialPassword, hashPassword } from '@/lib/auth';
import {
  authErrorResponse,
  getCurrentUserFromRequest,
  requireRole,
} from '@/lib/session';

const createSchema = z.object({
  name: z.string().min(1, 'Name erforderlich'),
  email: z.string().email('Ungültige E-Mail'),
  rolle: z.nativeEnum(Rolle),
  telefon: z.string().optional(),
  firma: z.string().optional(),
  passwort: z.string().min(8).optional(), // wenn leer: generieren
});

// GET /api/users — Liste (nur Admin)
export async function GET(req: NextRequest) {
  try {
    const me = requireRole(getCurrentUserFromRequest(req), Rolle.Admin);
    void me;

    const users = await prisma.user.findMany({
      orderBy: { erstelltAm: 'desc' },
      select: {
        id: true,
        email: true,
        name: true,
        rolle: true,
        telefon: true,
        firma: true,
        aktiv: true,
        letzterLogin: true,
        erstelltAm: true,
      },
    });
    return NextResponse.json({ users });
  } catch (err) {
    return authErrorResponse(err);
  }
}

// POST /api/users — Benutzer anlegen (nur Admin)
export async function POST(req: NextRequest) {
  try {
    const me = requireRole(getCurrentUserFromRequest(req), Rolle.Admin);

    const body = await req.json().catch(() => null);
    const parsed = createSchema.safeParse(body);
    if (!parsed.success) {
      return NextResponse.json(
        { error: parsed.error.issues[0]?.message ?? 'Ungültige Eingabe' },
        { status: 400 },
      );
    }
    const { name, email, rolle, telefon, firma, passwort } = parsed.data;

    const existing = await prisma.user.findUnique({ where: { email: email.toLowerCase() } });
    if (existing) {
      return NextResponse.json(
        { error: 'E-Mail-Adresse ist bereits vergeben' },
        { status: 409 },
      );
    }

    const initialesPasswort = passwort ?? generateInitialPassword();
    const passwortHash = await hashPassword(initialesPasswort);

    const user = await prisma.user.create({
      data: {
        name,
        email: email.toLowerCase(),
        rolle,
        telefon: telefon || null,
        firma: firma || null,
        passwortHash,
      },
      select: {
        id: true,
        email: true,
        name: true,
        rolle: true,
        telefon: true,
        firma: true,
        aktiv: true,
        erstelltAm: true,
      },
    });

    await prisma.auditLog.create({
      data: {
        userId: me.sub,
        aktion: 'Benutzer angelegt',
        details: { zielUser: user.id, rolle },
      },
    });

    // Passwort wird genau einmal im Response zurückgegeben, damit Admin es
    // per WhatsApp / E-Mail weitergeben kann. Danach nie wieder sichtbar.
    return NextResponse.json({ user, initialesPasswort }, { status: 201 });
  } catch (err) {
    return authErrorResponse(err);
  }
}
