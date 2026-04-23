/**
 * P&L Snapshot Service
 * 
 * Computes daily FIFO P&L snapshots and stores them in pnl_snapshots table.
 * Uses USDT (crypto) amounts — consistent with the dashboard transaction charts.
 */

import { prisma } from "../lib/db.js";
import { createLogger } from "../lib/logger.js";
import { fifoV2 } from "./intelligence/fifo-v2.service.js";

const log = createLogger("pnl-snapshot");

/**
 * Compute and store daily P&L snapshot for a given currency and date.
 * Volumes are in USDT (crypto amount), P&L is the spread captured.
 */
export async function computeDailyPnlSnapshot(currency: string, date: Date, accountId?: string) {
  const dayStart = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  const dayEnd = new Date(dayStart.getTime() + 86400000);

  const result = await fifoV2.computeForCurrency(currency, dayStart, dayEnd, accountId);

  // If no accountId is provided, we might still want a global snapshot, but since we added accountId to unique constraint, let's pass it.
  const uniqueKey = accountId 
    ? { date_currency_accountId: { date: dayStart, currency, accountId } } 
    : { date_currency: { date: dayStart, currency } } as any;

  return prisma.pnlSnapshot.upsert({
    where: uniqueKey,
    create: {
      date: dayStart,
      currency,
      realizedPnl: parseFloat(result.realizedPnlUsdt),
      buyCount: result.buyCount,
      sellCount: result.sellCount,
      buyVolume: parseFloat(result.buyVolumeCrypto),
      sellVolume: parseFloat(result.sellVolumeCrypto),
      spreadPct: parseFloat(result.spreadPct),
      inventoryQty: parseFloat(result.inventoryQty),
      accountId: accountId || null,
    },
    update: {
      realizedPnl: parseFloat(result.realizedPnlUsdt),
      buyCount: result.buyCount,
      sellCount: result.sellCount,
      buyVolume: parseFloat(result.buyVolumeCrypto),
      sellVolume: parseFloat(result.sellVolumeCrypto),
      spreadPct: parseFloat(result.spreadPct),
      inventoryQty: parseFloat(result.inventoryQty),
    },
  });
}

/**
 * Backfill P&L snapshots for the last N days.
 */
export async function backfillPnlSnapshots(days: number = 180, currency: string = "EUR") {
  log.info(`[PnL] Backfilling ${days} days for ${currency}...`);
  const now = new Date();
  let count = 0;

  const accounts = await prisma.p2PAccount.findMany();

  for (let i = days; i >= 0; i--) {
    const date = new Date(now.getTime() - i * 86400000);
    for (const account of accounts) {
      try {
        await computeDailyPnlSnapshot(currency, date, account.id);
        count++;
      } catch (err) {
        // Skip days with no data
      }
    }
  }

  log.info(`[PnL] Backfilled ${count} snapshots for ${currency}`);
  return count;
}

/**
 * Get daily P&L time-series for charting.
 */
export async function getPnlTimeSeries(currency: string = "EUR", days: number = 180, accountId?: string) {
  const since = new Date(Date.now() - days * 86400000);

  const whereClause: any = {
    currency,
    date: { gte: since },
  };
  if (accountId) whereClause.accountId = accountId;

  return prisma.pnlSnapshot.findMany({
    where: whereClause,
    orderBy: { date: "asc" },
  });
}
