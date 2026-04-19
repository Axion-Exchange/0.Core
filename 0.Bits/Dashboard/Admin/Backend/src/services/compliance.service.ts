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
}

export const complianceService = new ComplianceService();
