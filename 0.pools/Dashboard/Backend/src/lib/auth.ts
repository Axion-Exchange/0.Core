import jwt from 'jsonwebtoken';
import bcrypt from 'bcryptjs';
import crypto from 'crypto';

// SECURITY: Fail hard if JWT_SECRET is not set in production
const JWT_SECRET = process.env.JWT_SECRET;
if (!JWT_SECRET && process.env.NODE_ENV === 'production') {
  throw new Error('FATAL: JWT_SECRET environment variable is required in production');
}
const SECRET = JWT_SECRET || 'dev-only-secret-DO-NOT-USE-IN-PRODUCTION';

// Short-lived access tokens (24h) — institutional standard
const JWT_EXPIRES_IN = process.env.JWT_EXPIRES_IN || '24h';
const BCRYPT_ROUNDS = 12;

export interface JWTPayload {
  userId: string;
  email: string;
  roleSlug: string;
  sessionId: string; // Required for server-side session validation
}

export function signToken(payload: JWTPayload): string {
  return jwt.sign(payload, SECRET, { expiresIn: JWT_EXPIRES_IN as any });
}

export function verifyToken(token: string): JWTPayload {
  return jwt.verify(token, SECRET) as JWTPayload;
}

export async function hashPassword(password: string): Promise<string> {
  return bcrypt.hash(password, BCRYPT_ROUNDS);
}

export async function comparePassword(password: string, hash: string): Promise<boolean> {
  return bcrypt.compare(password, hash);
}

/**
 * Generate a cryptographically secure reference ID
 */
export function generateReference(): string {
  const bytes = crypto.randomBytes(6);
  return 'AX-' + bytes.toString('hex').toUpperCase().slice(0, 8);
}

/**
 * Generate a CSRF token — HMAC-SHA256 of sessionId with a server secret
 */
export function generateCSRFToken(sessionId: string): string {
  return crypto.createHmac('sha256', SECRET).update(sessionId).digest('hex');
}

/**
 * Verify a CSRF token matches the expected session
 */
export function verifyCSRFToken(token: string, sessionId: string): boolean {
  const expected = generateCSRFToken(sessionId);
  return crypto.timingSafeEqual(Buffer.from(token), Buffer.from(expected));
}
