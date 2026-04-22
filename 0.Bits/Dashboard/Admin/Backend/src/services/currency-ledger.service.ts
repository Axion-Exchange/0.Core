/**
 * Currency Ledger Service
 * 
 * Provides per-currency (EUR / COP / MXN) aggregated views for the
 * institutional treasury dashboard tabs. Reads exclusively from the
 * PostgreSQL database — zero external API calls.
 * 
 * Data sources:
 *   - fiat_ledgers  → live bank balance (polled every 30s by fiat-sync.worker)
 *   - p2p_orders    → P2P order history (polled every 30s by binance-sync.worker)
 *   - transactions  → Januar SEPA transactions (polled every 30s by fiat-sync.worker)
 */
import { prisma } from '../lib/db.js';
import { createLogger } from '../lib/logger.js';

const log = createLogger('currency-ledger');

// Map fiat codes to their bank source for fiat_ledgers
const FIAT_SOURCE_MAP: Record<string, string> = {
  EUR: 'januar',
  COP: 'facilitapay',
  MXN: 'facilitapay',
};

const FIAT_SYMBOLS: Record<string, string> = {
  EUR: '€',
  COP: '$',
  MXN: '$',
};

export class CurrencyLedgerService {

  /**
   * Balance summary for the top card (Balance / Available / Locked / Pending)
   */
  async getBalanceSummary(fiat: string) {
    const source = FIAT_SOURCE_MAP[fiat] || 'unknown';
    const symbol = FIAT_SYMBOLS[fiat] || '$';

    // 1. Live bank balance from fiat_ledgers
    const ledger = await prisma.fiatLedger.findFirst({
      where: { currency: fiat, source },
    });
    const bankBalance = ledger ? Number(ledger.balance) : 0;

    // 2. Locked in active P2P orders (PENDING_FIAT, FIAT_RECEIVED, PENDING_RELEASE)
    const lockedOrders = await prisma.p2POrder.aggregate({
      where: {
        fiat,
        status: { in: ['PENDING_FIAT', 'FIAT_RECEIVED', 'PENDING_RELEASE'] },
      },
      _sum: { fiatAmount: true },
      _count: true,
    });
    const lockedAmount = Number(lockedOrders._sum.fiatAmount || 0);

    // 3. Pending (APPEALING, DISPUTE_RESOLVED — not yet settled)
    const pendingOrders = await prisma.p2POrder.aggregate({
      where: {
        fiat,
        status: { in: ['APPEALING', 'DISPUTE_RESOLVED'] },
      },
      _sum: { fiatAmount: true },
    });
    const pendingAmount = Number(pendingOrders._sum.fiatAmount || 0);

    // 4. Total completed volume (all-time)
    const completedVolume = await prisma.p2POrder.aggregate({
      where: { fiat, status: 'COMPLETED' },
      _sum: { fiatAmount: true },
      _count: true,
    });
    const totalVolume = Number(completedVolume._sum.fiatAmount || 0);

    // Available = bank balance - locked
    const available = Math.max(bankBalance - lockedAmount, 0);

    return {
      fiat,
      symbol,
      totalBalance: bankBalance,
      available,
      locked: lockedAmount,
      pending: pendingAmount,
      totalCompletedVolume: totalVolume,
      totalCompletedOrders: completedVolume._count,
      activeOrders: lockedOrders._count,
      lastSyncAt: ledger?.lastSyncAt || null,
    };
  }

