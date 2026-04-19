import { z } from 'zod';

export const createApiKeySchema = z.object({
  label: z.string().min(1).max(100),
  permissions: z.array(z.string()).min(1),
  expiresInDays: z.coerce.number().int().min(1).max(365).optional(),
});

export const registerNodeSchema = z.object({
  hostname: z.string().min(1),
  ipAddress: z.string().min(1),
  region: z.string().max(20).optional(),
  provider: z.string().optional(),
  role: z.string().optional(),
  version: z.string().optional(),
});

export const nodeHeartbeatSchema = z.object({
  cpuPercent: z.coerce.number().min(0).max(100).optional(),
  memoryPercent: z.coerce.number().min(0).max(100).optional(),
  diskPercent: z.coerce.number().min(0).max(100).optional(),
  uptimeSeconds: z.coerce.number().int().min(0).optional(),
  status: z.enum(['ONLINE', 'DEGRADED', 'OFFLINE', 'MAINTENANCE']).optional(),
});

export const logQuerySchema = z.object({
  level: z.enum(['DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL']).optional(),
  source: z.string().optional(),
  from: z.coerce.date().optional(),
  to: z.coerce.date().optional(),
  page: z.coerce.number().int().min(1).default(1),
  limit: z.coerce.number().int().min(1).max(100).default(50),
});
