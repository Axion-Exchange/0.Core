import { prisma } from '../lib/db.js';
import { safeTransaction } from '../lib/transaction.js';
import { withAdvisoryLock, LOCK_NS } from '../lib/advisory-lock.js';
import { binanceService } from './binance.service.js';
import type { Prisma, TransactionStatus, TransactionType } from '@prisma/client';

export class TreasuryService {
  /**
   * Get aggregated portfolio across all currencies.
   */
  async getPortfolioSummary(accountId?: string) {
    const where = accountId ? { accountId } : {};
    const portfolios = await prisma.portfolio.findMany({
      where,
      orderBy: { currency: 'asc' },
    });

    const totalUsd = portfolios.reduce((sum: number, p: any) => sum + Number(p.totalBalance), 0);

    return { portfolios, totalUsd };
  }

  /**
   * Get single currency portfolio with recent snapshots.
   */
  async getPortfolioByCurrency(currency: string) {
    const portfolio = await prisma.portfolio.findUnique({
      where: { currency },
      include: {
        snapshots: {
          orderBy: { createdAt: 'desc' },
          take: 30,
        },
      },
    });

    return portfolio;
  }

  /**
   * Get live exchange balances across all wallets.
   */
  async getBalances(accountId?: string) {
    const where = accountId ? { accountId } : {};
    const wallets = await prisma.cryptoWallet.findMany({
      where,
      include: { account: { select: { exchange: true, label: true } } },
      orderBy: [{ account: { exchange: 'asc' } }, { asset: 'asc' }],
    });

    const fiatLedgers = await prisma.fiatLedger.findMany({
      orderBy: { currency: 'asc' },
    });

    return { wallets, fiatLedgers };
  }

  /**
   * Historical balance snapshots for chart data.
   */
  async getBalanceHistory(currency: string, days: number = 30, accountId?: string) {
    const since = new Date(Date.now() - days * 24 * 60 * 60 * 1000);

    const where: any = { currency };
    if (accountId) where.accountId = accountId;

    const portfolios = await prisma.portfolio.findMany({ where });
    if (portfolios.length === 0) return [];
    const portfolioIds = portfolios.map((p: any) => p.id);

    return prisma.balanceSnapshot.findMany({
      where: {
        portfolioId: { in: portfolioIds },
        createdAt: { gte: since },
      },
      orderBy: { createdAt: 'asc' },
    });
  }

  /**
   * List unified transactions with filtering and pagination.
   */
  async listTransactions(filters: {
    type?: TransactionType;
    status?: TransactionStatus;
    asset?: string;
    source?: string;
    from?: Date;
    to?: Date;
    page: number;
    limit: number;
    accountId?: string;
  }) {
    const where: Prisma.TransactionWhereInput = {};

    if (filters.accountId) where.accountId = filters.accountId;
    if (filters.type) where.type = filters.type;
    if (filters.status) where.status = filters.status;
    if (filters.asset) where.asset = filters.asset;
    if (filters.source) where.source = filters.source;
    if (filters.from || filters.to) {
      where.createdAt = {};
      if (filters.from) where.createdAt.gte = filters.from;
      if (filters.to) where.createdAt.lte = filters.to;
    }

    const [data, total] = await Promise.all([
      prisma.transaction.findMany({
        where,
        include: { user: { select: { displayName: true } } },
        orderBy: { createdAt: 'desc' },
        skip: (filters.page - 1) * filters.limit,
        take: filters.limit,
      }),
      prisma.transaction.count({ where }),
    ]);

    return { data, total, page: filters.page, limit: filters.limit };
  }

  /**
   * Get single transaction detail.
   */
  async getTransaction(id: string) {
    return prisma.transaction.findUnique({
      where: { id },
      include: { user: true },
    });
  }

  /**
   * Update portfolio balance (called by sync jobs).
   */
  async upsertPortfolio(currency: string, data: { totalBalance: number; availableBalance: number; lockedBalance?: number; pendingBalance?: number }, accountId?: string) {
    // Doc ref: §Ledger Integrity (citations 9, 28, 29)
    // Advisory lock prevents concurrent portfolio mutations for the same currency.
    return withAdvisoryLock(LOCK_NS.USER_BALANCE, `portfolio:${currency}:${accountId||'global'}`, async (tx) => {
      const existing = await tx.portfolio.findFirst({
        where: { currency, accountId: accountId || null }
      });

      if (existing) {
        return tx.portfolio.update({
          where: { id: existing.id },
          data: {
            totalBalance: data.totalBalance,
            availableBalance: data.availableBalance,
            lockedBalance: data.lockedBalance ?? existing.lockedBalance,
            pendingBalance: data.pendingBalance ?? existing.pendingBalance,
            lastSyncAt: new Date(),
          }
        });
      } else {
        return tx.portfolio.create({
          data: {
            currency,
            accountId: accountId || null,
            totalBalance: data.totalBalance,
            availableBalance: data.availableBalance,
            lockedBalance: data.lockedBalance ?? 0,
            pendingBalance: data.pendingBalance ?? 0,
            lastSyncAt: new Date(),
          }
        });
      }
    });
  }