  /**
   * Daily metrics for the chart cards.
   * Returns data in the OverviewData shape the ChartCard components expect.
   * 
   * Metrics per day:
   *   - "New counterparties" → distinct counterpartyNames that day
   *   - "Payments completed" → sum of completed fiatAmount that day  
   *   - "Active orders" → count of orders created that day
   */
  async getDailyMetrics(fiat: string, from?: Date, to?: Date) {
    const dateFrom = from || new Date(Date.now() - 365 * 24 * 60 * 60 * 1000);
    const dateTo = to || new Date();

    // Get all orders in range for this fiat
    const orders = await prisma.p2POrder.findMany({
      where: {
        fiat,
        createdAt: { gte: dateFrom, lte: dateTo },
      },
      select: {
        createdAt: true,
        status: true,
        fiatAmount: true,
        counterpartyName: true,
        counterparty: true,
      },
      orderBy: { createdAt: 'asc' },
    });

    // Group by day
    const dayMap = new Map<string, {
      date: string;
      completedVolume: number;
      orderCount: number;
      counterparties: Set<string>;
    }>();

    for (const order of orders) {
      const dayKey = order.createdAt.toISOString().slice(0, 10) + 'T00:00:00';
      
      if (!dayMap.has(dayKey)) {
        dayMap.set(dayKey, {
          date: dayKey,
          completedVolume: 0,
          orderCount: 0,
          counterparties: new Set(),
        });
      }

      const day = dayMap.get(dayKey)!;
      day.orderCount++;

      if (order.status === 'COMPLETED') {
        day.completedVolume += Number(order.fiatAmount);
      }

      const name = order.counterpartyName || order.counterparty || 'Unknown';
      day.counterparties.add(name);
    }

    // Convert to OverviewData format
    const overviews = Array.from(dayMap.values()).map(day => ({
      date: day.date,
      "Rows written": day.orderCount,          // Used internally by ChartCard
      "Rows read": day.counterparties.size * 100, // Scale for visual
      "Queries": day.orderCount,
      "Payments completed": day.completedVolume,
      "New counterparties": day.counterparties.size,
      "Active orders": day.orderCount,
      "Logins": day.orderCount,                 // Fallback for existing template
      "Sign ups": day.counterparties.size,       // Fallback for existing template
      "Sign outs": 0,
      "Support calls": 0,
    }));

    return overviews;
  }

  /**
   * P2P orders table in the Usage[] format the DataTable expects.
   */
  async getOrdersTable(fiat: string, limit: number = 50, page: number = 1) {
    const skip = (page - 1) * limit;

    // Only show Pending (active open orders) and Completed — no cancelled/expired
    const statusFilter = {
      in: ['PENDING_FIAT', 'FIAT_RECEIVED', 'PENDING_RELEASE', 'RELEASED', 'COMPLETED', 'APPEALING', 'DISPUTE_RESOLVED'] as any[],
    };

    const [orders, total] = await Promise.all([
      prisma.p2POrder.findMany({
        where: { fiat, status: statusFilter },
        orderBy: { createdAt: 'desc' },
        take: limit,
        skip,
        select: {
          id: true,
          externalOrderId: true,
          counterpartyName: true,
          counterparty: true,
          status: true,
          type: true,
          fiatAmount: true,
          amount: true,
          asset: true,
          price: true,
          paymentMethod: true,
          createdAt: true,
          completedAt: true,
        },
      }),
      prisma.p2POrder.count({ where: { fiat, status: statusFilter } }),
    ]);

    // Map to Usage[] format the DataTable expects
    // Pending = open order on Binance (awaiting fiat/release)
    // Completed = trade fully settled
    const usage = orders.map(order => {
      const isCompleted = order.status === 'COMPLETED' || order.status === 'RELEASED';
      const displayStatus = isCompleted ? 'Completed' : 'Pending';

      return {
        transactionNumber: order.externalOrderId || order.id.slice(0, 13),
        owner: order.counterpartyName || order.counterparty || 'Unknown',
        status: displayStatus,
        amount: Number(order.fiatAmount),
        date: order.createdAt.toLocaleDateString('en-GB', {
          day: '2-digit', month: '2-digit', year: 'numeric',
          hour: '2-digit', minute: '2-digit',
        }),
        // Extra fields for rich display (won't break existing columns)
        type: order.type,
        asset: order.asset,
        cryptoAmount: Number(order.amount),
        price: Number(order.price),
        paymentMethod: order.paymentMethod,
      };
    });

    return { data: usage, total, page, limit };
  }
}

export const currencyLedgerService = new CurrencyLedgerService();
