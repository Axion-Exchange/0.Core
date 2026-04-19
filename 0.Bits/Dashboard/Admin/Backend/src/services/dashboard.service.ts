import { prisma } from '../lib/db.js';

export class DashboardService {
  /**
   * Aggregated metrics for the home dashboard.
   */
  async getSummary() {
    const now = new Date();
    const last24h = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    const last7d = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);

    const [
      totalUsers,
      activeUsers,
      blockedUsers,
      pendingKyc,
      pendingKyb,
      totalOrders,
      activeOrders,
      ordersLast24h,
      totalAds,
      activeAds,
      activeDisputes,
      totalVolume,
      volumeLast24h,
      portfolios,
      openTasks,
      upcomingMeetings,
    ] = await Promise.all([
      prisma.user.count(),
      prisma.user.count({ where: { isBlocked: false, isFrozen: false } }),
      prisma.user.count({ where: { isBlocked: true } }),
      prisma.user.count({ where: { kycStatus: 'PENDING' } }),
      prisma.user.count({ where: { kybStatus: 'PENDING' } }),
      prisma.p2POrder.count(),
      prisma.p2POrder.count({ where: { status: { in: ['PENDING_FIAT', 'FIAT_RECEIVED', 'PENDING_RELEASE'] } } }),
      prisma.p2POrder.count({ where: { createdAt: { gte: last24h } } }),
      prisma.p2PAdvertisement.count(),
      prisma.p2PAdvertisement.count({ where: { status: 'ACTIVE' } }),
      prisma.p2PDispute.count({ where: { status: { in: ['OPEN', 'UNDER_REVIEW', 'EVIDENCE_REQUESTED'] } } }),
      prisma.transaction.aggregate({ _sum: { fiatAmount: true }, where: { status: 'COMPLETED' } }),
      prisma.transaction.aggregate({ _sum: { fiatAmount: true }, where: { status: 'COMPLETED', createdAt: { gte: last24h } } }),
      prisma.portfolio.findMany({ orderBy: { currency: 'asc' } }),
      prisma.task.count({ where: { status: { in: ['TODO', 'IN_PROGRESS'] } } }),
      prisma.meeting.count({ where: { startsAt: { gte: now }, status: 'SCHEDULED' } }),
    ]);

    return {
      users: { total: totalUsers, active: activeUsers, blocked: blockedUsers, pendingKyc, pendingKyb },
      orders: { total: totalOrders, active: activeOrders, last24h: ordersLast24h },
      ads: { total: totalAds, active: activeAds },
      disputes: { active: activeDisputes },
      volume: { total: Number(totalVolume._sum.fiatAmount ?? 0), last24h: Number(volumeLast24h._sum.fiatAmount ?? 0) },
      portfolios,
      tasks: { open: openTasks },
      meetings: { upcoming: upcomingMeetings },
      timestamp: now.toISOString(),
    };
  }
}

export const dashboardService = new DashboardService();
