import { z } from 'zod';

export const createUserSchema = z.object({
  email: z.string().email().optional(),
  phone: z.string().optional(),
  displayName: z.string().min(1).max(200),
  legalName: z.string().optional(),
  country: z.string().length(3).optional(),
  externalId: z.string().optional(),
  notes: z.string().optional(),
});

export const updateUserSchema = createUserSchema.partial().extend({
  riskScore: z.coerce.number().int().min(0).max(100).optional(),
});

export const freezeUserSchema = z.object({
  frozen: z.boolean(),
  reason: z.string().optional(),
});

export const blockUserSchema = z.object({
  blocked: z.boolean(),
  reason: z.string().optional(),
});

export const kycDecisionSchema = z.object({
  rejectionReason: z.string().optional(),
});

export const userListQuerySchema = z.object({
  search: z.string().optional(),
  kycStatus: z.enum(['NOT_STARTED', 'PENDING', 'IN_REVIEW', 'APPROVED', 'REJECTED', 'EXPIRED']).optional(),
  isBlocked: z.coerce.boolean().optional(),
  isFrozen: z.coerce.boolean().optional(),
  minVolume: z.coerce.number().min(0).optional(),
  page: z.coerce.number().int().min(1).default(1),
  limit: z.coerce.number().int().min(1).max(100).default(25),
  sortBy: z.enum(['createdAt', 'displayName', 'totalVolume', 'riskScore']).default('createdAt'),
  sortOrder: z.enum(['asc', 'desc']).default('desc'),
});
