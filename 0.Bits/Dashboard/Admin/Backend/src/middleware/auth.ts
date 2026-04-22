import type { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';
import { config } from '../config/index.js';
import { prisma } from '../lib/db.js';
import { sendError } from '../lib/response.js';
import { isTokenBlacklisted, isAdminTokenRevokedAfter } from '../lib/redis.js';
import type { JwtPayload } from '../types/index.js';
import type { Role } from '@prisma/client';

/**
 * Middleware: Verify JWT bearer token, check blacklist, and attach admin context.
 * 
 * Doc ref: §Session Revocation and JWT Blacklisting (citation 15)
 * "Institutional grade systems implement a token blacklist in Redis.
 *  When an admin logs out or a suspicious session is detected,
 *  the token's jti is stored in Redis with a TTL matching the token's remaining validity."
 */
export function requireAuth(req: Request, res: Response, next: NextFunction): void {
  const authHeader = req.headers.authorization;

  if (!authHeader?.startsWith('Bearer ')) {
    sendError(res, 401, 'AUTH_MISSING', 'Authorization header required (Bearer <token>)');
    return;
  }

  const token = authHeader.slice(7);

  try {
    const decoded = jwt.verify(token, config.JWT_SECRET) as JwtPayload;

    // ── Redis Blacklist Check ──────────────────────────────────────────
    // Check both individual token revocation (jti) and admin-wide revocation
    const jti = (decoded as any).jti || decoded.sessionId;
    const checkBlacklist = async () => {
      // 1. Check if this specific token was blacklisted (logout)
      if (await isTokenBlacklisted(jti)) {
        sendError(res, 401, 'AUTH_REVOKED', 'Token has been revoked — please re-authenticate');
        return;
      }

      // 2. Check if all tokens for this admin were revoked (password change / compromise)
      const iat = (decoded as any).iat || 0;
      if (await isAdminTokenRevokedAfter(decoded.sub, iat)) {
        sendError(res, 401, 'AUTH_REVOKED', 'All sessions revoked — please re-authenticate');
        return;
      }

      req.admin = decoded;
      next();
    };

    checkBlacklist().catch(() => {
      // Redis unavailable — fail open to preserve availability
      // (degraded security, but service stays up)
      req.admin = decoded;
      next();
    });

  } catch (err: unknown) {
    const message = err instanceof jwt.TokenExpiredError
      ? 'Token expired — please re-authenticate'
      : 'Invalid or malformed token';
    sendError(res, 401, 'AUTH_INVALID', message);
  }
}

/**
 * Middleware: Require specific admin roles (RBAC guard).
 * Must be used AFTER requireAuth.
 */
export function requireRole(...allowedRoles: Role[]) {
  return (req: Request, res: Response, next: NextFunction): void => {
    if (!req.admin) {
      sendError(res, 401, 'AUTH_MISSING', 'Authentication required');
      return;
    }

    if (!allowedRoles.includes(req.admin.role)) {
      sendError(res, 403, 'FORBIDDEN', `Insufficient permissions. Required: ${allowedRoles.join(' | ')}`);
      return;
    }

    next();
  };
}

/**
 * Optional auth: attach admin context if token present, but don't block.
 */
export function optionalAuth(req: Request, _res: Response, next: NextFunction): void {
  const authHeader = req.headers.authorization;

  if (authHeader?.startsWith('Bearer ')) {
    try {
      const token = authHeader.slice(7);
      const decoded = jwt.verify(token, config.JWT_SECRET) as JwtPayload;
      req.admin = decoded;
    } catch {
      // Token invalid — proceed without auth context
    }
  }

  next();
}
