import { prisma } from '../lib/db.js';
import { sha256, generateSecureToken } from '../lib/crypto.js';
import { checkDatabaseHealth } from '../lib/db.js';
import type { LogLevel, Prisma } from '@prisma/client';

export class OperationsService {
  // ── Health ─────────────────────────────────────────────

  async getSystemHealth() {
    const dbHealthy = await checkDatabaseHealth();
    const uptime = process.uptime();

    const recentChecks = await prisma.healthCheck.findMany({
      orderBy: { checkedAt: 'desc' },
      take: 10,
    });

    return {
      status: dbHealthy ? 'operational' : 'degraded',
      uptime: Math.floor(uptime),
      database: dbHealthy ? 'connected' : 'disconnected',
      timestamp: new Date().toISOString(),
      recentChecks,
      memory: process.memoryUsage(),
    };
  }

  // ── API Keys ───────────────────────────────────────────

  async listApiKeys() {
    return prisma.apiKey.findMany({
      where: { isRevoked: false },
      orderBy: { createdAt: 'desc' },
      select: {
        id: true, label: true, keyPrefix: true, permissions: true,
        lastUsedAt: true, expiresAt: true, createdAt: true,
      },
    });
  }

  async createApiKey(data: { label: string; permissions: string[]; expiresInDays?: number; createdById: string }) {
    const rawKey = `zbk_${generateSecureToken(32)}`;
    const keyPrefix = rawKey.slice(0, 8);
    const keyHash = sha256(rawKey);

    const expiresAt = data.expiresInDays
      ? new Date(Date.now() + data.expiresInDays * 24 * 60 * 60 * 1000)
      : null;

    const apiKey = await prisma.apiKey.create({
      data: {
        label: data.label,
        keyPrefix,
        keyHash,
        permissions: data.permissions,
        expiresAt,
        createdById: data.createdById,
      },
    });

    // Return the raw key ONLY on creation — it's never stored
    return { ...apiKey, rawKey };
  }

  async revokeApiKey(id: string) {
    return prisma.apiKey.update({
      where: { id },
      data: { isRevoked: true, revokedAt: new Date() },
    });
  }

  // ── Nodes ──────────────────────────────────────────────

  async listNodes() {
    return prisma.node.findMany({
      orderBy: [{ status: 'asc' }, { hostname: 'asc' }],
    });
  }

  async registerNode(data: { hostname: string; ipAddress: string; region?: string; provider?: string; role?: string; version?: string }) {
    return prisma.node.upsert({
      where: { hostname: data.hostname },
      create: { ...data, lastHeartbeatAt: new Date() } as any,
      update: { ...data, lastHeartbeatAt: new Date(), status: 'ONLINE' } as any,
    });
  }

  async nodeHeartbeat(id: string, data: Record<string, unknown>) {
    return prisma.node.update({
      where: { id },
      data: { ...data, lastHeartbeatAt: new Date() } as any,
    });
  }

  // ── Logs ───────────────────────────────────────────────

  async listLogs(filters: { level?: LogLevel; source?: string; from?: Date; to?: Date; page: number; limit: number }) {
    const where: Prisma.SystemLogWhereInput = {};

    if (filters.level) where.level = filters.level;
    if (filters.source) where.source = filters.source;
    if (filters.from || filters.to) {
      where.createdAt = {};
      if (filters.from) where.createdAt.gte = filters.from;
      if (filters.to) where.createdAt.lte = filters.to;
    }

    const [data, total] = await Promise.all([
      prisma.systemLog.findMany({
        where,
        orderBy: { createdAt: 'desc' },
        skip: (filters.page - 1) * filters.limit,
        take: filters.limit,
      }),
      prisma.systemLog.count({ where }),
    ]);

    return { data, total, page: filters.page, limit: filters.limit };
  }

  /**
   * Write a structured log entry to the database.
   */
  async writeLog(level: LogLevel, source: string, message: string, metadata?: Record<string, unknown>) {
    return prisma.systemLog.create({
      data: { level, source, message, metadata: (metadata ?? undefined) as any },
    });
  }
}

export const operationsService = new OperationsService();
