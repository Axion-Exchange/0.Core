import type { Request, Response, NextFunction } from 'express';
import { ZodSchema, ZodError } from 'zod';
import { sendError } from '../lib/response.js';

/**
 * Validate request body against a Zod schema.
 */
export function validateBody(schema: ZodSchema) {
  return (req: Request, res: Response, next: NextFunction): void => {
    const result = schema.safeParse(req.body);
    if (!result.success) {
      const details = formatZodError(result.error);
      sendError(res, 400, 'VALIDATION_ERROR', 'Request body validation failed', details);
      return;
    }
    req.body = result.data;
    next();
  };
}

/**
 * Validate request query parameters against a Zod schema.
 */
export function validateQuery(schema: ZodSchema) {
  return (req: Request, res: Response, next: NextFunction): void => {
    const result = schema.safeParse(req.query);
    if (!result.success) {
      const details = formatZodError(result.error);
      sendError(res, 400, 'VALIDATION_ERROR', 'Query parameter validation failed', details);
      return;
    }
    // Attach validated query — use Object.defineProperty to bypass getter-only
    try {
      Object.defineProperty(req, 'query', { value: result.data, writable: true });
    } catch {
      // Fallback: store on req directly 
      (req as any).validatedQuery = result.data;
    }
    next();
  };
}

/**
 * Validate request path parameters against a Zod schema.
 */
export function validateParams(schema: ZodSchema) {
  return (req: Request, res: Response, next: NextFunction): void => {
    const result = schema.safeParse(req.params);
    if (!result.success) {
      const details = formatZodError(result.error);
      sendError(res, 400, 'VALIDATION_ERROR', 'Path parameter validation failed', details);
      return;
    }
    next();
  };
}

function formatZodError(error: ZodError): Array<{ field: string; message: string }> {
  return error.issues.map((issue) => ({
    field: issue.path.join('.'),
    message: issue.message,
  }));
}
