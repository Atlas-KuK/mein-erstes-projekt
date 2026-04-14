import { cookies } from 'next/headers';
import { NextRequest, NextResponse } from 'next/server';
import { Rolle } from '@prisma/client';
import { prisma } from './prisma';
import {
  AccessPayload,
  signAccessToken,
  signRefreshToken,
  verifyAccessToken,
  hashPassword,
} from './auth';

// Cookie-Namen
export const ACCESS_COOKIE  = 'emp_access';
export const REFRESH_COOKIE = 'emp_refresh';

const isProd = process.env.NODE_ENV === 'production';
const FIFTEEN_MIN = 15 * 60;
const SEVEN_DAYS  = 7 * 24 * 60 * 60;

// ---------------------------------------------------------------------------
// Cookies setzen / löschen
// ---------------------------------------------------------------------------

export async function issueSession(
  res: NextResponse,
  user: { id: string; email: string; rolle: Rolle },
) {
  const accessToken = signAccessToken({
    sub: user.id,
    email: user.email,
    rolle: user.rolle,
  });
  const { token: refreshToken } = signRefreshToken(user.id);

  // Refresh-Token-Hash in DB speichern, damit Logout/Invalidierung möglich
  const refreshHash = await hashPassword(refreshToken);
  await prisma.user.update({
    where: { id: user.id },
    data: {
      refreshTokenHash: refreshHash,
      refreshTokenExpires: new Date(Date.now() + SEVEN_DAYS * 1000),
      letzterLogin: new Date(),
    },
  });

  res.cookies.set(ACCESS_COOKIE, accessToken, {
    httpOnly: true,
    secure: isProd,
    sameSite: 'lax',
    path: '/',
    maxAge: FIFTEEN_MIN,
  });
  res.cookies.set(REFRESH_COOKIE, refreshToken, {
    httpOnly: true,
    secure: isProd,
    sameSite: 'lax',
    path: '/',
    maxAge: SEVEN_DAYS,
  });
}

export function clearSession(res: NextResponse) {
  res.cookies.set(ACCESS_COOKIE,  '', { path: '/', maxAge: 0 });
  res.cookies.set(REFRESH_COOKIE, '', { path: '/', maxAge: 0 });
}

// ---------------------------------------------------------------------------
// Session aus Request lesen (Server Components / API Routes)
// ---------------------------------------------------------------------------

export async function getCurrentUser(): Promise<AccessPayload | null> {
  const jar = cookies();
  const token = jar.get(ACCESS_COOKIE)?.value;
  if (!token) return null;
  try {
    return verifyAccessToken(token);
  } catch {
    return null;
  }
}

export function getCurrentUserFromRequest(req: NextRequest): AccessPayload | null {
  const token = req.cookies.get(ACCESS_COOKIE)?.value;
  if (!token) return null;
  try {
    return verifyAccessToken(token);
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// Rollen-Guard
// ---------------------------------------------------------------------------

export function hasRole(payload: AccessPayload | null, ...allowed: Rolle[]): boolean {
  return !!payload && allowed.includes(payload.rolle);
}

export function requireRole(payload: AccessPayload | null, ...allowed: Rolle[]): AccessPayload {
  if (!payload) {
    throw new AuthError(401, 'Nicht authentifiziert');
  }
  if (!allowed.includes(payload.rolle)) {
    throw new AuthError(403, 'Keine Berechtigung');
  }
  return payload;
}

export class AuthError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'AuthError';
  }
}

export function authErrorResponse(err: unknown): NextResponse {
  if (err instanceof AuthError) {
    return NextResponse.json({ error: err.message }, { status: err.status });
  }
  console.error(err);
  return NextResponse.json({ error: 'Interner Fehler' }, { status: 500 });
}
