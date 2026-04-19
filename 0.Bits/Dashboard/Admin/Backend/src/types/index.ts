import type { Role } from '@prisma/client';

/**
 * Decoded JWT payload attached to authenticated requests.
 */
export interface JwtPayload {
  sub: string;       // Admin UUID
  email: string;
  role: Role;
  sessionId: string;
  iat?: number;
  exp?: number;
}

/**
 * Extend Express Request to include authenticated admin context.
 */
declare global {
  namespace Express {
    interface Request {
      admin?: JwtPayload;
      correlationId?: string;
    }
  }
}

/**
 * Standardized sort direction.
 */
export type SortOrder = 'asc' | 'desc';

/**
 * Date range filter used across multiple query services.
 */
export interface DateRange {
  from?: Date;
  to?: Date;
}
