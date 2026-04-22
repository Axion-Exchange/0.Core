import { prisma } from '../lib/db.js';

export class ComplianceService {
  async getAuditTrail(filters: { adminId?: string; action?: string; resource?: string; from?: Date; to?: Date; page: number; limit: number }) {
    const where: Record<string, unknown> = {};

    if (filters.adminId) where['adminId'] = filters.adminId;
    if (filters.action) where['action'] = { contains: filters.action };
    if (filters.resource) where['resource'] = filters.resource;
    if (filters.from || filters.to) {
      where['createdAt'] = {};
      if (filters.from) (where['createdAt'] as any).gte = filters.from;
      if (filters.to) (where['createdAt'] as any).lte = filters.to;
    }

    const [data, total] = await Promise.all([
      prisma.auditLog.findMany({
        where: where as any,
        include: { admin: { select: { displayName: true, email: true } } },
        orderBy: { createdAt: 'desc' },
        skip: (filters.page - 1) * filters.limit,
        take: filters.limit,
      }),
      prisma.auditLog.count({ where: where as any }),
    ]);

    return { data, total, page: filters.page, limit: filters.limit };
  }

  async getSummary() {
    const [totalUsers, pendingKyc, totalOrders, totalVolume, activeDisputes, recentAuditActions] = await Promise.all([
      prisma.user.count(),
      prisma.user.count({ where: { kycStatus: 'PENDING' } }),
      prisma.p2POrder.count(),
      prisma.transaction.aggregate({ _sum: { fiatAmount: true }, where: { status: 'COMPLETED' } }),
      prisma.p2PDispute.count({ where: { status: { in: ['OPEN', 'UNDER_REVIEW', 'EVIDENCE_REQUESTED'] } } }),
      prisma.auditLog.count({ where: { createdAt: { gte: new Date(Date.now() - 24 * 60 * 60 * 1000) } } }),
    ]);

    return {
      totalUsers,
      pendingKyc,
      totalOrders,
      totalVolume: Number(totalVolume._sum.fiatAmount ?? 0),
      activeDisputes,
      recentAuditActions,
    };
  }

  /**
   * Daily P&L breakdown for the last N days.
   */
  async getDailyPnl(days: number = 14) {
    const since = new Date(Date.now() - days * 24 * 60 * 60 * 1000);
    const transactions = await prisma.transaction.findMany({
      where: { status: 'COMPLETED', createdAt: { gte: since } },
      select: { createdAt: true, fiatAmount: true, fee: true, type: true, currency: true },
      orderBy: { createdAt: 'asc' },
    });

    // Group by day
    const dailyMap = new Map<string, { date: string; volume: number; fees: number; count: number }>();
    for (const tx of transactions) {
      const day = tx.createdAt.toISOString().slice(0, 10);
      const existing = dailyMap.get(day) ?? { date: day, volume: 0, fees: 0, count: 0 };
      existing.volume += Number(tx.fiatAmount ?? 0);
      existing.fees += Number(tx.fee ?? 0);
      existing.count += 1;
      dailyMap.set(day, existing);
    }

    return Array.from(dailyMap.values());
  }

  /**
   * Top counterparties by volume.
   */
  async getCounterpartyMatrix(limit: number = 20) {
    const orders = await prisma.p2POrder.groupBy({
      by: ['counterparty'],
      _sum: { fiatAmount: true, amount: true },
      _count: { id: true },
      orderBy: { _sum: { fiatAmount: 'desc' } },
      take: limit,
    });

    return orders.map((row: any) => ({
      counterparty: row.counterparty,
      totalFiatVolume: Number(row._sum.fiatAmount ?? 0),
      totalCryptoVolume: Number(row._sum.amount ?? 0),
      orderCount: row._count.id,
    }));
  }

  /**
   * Export audit trail as CSV-ready data.
   */
  async exportAuditCsv(filters: { from?: Date; to?: Date }) {
    const where: Record<string, unknown> = {};
    if (filters.from || filters.to) {
      where['createdAt'] = {};
      if (filters.from) (where['createdAt'] as any).gte = filters.from;
      if (filters.to) (where['createdAt'] as any).lte = filters.to;
    }

    const logs = await prisma.auditLog.findMany({
      where: where as any,
      include: { admin: { select: { displayName: true, email: true } } },
      orderBy: { createdAt: 'desc' },
      take: 10000, // Safety cap
    });

    return logs.map((log: any) => ({
      timestamp: log.createdAt.toISOString(),
      admin: log.admin?.displayName ?? log.adminId,
      action: log.action,
      resource: log.resource,
      resourceId: log.resourceId,
      method: log.method,
      path: log.path,
      responseCode: log.responseCode,
      duration: log.duration,
      ip: log.ipAddress,
    }));
  }
}

export const complianceService = new ComplianceService();
