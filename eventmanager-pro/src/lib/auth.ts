import bcrypt from 'bcryptjs';
import jwt, { JwtPayload } from 'jsonwebtoken';
import { randomBytes } from 'crypto';
import type { Rolle } from '@prisma/client';

// ---------------------------------------------------------------------------
// Umgebungsvariablen
// ---------------------------------------------------------------------------

function mustEnv(name: string): string {
  const v = process.env[name];
  if (!v) throw new Error(`Umgebungsvariable ${name} fehlt`);
  return v;
}

// Lazy: Env-Checks erst bei Verwendung, damit der Seed ohne JWT-Secrets
// (z.B. in CI oder vor dem ersten .env-Setup) lauffähig bleibt.
const accessSecret  = () => mustEnv('JWT_ACCESS_SECRET');
const refreshSecret = () => mustEnv('JWT_REFRESH_SECRET');
const accessExpires  = () => process.env.JWT_ACCESS_EXPIRES_IN  ?? '15m';
const refreshExpires = () => process.env.JWT_REFRESH_EXPIRES_IN ?? '7d';
const bcryptRounds   = () =>
  Number.parseInt(process.env.BCRYPT_ROUNDS ?? '12', 10);

// ---------------------------------------------------------------------------
// Passwort-Hashing
// ---------------------------------------------------------------------------

export async function hashPassword(plain: string): Promise<string> {
  return bcrypt.hash(plain, bcryptRounds());
}

export async function verifyPassword(plain: string, hash: string): Promise<boolean> {
  return bcrypt.compare(plain, hash);
}

// ---------------------------------------------------------------------------
// JWT
// ---------------------------------------------------------------------------

export interface AccessPayload extends JwtPayload {
  sub: string;      // User-ID
  rolle: Rolle;
  email: string;
}

export interface RefreshPayload extends JwtPayload {
  sub: string;
  jti: string;      // Token-ID, damit man serverseitig invalidieren kann
}

export function signAccessToken(payload: Omit<AccessPayload, 'iat' | 'exp'>): string {
  return jwt.sign(payload, accessSecret(), { expiresIn: accessExpires() } as jwt.SignOptions);
}

export function verifyAccessToken(token: string): AccessPayload {
  return jwt.verify(token, accessSecret()) as AccessPayload;
}

export function signRefreshToken(userId: string): { token: string; jti: string } {
  const jti = randomBytes(16).toString('hex');
  const token = jwt.sign(
    { sub: userId, jti },
    refreshSecret(),
    { expiresIn: refreshExpires() } as jwt.SignOptions,
  );
  return { token, jti };
}

export function verifyRefreshToken(token: string): RefreshPayload {
  return jwt.verify(token, refreshSecret()) as RefreshPayload;
}

// ---------------------------------------------------------------------------
// Passwort-Reset-Token
// ---------------------------------------------------------------------------

export function generateResetToken(): { token: string; expires: Date } {
  const token = randomBytes(32).toString('hex');
  const expires = new Date(Date.now() + 60 * 60 * 1000); // 1h
  return { token, expires };
}

// ---------------------------------------------------------------------------
// Initiales Passwort generieren (für Admin-Setup / Einladungen)
// ---------------------------------------------------------------------------

export function generateInitialPassword(length = 14): string {
  // URL-sicheres Alphabet, keine leicht verwechselbaren Zeichen
  const alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789';
  const buf = randomBytes(length);
  let out = '';
  for (let i = 0; i < length; i++) out += alphabet[buf[i] % alphabet.length];
  return out;
}
