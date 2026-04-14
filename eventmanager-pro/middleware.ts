import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Einfacher Edge-Middleware-Guard: leitet unauthentifizierte Requests auf /login um.
// Die eigentliche JWT-Verifikation passiert in API-Routen und Server Components
// (edge-compatibles `jsonwebtoken` wäre fragil). Dieser Check prüft nur das
// Vorhandensein des Cookies und schützt vor versehentlichen Direktaufrufen.

const PUBLIC_PATHS = [
  '/login',
  '/passwort-vergessen',
  '/passwort-zuruecksetzen',
  '/datenschutz',
  '/api/auth/login',
  '/api/auth/logout',
  '/api/auth/forgot-password',
  '/api/auth/reset-password',
  '/api/auth/refresh',
];

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  // Public assets durchlassen
  if (
    pathname.startsWith('/_next') ||
    pathname.startsWith('/favicon') ||
    pathname.startsWith('/icons') ||
    pathname === '/manifest.webmanifest'
  ) {
    return NextResponse.next();
  }

  // Public routes durchlassen
  if (PUBLIC_PATHS.some((p) => pathname === p || pathname.startsWith(p + '/'))) {
    return NextResponse.next();
  }

  const hasAccess = req.cookies.get('emp_access')?.value;
  if (!hasAccess) {
    const url = req.nextUrl.clone();
    url.pathname = '/login';
    url.searchParams.set('redirect', pathname);
    return NextResponse.redirect(url);
  }
  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
