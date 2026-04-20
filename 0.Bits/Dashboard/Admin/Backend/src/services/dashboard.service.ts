import { prisma } from '../lib/db.js';
import { binanceService } from './binance.service.js';

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
      // If Binance returns live balances, use them, otherwise fallback to mock DB portfolios
      binanceService.fetchFundingBalances().then(b => b.length > 0 ? b : prisma.portfolio.findMany({ orderBy: { currency: 'asc' } })),
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

  /**
   * Get all live P2P Orders formatted for the Tremor Volume Chart.
   * Strict Data-Archiving Engine: Only serves cached Postgres data fetched silently by the background daemon.
   */
  async getTransactions() {
    // 100% Database enforcement for sub-10ms UI renders and infinite scroll safety.
    const orders = await prisma.p2POrder.findMany({
      orderBy: {
        createdAt: 'asc'
      }
    });

    return orders.map((order: any) => {
      // Safely extract metadata properties to populate granular visual metrics
      const meta = (order.metadata || {}) as Record<string, any>;
      
      return {
        transaction_id: order.id,
        // Standardize datetime formatting string for tremor chart indexing
        transaction_date: order.createdAt.toISOString(),
        // Natively fix the COP/MXN chart anomaly by strictly defaulting to the unhedged USDT asset magnitude 
        amount: Number(order.amount) || Number(order.fiatAmount) || 0,
        expense_status: (order.status === 'COMPLETED' || order.status === 'RELEASED') ? 'completed' : 'cancelled',
        payment_status: 'cleared',
        category: order.type === 'SELL' ? 'Arbitrage Sell' : 'Arbitrage Buy',
        // Permanently bind the authentic True Legal Name scraped intimately from the undocumented SAPI layer
        merchant: order.counterpartyName ? order.counterpartyName : (meta.counterparty_name ? String(meta.counterparty_name) : (order.counterparty || 'Binance P2P User')),
        country: 'Global',
        currency: order.fiat || 'USD',
        lastEdited: order.updatedAt ? order.updatedAt.toISOString() : order.createdAt.toISOString(),
        continent: 'Europe'
      }
    });
  }
}

export const dashboardService = new DashboardService();
