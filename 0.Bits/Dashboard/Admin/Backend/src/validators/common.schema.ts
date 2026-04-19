import { z } from 'zod';
import type { Request } from 'express';

/**
 * Safely extract a route param as string (Express 5 may return string | string[]).
 */
export function param(req: Request, name: string): string {
  const val = req.params[name];
  return Array.isArray(val) ? val[0]! : val ?? '';
}

/** UUID path parameter */
export const idParamSchema = z.object({
  id: z.string().uuid('Invalid ID format'),
});

/** Standard pagination query */
export const paginationSchema = z.object({
  page: z.coerce.number().int().min(1).default(1),
  limit: z.coerce.number().int().min(1).max(100).default(25),
});

/** Date range filter */
export const dateRangeSchema = z.object({
  from: z.coerce.date().optional(),
  to: z.coerce.date().optional(),
});

/** Search + pagination */
export const searchPaginationSchema = paginationSchema.extend({
  search: z.string().optional(),
  sortBy: z.string().optional(),
  sortOrder: z.enum(['asc', 'desc']).default('desc'),
});
