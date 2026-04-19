import { z } from 'zod';

export const portfolioQuerySchema = z.object({
  currency: z.string().max(10).optional(),
});

export const balanceHistorySchema = z.object({
  currency: z.string().max(10),
  days: z.coerce.number().int().min(1).max(365).default(30),
});

export const transactionQuerySchema = z.object({
  type: z.enum(['BUY', 'SELL', 'TRANSFER_IN', 'TRANSFER_OUT', 'CONVERSION', 'FEE', 'ADJUSTMENT']).optional(),
  status: z.enum(['PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'CANCELLED', 'REVERSED']).optional(),
  asset: z.string().max(10).optional(),
  source: z.string().optional(),
  from: z.coerce.date().optional(),
  to: z.coerce.date().optional(),
  page: z.coerce.number().int().min(1).default(1),
  limit: z.coerce.number().int().min(1).max(100).default(25),
});