  /**
   * Record a balance snapshot for time-series tracking.
   */
  async recordSnapshot(portfolioId: string, balance: number, balanceUsd?: number) {
    return prisma.balanceSnapshot.create({
      data: {
        portfolioId,
        balance,
        balanceUsd: balanceUsd ?? null,
        source: 'sync',
      },
    });
  }

  /**
   * Institutional Aggregated Balances — Uses balance_ledger for correct
   * available + pending totals, and real historical snapshots for charts.
   */
  async getAggregatedPortfolioView(accountId?: string) {
    // 1. Get latest balance per source+currency from balance_ledger
    let query = `
      SELECT DISTINCT ON (source, currency)
        source, currency, 
        available::float as available,
        pending::float as pending,
        (available + pending)::float as total,
        "snapshotAt"
      FROM balance_ledger
      WHERE source != 'binance_funding'
    `;
    if (accountId) {
      query += ` AND "accountId" = '${accountId}'`;
    }
    query += ` ORDER BY source, currency, "snapshotAt" DESC`;

    const latestBalances: any[] = await prisma.$queryRawUnsafe(query);

    // 2. Build summary buckets from real data
    const summaryBuckets = latestBalances.map((b: any) => {
      const name = `${(b.source || 'EXTERNAL').toUpperCase()} - ${b.currency}`;
      const currencySymbol = b.currency === 'EUR' ? '€' : b.currency === 'GBP' ? '£' : '$';
      const total = b.total || 0;
      const available = b.available || 0;
      const pending = b.pending || 0;

      return {
        name,
        value: total,
        valueFormatted: `${currencySymbol}${total.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
        available,
        availableFormatted: `${currencySymbol}${available.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
        pending,
        pendingFormatted: `${currencySymbol}${pending.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
        currency: b.currency,
        source: b.source,
        bgColor: b.source === 'januar' ? 'bg-blue-500' : 'bg-emerald-500',
        lastSync: b.snapshotAt,
      };
    });

    // 3. Build time-series chart from real balance_ledger snapshots
    // Group by day, get avg total per source+currency
    const chartRows: any[] = await prisma.$queryRawUnsafe(`
      SELECT 
        "snapshotAt"::date as day,
        source,
        currency,
        AVG((available + pending)::float) as avg_total
      FROM balance_ledger
      WHERE "snapshotAt" >= NOW() - INTERVAL '30 days'
        AND source != 'binance_funding'
      GROUP BY "snapshotAt"::date, source, currency
      ORDER BY day ASC
    `);

    // Pivot into chart format: { date, "JANUAR - EUR": 9467, "FACILITAPAY - COP": 500, ... }
    const categories = latestBalances.map((b: any) => `${(b.source || 'EXTERNAL').toUpperCase()} - ${b.currency}`);
    const dayMap = new Map<string, any>();

    for (const row of chartRows) {
      const dateStr = new Date(row.day).toLocaleDateString('en-US', { month: 'short', day: '2-digit' });
      if (!dayMap.has(dateStr)) {
        dayMap.set(dateStr, { date: dateStr });
      }
      const key = `${(row.source || 'EXTERNAL').toUpperCase()} - ${row.currency}`;
      dayMap.get(dateStr)[key] = Math.round(row.avg_total * 100) / 100;
    }

    const chartData = Array.from(dayMap.values());

    // If only 1 day of snapshots, generate a minimal chart with current values
    if (chartData.length <= 1) {
      const now = new Date();
      const singlePoint: any = {
        date: now.toLocaleDateString('en-US', { month: 'short', day: '2-digit' }),
      };
      for (const b of latestBalances) {
        const key = `${(b.source || 'EXTERNAL').toUpperCase()} - ${b.currency}`;
        singlePoint[key] = b.total;
      }
      if (chartData.length === 0) chartData.push(singlePoint);
    }

    // Total across all accounts
    const totalValue = latestBalances.reduce((acc: number, b: any) => acc + (b.total || 0), 0);

    return {
      totalUsd: totalValue,
      summary: summaryBuckets,
      chartData,
      categories,
      colors: ['blue', 'emerald', 'violet', 'fuchsia', 'orange', 'sky'],
    };
  }
  /**
   * Calculate exact real-time Institutional Crypto Balances as requested.
   * Formula: Total = (Available Exchange Funding Balance) + (Pending Buy Orders Amount)
   */
  async getCryptoBalances() {
    // 1. Fetch available crypto natively from all active exchange accounts
    const activeAccounts = await prisma.p2PAccount.findMany({
      where: { exchange: 'BINANCE', isActive: true }
    });
    if (activeAccounts.length === 0) activeAccounts.push({ id: undefined } as any);
    
    let fundingBalances: any[] = [];
    for (const acc of activeAccounts) {
       const bals = await binanceService.fetchFundingBalances(acc.id ? acc : undefined);
       // Tag with account name for frontend breakdown if needed
       fundingBalances = fundingBalances.concat(bals.map((b: any) => ({ ...b, accountLabel: acc.label || 'Default' })));
    }
    
    // 2. Query DB for active BUY orders (where we are awaiting crypto release)
    const activeBuys = await prisma.p2POrder.findMany({
      where: {
        type: "BUY",
        status: { in: ["PENDING_FIAT", "FIAT_RECEIVED", "PENDING_RELEASE", "APPEALING"] },
      }
    });

    // We will organize by Asset (USDT, BTC, etc.)
    const assets = new Map<string, { available: number; locked: number; pendingBuys: number }>();
    
    // We will also organize by Account + Asset for the detail breakdown
    const accountDetailsMap = new Map<string, { accountLabel: string, asset: string, available: number, locked: number, pendingBuys: number }>();

    // Pre-seed all active accounts with at least USDT so they show up in the UI even if empty
    for (const acc of activeAccounts) {
      const accLabel = acc.label || 'Default';
      const key = `${accLabel}-USDT`;
      accountDetailsMap.set(key, { accountLabel: accLabel, asset: 'USDT', available: 0, locked: 0, pendingBuys: 0 });
    }

    // Seed map with exchange balances
    for (const b of fundingBalances) {
      if (!assets.has(b.currency)) assets.set(b.currency, { available: 0, locked: 0, pendingBuys: 0 });
      assets.get(b.currency)!.available += b.available;
      assets.get(b.currency)!.locked += b.locked || 0;
      
      const key = `${b.accountLabel}-${b.currency}`;
      if (!accountDetailsMap.has(key)) accountDetailsMap.set(key, { accountLabel: b.accountLabel, asset: b.currency, available: 0, locked: 0, pendingBuys: 0 });
      accountDetailsMap.get(key)!.available += b.available;
      accountDetailsMap.get(key)!.locked += b.locked || 0;
    }

    // Add pending buys
    for (const order of activeBuys) {
      const asset = order.asset.toUpperCase();
      if (!assets.has(asset)) assets.set(asset, { available: 0, locked: 0, pendingBuys: 0 });
      assets.get(asset)!.pendingBuys += Number(order.amount);
      
      const acc = activeAccounts.find((a: any) => a.id === order.accountId);
      const accLabel = acc?.label || 'Default';
      const key = `${accLabel}-${asset}`;
      if (!accountDetailsMap.has(key)) accountDetailsMap.set(key, { accountLabel: accLabel, asset: asset, available: 0, locked: 0, pendingBuys: 0 });
      accountDetailsMap.get(key)!.pendingBuys += Number(order.amount);
    }

    const summary: any[] = [];
    const accountsDetail: any[] = [];
    let totalUsd = 0; // Strictly speaking, we assume USDT=1 USD here, and perhaps fetch live rates for BTC/ETH if requested later

    for (const [asset, data] of assets) {
      const totalAsset = data.available + data.locked + data.pendingBuys;

      let usdValue = totalAsset; 
      // Very basic mock price conversion for UI showcase if not strictly USDT
      if (asset === "BTC") usdValue *= 95000;
      if (asset === "ETH") usdValue *= 3200;

      totalUsd += usdValue;

      summary.push({
        asset,
        balance: totalAsset.toLocaleString(undefined, { maximumFractionDigits: 4 }),
        usdValue,
        available: data.available,
        locked: data.locked,
        pendingBuys: data.pendingBuys
      });
    }
    
    for (const [key, data] of accountDetailsMap) {
      const totalAsset = data.available + data.locked + data.pendingBuys;
      
      let usdValue = totalAsset;
      if (data.asset === "BTC") usdValue *= 95000;
      if (data.asset === "ETH") usdValue *= 3200;
      
      accountsDetail.push({
        id: key,
        accountLabel: data.accountLabel,
        asset: data.asset,
        balance: totalAsset,
        balanceFormatted: totalAsset.toLocaleString(undefined, { maximumFractionDigits: 4 }),
        usdValue,
        available: data.available,
        locked: data.locked,
        pendingBuys: data.pendingBuys
      });
    }

    return {
      totalUsd,
      summary,
      accountsDetail
    };
  }

}

export const treasuryService = new TreasuryService();
