import type { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';
import { config } from '../config/index.js';
import { prisma } from '../lib/db.js';
import { sendError } from '../lib/response.js';
import type { JwtPayload } from '../types/index.js';
import type { Role } from '@prisma/client';

/**
 * Middleware: Verify JWT bearer token and attach admin context.
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
    req.admin = decoded;
    next();
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
