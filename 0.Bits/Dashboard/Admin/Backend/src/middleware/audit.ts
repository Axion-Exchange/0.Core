import { sinkAuditToBigQuery } from "../services/audit-bigquery.service.js";
import type { Request, Response, NextFunction } from 'express';
import { prisma } from '../lib/db.js';
import { createLogger } from '../lib/logger.js';

const log = createLogger('audit');

/**
 * Middleware: Automatically log all mutating requests to the audit trail.
 * Only logs POST, PUT, PATCH, DELETE — skips GET/HEAD/OPTIONS.
 * Must be used AFTER requireAuth so req.admin is available.
 */
export function auditLog(req: Request, res: Response, next: NextFunction): void {
  const method = req.method.toUpperCase();

  // Skip non-mutating methods
  if (['GET', 'HEAD', 'OPTIONS'].includes(method)) {
    next();
    return;
  }

  // Capture timing
  const startTime = Date.now();

  // Intercept response to capture status code
  const originalJson = res.json.bind(res);
  res.json = function (body: unknown) {
    const duration = Date.now() - startTime;

    // Fire-and-forget audit log write
    if (req.admin) {
      const action = deriveAction(method, req.path);
      const resource = deriveResource(req.path);

      // Write to PostgreSQL (local DB)
      prisma.auditLog.create({
        data: {
          adminId: req.admin.sub,
          action,
          resource,
          resourceId: extractResourceId(req.params as Record<string, string>),
          method,
          path: req.path,
          ipAddress: (req.ip ?? req.socket.remoteAddress ?? 'unknown'),
          userAgent: req.headers['user-agent'] ?? null,
          requestBody: (sanitizeBody(req.body) ?? undefined) as any,
          responseCode: res.statusCode,
          duration,
          correlationId: req.correlationId ?? null,
        },
      }).catch((err: unknown) => {
        log.error('Failed to write audit log', { error: (err as Error).message });
      });

      // Immutable audit log → BigQuery (tamper-proof, append-only)
      sinkAuditToBigQuery({
        id: crypto.randomUUID(),
        adminId: req.admin.sub,
        action,
        resource,
        resourceId: extractResourceId(req.params as Record<string, string>),
        method,
        path: req.path,
        ipAddress: (req.ip ?? req.socket.remoteAddress ?? 'unknown'),
        userAgent: req.headers['user-agent'] ?? undefined,
        requestBody: sanitizeBody(req.body) ?? undefined,
        responseCode: res.statusCode,
        duration,
        correlationId: req.correlationId ?? undefined,
      });
    }

    return originalJson(body);
  };

  next();
}

/**
 * Derive a human-readable action string from HTTP method and path.
 * e.g., "POST /api/v1/p2p/ads" → "p2p.ads.create"
 */
function deriveAction(method: string, path: string): string {
  const segments = path.replace('/api/v1/', '').split('/').filter(Boolean);
  const domain = segments[0] ?? 'unknown';
  const resource = segments[1] ?? domain;

  const verbMap: Record<string, string> = {
    POST: 'create',
    PUT: 'update',
    PATCH: 'update',
    DELETE: 'delete',
  };

  const verb = verbMap[method] ?? method.toLowerCase();
  return `${domain}.${resource}.${verb}`;
}

function deriveResource(path: string): string {
  const segments = path.replace('/api/v1/', '').split('/').filter(Boolean);
  return segments[0] ?? 'unknown';
}

function extractResourceId(params: Record<string, string>): string | null {
  return params['id'] ?? null;
}

/**
 * Remove sensitive fields from request body before persisting.
 */
function sanitizeBody(body: unknown): Record<string, unknown> | null {
  if (!body || typeof body !== 'object') return null;

  const sanitized = { ...body as Record<string, unknown> };
  const sensitiveKeys = ['password', 'passwordHash', 'apiKey', 'apiSecret', 'secret', 'token', 'passphrase'];

  for (const key of sensitiveKeys) {
    if (key in sanitized) {
      sanitized[key] = '[REDACTED]';
    }
  }

  return sanitized;
}
