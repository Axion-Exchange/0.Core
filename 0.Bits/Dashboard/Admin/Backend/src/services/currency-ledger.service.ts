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
   * Balance summary for the top card.
   * Available = Live bank balance (from latest BalanceLedger snapshot)
   * Pending   = Active P2P escrow orders (from latest BalanceLedger snapshot)
   */
  async getBalanceSummary(fiat: string) {
    const source = FIAT_SOURCE_MAP[fiat] || 'unknown';
    const symbol = FIAT_SYMBOLS[fiat] || '$';

    // 1. Get latest snapshot from append-only balance_ledger
    const latestSnapshot = await prisma.balanceLedger.findFirst({
      where: { source, currency: fiat },
      orderBy: { snapshotAt: 'desc' },
    });

    const available = latestSnapshot ? Number(latestSnapshot.available) : 0;
    const pending = latestSnapshot ? Number(latestSnapshot.pending) : 0;

    // 2. Fallback: if no snapshot yet, read from legacy fiat_ledgers
    let bankBalance = available;
    if (!latestSnapshot) {
      const ledger = await prisma.fiatLedger.findFirst({
        where: { currency: fiat, source },
      });
      bankBalance = ledger ? Number(ledger.balance) : 0;

      // Calculate pending from live P2P orders
      const escrowAgg = await prisma.p2POrder.aggregate({
        where: {
          fiat,
          status: { in: ['PENDING_FIAT', 'FIAT_RECEIVED', 'PENDING_RELEASE', 'APPEALING'] },
        },
        _sum: { fiatAmount: true },
      });
      const escrowPending = Number(escrowAgg._sum.fiatAmount || 0);

      return {
        fiat, symbol,
        available: bankBalance,
        pending: escrowPending,
        totalBalance: bankBalance + escrowPending,
        lastSnapshotAt: null,
      };
    }

    // 3. Total completed volume (all-time)
    const completedVolume = await prisma.p2POrder.aggregate({
      where: { fiat, status: 'COMPLETED' },
      _sum: { fiatAmount: true },
      _count: true,
    });
    const totalVolume = Number(completedVolume._sum.fiatAmount || 0);

    return {
      fiat,
      symbol,
      available,
      pending,
      totalBalance: available + pending,
      totalCompletedVolume: totalVolume,
      totalCompletedOrders: completedVolume._count,
      lastSnapshotAt: latestSnapshot.snapshotAt,
    };
  }

  /**
   * Daily metrics for the chart cards.
   * Returns data in the OverviewData shape the ChartCard components expect.
   * 
   * Metrics per day:
   *   - "New counterparties" → counterparties trading for the FIRST TIME ever on that day
   *   - "Order volume" → sum of completed fiatAmount that day  
   *   - "Active orders" → count of orders created that day
   */
  async getDailyMetrics(fiat: string, from?: Date, to?: Date) {
    const dateFrom = from || new Date(Date.now() - 365 * 24 * 60 * 60 * 1000);
    const dateTo = to || new Date();

    // 1. Get ALL counterparties who traded BEFORE the date range
    //    so we can identify truly "new" ones within the range
    const historicalCounterparties = await prisma.p2POrder.findMany({
      where: {
        fiat,
        createdAt: { lt: dateFrom },
      },
      select: {
        counterpartyName: true,
        counterparty: true,
      },
      distinct: ['counterpartyName', 'counterparty'],
    });

    const seenBefore = new Set<string>();
    for (const cp of historicalCounterparties) {
      const name = cp.counterpartyName || cp.counterparty || 'Unknown';
      seenBefore.add(name);
    }

    // 2. Get all orders in range for this fiat
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

    // 3. Group by day, tracking truly NEW counterparties
    const dayMap = new Map<string, {
      date: string;
      completedVolume: number;
      orderCount: number;
      newCounterparties: number;
    }>();

    for (const order of orders) {
      const dayKey = order.createdAt.toISOString().slice(0, 10) + 'T00:00:00';
      
      if (!dayMap.has(dayKey)) {
        dayMap.set(dayKey, {
          date: dayKey,
          completedVolume: 0,
          orderCount: 0,
          newCounterparties: 0,
        });
      }

      const day = dayMap.get(dayKey)!;
      day.orderCount++;

      if (order.status === 'COMPLETED') {
        day.completedVolume += Number(order.fiatAmount);
      }

      // A counterparty is "new" if we've NEVER seen them before
      const name = order.counterpartyName || order.counterparty || 'Unknown';
      if (!seenBefore.has(name)) {
        seenBefore.add(name); // Mark as seen so they're not counted again tomorrow
        day.newCounterparties++;
      }
    }

    // 4. Convert to OverviewData format
    const overviews = Array.from(dayMap.values()).map(day => ({
      date: day.date,
      "Rows written": day.orderCount,
      "Rows read": day.newCounterparties * 100,
      "Queries": day.orderCount,
      "Payments completed": day.completedVolume,
      "New counterparties": day.newCounterparties,
      "Active orders": day.orderCount,
      "Order volume": day.completedVolume,
      "Logins": day.orderCount,
      "Sign ups": day.newCounterparties,
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
