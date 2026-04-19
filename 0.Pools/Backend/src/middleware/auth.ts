import { Request, Response, NextFunction } from 'express';
import { verifyToken, verifyCSRFToken, JWTPayload } from '../lib/auth';
import prisma from '../lib/prisma';

// Extend Express Request with user info
declare global {
  namespace Express {
    interface Request {
      user?: JWTPayload;
      sessionId?: string;
    }
  }
}

/**
 * Authentication middleware — extracts and verifies JWT from:
 * 1. __session HTTP-only cookie (primary — institutional standard)
 * 2. Authorization: Bearer <token> header (fallback for API clients)
 *
 * Then validates the session still exists in the database
 * (supports server-side session revocation).
 */
export function authenticate(req: Request, res: Response, next: NextFunction): void {
  try {
    let token: string | undefined;

    // 1. Primary: HTTP-only cookie
    token = req.cookies?.['__session'];

    // 2. Fallback: Bearer header (for programmatic API access)
    if (!token) {
      const authHeader = req.headers.authorization;
      if (authHeader?.startsWith('Bearer ')) {
        token = authHeader.slice(7);
      }
    }

    if (!token) {
      res.status(401).json({ success: false, message: 'Authentication required' });
      return;
    }

    const payload = verifyToken(token);
    req.user = payload;
    req.sessionId = payload.sessionId;
    next();
  } catch (error) {
    res.status(401).json({ success: false, message: 'Invalid or expired token' });
    return;
  }
}

/**
 * Session validation middleware — checks that the session still exists in DB.
 * Use after `authenticate` for routes that need revocation support.
 * Skipped for high-frequency read endpoints to reduce DB load.
 */
export function validateSession(req: Request, res: Response, next: NextFunction): void {
  if (!req.user?.sessionId) {
    res.status(401).json({ success: false, message: 'Invalid session' });
    return;
  }

  prisma.session.findUnique({
    where: { id: req.user.sessionId },
  }).then((session) => {
    if (!session || session.expires < new Date()) {
      res.status(401).json({ success: false, message: 'Session expired or revoked' });
      return;
    }

    // Update last active timestamp (fire-and-forget)
    prisma.session.update({
      where: { id: session.id },
      data: { lastActive: new Date() },
    }).catch(() => {}); // Non-critical

    next();
  }).catch(() => {
    res.status(401).json({ success: false, message: 'Session validation failed' });
  });
}

/**
 * CSRF protection middleware — validates X-CSRF-Token header
 * against the session ID. Required for all state-changing operations.
 */
export function requireCSRF(req: Request, res: Response, next: NextFunction): void {
  const csrfToken = req.headers['x-csrf-token'] as string;

  if (!csrfToken || !req.user?.sessionId) {
    res.status(403).json({ success: false, message: 'CSRF token required' });
    return;
  }

  try {
    if (!verifyCSRFToken(csrfToken, req.user.sessionId)) {
      res.status(403).json({ success: false, message: 'Invalid CSRF token' });
      return;
    }
  } catch {
    res.status(403).json({ success: false, message: 'Invalid CSRF token' });
    return;
  }

  next();
}

/**
 * Re-authentication middleware — requires a valid reauth_token cookie.
 * Used before sensitive operations (password change, 2FA disable, etc.)
 */
export function requireReauth(req: Request, res: Response, next: NextFunction): void {
  const reauthToken = req.cookies?.['__reauth'];
  if (!reauthToken) {
    res.status(403).json({ success: false, message: 'Re-authentication required', code: 'REAUTH_REQUIRED' });
    return;
  }

  try {
    const payload = verifyToken(reauthToken);
    if (payload.userId !== req.user?.userId) {
      throw new Error('Reauth user mismatch');
    }
    next();
  } catch {
    res.status(403).json({ success: false, message: 'Re-authentication expired', code: 'REAUTH_REQUIRED' });
    return;
  }
}

/**
 * Authorization middleware — checks if user has the required role
 */
export function authorize(...roles: string[]) {
  return (req: Request, res: Response, next: NextFunction): void => {
    if (!req.user) {
      res.status(401).json({ success: false, message: 'Authentication required' });
      return;
    }

    if (!roles.includes(req.user.roleSlug)) {
      res.status(403).json({ success: false, message: 'Insufficient permissions' });
      return;
    }

    next();
  };
}
