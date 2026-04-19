import { prisma } from '../lib/db.js';
import type { Prisma, TransactionStatus, TransactionType } from '@prisma/client';

export class TreasuryService {
  /**
   * Get aggregated portfolio across all currencies.
   */
  async getPortfolioSummary() {
    const portfolios = await prisma.portfolio.findMany({
      orderBy: { currency: 'asc' },
    });

    const totalUsd = portfolios.reduce((sum, p) => sum + Number(p.totalBalance), 0);

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
  async getBalances() {
    const wallets = await prisma.cryptoWallet.findMany({
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
  async getBalanceHistory(currency: string, days: number = 30) {
    const since = new Date(Date.now() - days * 24 * 60 * 60 * 1000);

    const portfolio = await prisma.portfolio.findUnique({ where: { currency } });
    if (!portfolio) return [];

    return prisma.balanceSnapshot.findMany({
      where: {
        portfolioId: portfolio.id,
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
  }) {
    const where: Prisma.TransactionWhereInput = {};

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
  async upsertPortfolio(currency: string, data: { totalBalance: number; availableBalance: number; lockedBalance?: number; pendingBalance?: number }) {
    return prisma.portfolio.upsert({
      where: { currency },
      create: {
        currency,
        totalBalance: data.totalBalance,
        availableBalance: data.availableBalance,
        lockedBalance: data.lockedBalance ?? 0,
        pendingBalance: data.pendingBalance ?? 0,
        lastSyncAt: new Date(),
      },
      update: {
        totalBalance: data.totalBalance,
        availableBalance: data.availableBalance,
        lockedBalance: data.lockedBalance ?? 0,
        pendingBalance: data.pendingBalance ?? 0,
        lastSyncAt: new Date(),
      },
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
}

export const treasuryService = new TreasuryService();
