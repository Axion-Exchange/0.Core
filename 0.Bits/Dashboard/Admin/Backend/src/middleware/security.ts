import type { Request, Response, NextFunction } from 'express';
import { createLogger } from '../lib/logger.js';

const log = createLogger('security');

/**
 * OWASP API Security Middleware
 * 
 * Doc ref: §API Security and External Integrations (citations 36, 54)
 * "BOLA is the most common institutional vulnerability where a user can access
 *  another user's data by manipulating an ID in the request."
 * "All API traffic must use TLS 1.2 or 1.3 with valid SSL certificates,
 *  and HSTS must be enabled to force browser connections to remain encrypted."
 */

/**
 * Input sanitization middleware.
 * Strips dangerous characters from request body/query to prevent:
 * - NoSQL injection ($where, $gt, etc.)
 * - Prototype pollution (__proto__, constructor)
 * - Path traversal (../)
 */
export function sanitizeInput(req: Request, _res: Response, next: NextFunction): void {
  const DANGEROUS_KEYS = ['$where', '$gt', '$lt', '$gte', '$lte', '$ne', '$in', '$nin', '$regex',
    '__proto__', 'constructor', 'prototype'];

  function sanitize(obj: any, depth = 0): any {
    if (depth > 10) return obj; // Prevent infinite recursion
    if (obj === null || obj === undefined) return obj;
    if (typeof obj !== 'object') return obj;

    if (Array.isArray(obj)) {
      return obj.map(item => sanitize(item, depth + 1));
    }

    const cleaned: Record<string, any> = {};
    for (const [key, value] of Object.entries(obj)) {
      // Block dangerous keys
      if (DANGEROUS_KEYS.includes(key)) {
        log.warn(`[Security] Blocked dangerous key "${key}" in request`, {
          path: req.path,
          method: req.method,
        });
        continue;
      }

      // Block path traversal in string values
      if (typeof value === 'string' && value.includes('../')) {
        log.warn(`[Security] Blocked path traversal in "${key}"`, { path: req.path });
        cleaned[key] = value.replace(/\.\.\//g, '');
        continue;
      }

      cleaned[key] = sanitize(value, depth + 1);
    }
    return cleaned;
  }

  if (req.body && typeof req.body === 'object') {
    req.body = sanitize(req.body);
  }
  // Note: req.query is read-only in Express 5+ (getter). 
  // Query params are already URL-decoded by Express and don't need sanitization
  // for NoSQL injection since we use Prisma (parameterized queries).

  next();
}

/**
 * Security response headers beyond what Helmet provides.
 * Adds defense-in-depth headers recommended by OWASP.
 */
export function securityHeaders(_req: Request, res: Response, next: NextFunction): void {
  // Prevent caching of API responses containing sensitive data
  res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate, proxy-revalidate');
  res.setHeader('Pragma', 'no-cache');
  res.setHeader('Expires', '0');

  // Prevent content type sniffing (Helmet does this too, belt-and-suspenders)
  res.setHeader('X-Content-Type-Options', 'nosniff');

  // Disable browser-side features we don't use
  res.setHeader('Permissions-Policy', 'camera=(), microphone=(), geolocation=(), payment=()');

  // Referrer policy — don't leak full URL to external domains
  res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');

  next();
}

/**
 * Request payload size enforcement.
 * Blocks oversized payloads that could be used for:
 * - Memory exhaustion attacks
 * - ReDoS via large regex-matched strings
 */
export function enforcePayloadLimits(req: Request, res: Response, next: NextFunction): void {
  const contentLength = parseInt(req.headers['content-length'] || '0', 10);

  // Block absurdly large payloads (> 5MB)
  if (contentLength > 5 * 1024 * 1024) {
    log.warn(`[Security] Blocked oversized payload: ${contentLength} bytes`, { path: req.path });
    res.status(413).json({
      success: false,
      error: { code: 'PAYLOAD_TOO_LARGE', message: 'Request body exceeds maximum size' },
    });
    return;
  }

  next();
}
