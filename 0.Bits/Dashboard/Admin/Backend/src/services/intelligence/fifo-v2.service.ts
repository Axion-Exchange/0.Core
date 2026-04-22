/**
 * True FIFO P&L Engine v2
 * 
 * ═══════════════════════════════════════════════════════════════
 * FIXES from v1:
 *   1. Actual FIFO queue (not WAC) — oldest buy lots consumed first
 *   2. Multi-currency: separate P&L for EUR, COP, MXN, GBP
 *   3. Full cost-basis carry-forward — queries ALL history then
 *      slices the period window, so inventory from prior periods
 *      is correctly accounted for
 * ═══════════════════════════════════════════════════════════════
 */

import { PrismaClient, AdType, OrderStatus, Prisma } from '@prisma/client';
import { createLogger } from '../../lib/logger.js';
import { prisma } from '../../lib/db.js';

const Decimal = Prisma.Decimal;
const log = createLogger('fifo-v2');

// ── Types ────────────────────────────────────────────────────────────────────

interface FifoLot {
  orderId: string;
  qty: typeof Decimal.prototype;
  costPerUnit: typeof Decimal.prototype;
  date: Date;
}

export interface FifoPnLResult {
  currency: string;
  periodStart: Date;
  periodEnd: Date;
  // Counts
  buyCount: number;
  sellCount: number;
  // Volumes
  buyVolumeFiat: string;
  sellVolumeFiat: string;
  buyVolumeCrypto: string;
  sellVolumeCrypto: string;
  // P&L (EUR)
  realizedPnl: string;
  unrealizedPnl: string;
  totalPnl: string;
  // P&L (USDT) — EUR P&L converted at each trade's actual sell rate
  realizedPnlUsdt: string;
  // Pricing
  avgBuyPrice: string;
  avgSellPrice: string;
  spreadPct: string;
  // Inventory
  inventoryQty: string;
  inventoryCostBasis: string;
  inventoryAvgCost: string;
  // Lot detail
  openLots: number;
  matchedTrades: MatchedTrade[];
}

export interface MatchedTrade {
  sellOrderId: string;
  sellDate: Date;
  sellQty: string;
  sellPrice: string;
  buyOrderId: string;
  buyDate: Date;
  buyPrice: string;
  pnl: string;
}

export interface MultiCurrencyPnL {
  currencies: Record<string, FifoPnLResult>;
  aggregatedPnlEur: string;
  timestamp: string;
}

// ── Engine ───────────────────────────────────────────────────────────────────

export class FifoV2Engine {
  private db: PrismaClient;

  constructor(db?: PrismaClient) {
    this.db = db || prisma;
  }

  /**
   * Compute true FIFO P&L for a single currency.
   * 
   * Key difference from v1: We load ALL orders from the beginning of time
   * to build the full cost-basis queue, then only report P&L for the
   * requested period. This ensures inventory carry-forward is correct.
   */
  async computeForCurrency(
    currency: string,
    periodStart?: Date,
    periodEnd?: Date,
  ): Promise<FifoPnLResult> {
    const now = new Date();
    const pStart = periodStart || new Date(2020, 0, 1);
    const pEnd = periodEnd || now;

    // Load ALL completed orders for this currency, sorted chronologically
    const allOrders = await this.db.p2POrder.findMany({
      where: {
        fiat: currency,
        status: OrderStatus.COMPLETED,
        createdAt: { lte: pEnd },
      },
      orderBy: { createdAt: 'asc' },
    });

    // FIFO queue: oldest lots at front
    const queue: FifoLot[] = [];
    const matchedTrades: MatchedTrade[] = [];

    // Period-specific counters (only count orders IN the period)
    let buyCount = 0;
    let sellCount = 0;
    let buyVolumeFiat = new Decimal('0');
    let sellVolumeFiat = new Decimal('0');
    let buyVolumeCrypto = new Decimal('0');
    let sellVolumeCrypto = new Decimal('0');
    let realizedPnl = new Decimal('0');
    let realizedPnlUsdt = new Decimal('0');

    for (const order of allOrders) {
      const cryptoQty = new Decimal(order.amount.toString());
      const fiatAmt = new Decimal(order.fiatAmount.toString());
      const pricePerUnit = cryptoQty.gt(0) ? fiatAmt.div(cryptoQty) : new Decimal('0');
      const isInPeriod = order.createdAt >= pStart && order.createdAt <= pEnd;

      if (order.type === AdType.BUY) {
        // Push to FIFO queue
        queue.push({
          orderId: order.id,
          qty: cryptoQty,
          costPerUnit: pricePerUnit,
          date: order.createdAt,
        });

        if (isInPeriod) {
          buyCount++;
          buyVolumeFiat = buyVolumeFiat.plus(fiatAmt);
          buyVolumeCrypto = buyVolumeCrypto.plus(cryptoQty);
        }

      } else if (order.type === AdType.SELL) {
        // Consume oldest lots from FIFO queue
        let remaining = cryptoQty;

        while (remaining.gt(0) && queue.length > 0) {
          const lot = queue[0]!;
          const consumed = Decimal.min(remaining, lot.qty);

          // Cost basis for consumed portion
          const costBasis = consumed.mul(lot.costPerUnit);
          const revenue = consumed.mul(pricePerUnit);
          const tradePnl = revenue.minus(costBasis);

          if (isInPeriod) {
            realizedPnl = realizedPnl.plus(tradePnl);
            // Convert EUR P&L to USDT using THIS trade's actual sell rate
            if (pricePerUnit.gt(0)) {
              realizedPnlUsdt = realizedPnlUsdt.plus(tradePnl.div(pricePerUnit));
            }

            matchedTrades.push({
              sellOrderId: order.id,
              sellDate: order.createdAt,
              sellQty: consumed.toFixed(4),
              sellPrice: pricePerUnit.toFixed(4),
              buyOrderId: lot.orderId,
              buyDate: lot.date,
              buyPrice: lot.costPerUnit.toFixed(4),
              pnl: tradePnl.toFixed(2),
            });
          }

          // Reduce lot
          lot.qty = lot.qty.minus(consumed);
          remaining = remaining.minus(consumed);

          // Remove exhausted lot
          if (lot.qty.lte(0)) {
            queue.shift();
          }
        }

        if (isInPeriod) {
          sellCount++;
          sellVolumeFiat = sellVolumeFiat.plus(fiatAmt);
          sellVolumeCrypto = sellVolumeCrypto.plus(cryptoQty);
        }
      }
    }

    // Inventory remaining in queue
    let invQty = new Decimal('0');
    let invCostBasis = new Decimal('0');
    for (const lot of queue) {
      invQty = invQty.plus(lot.qty);
      invCostBasis = invCostBasis.plus(lot.qty.mul(lot.costPerUnit));
    }
    const invAvgCost = invQty.gt(0) ? invCostBasis.div(invQty) : new Decimal('0');

    // Averages
    const avgBuy = buyVolumeCrypto.gt(0)
      ? buyVolumeFiat.div(buyVolumeCrypto)
      : new Decimal('0');
    const avgSell = sellVolumeCrypto.gt(0)
      ? sellVolumeFiat.div(sellVolumeCrypto)
      : new Decimal('0');
    const spread = avgBuy.gt(0)
      ? avgSell.minus(avgBuy).div(avgBuy).mul(100)
      : new Decimal('0');

    // Unrealized P&L (mark inventory to latest sell price)
    const unrealizedPnl = avgSell.gt(0) && invQty.gt(0)
      ? invQty.mul(avgSell.minus(invAvgCost))
      : new Decimal('0');

    return {
      currency,
      periodStart: pStart,
      periodEnd: pEnd,
      buyCount,
      sellCount,
      buyVolumeFiat: buyVolumeFiat.toFixed(2),
      sellVolumeFiat: sellVolumeFiat.toFixed(2),
      buyVolumeCrypto: buyVolumeCrypto.toFixed(4),
      sellVolumeCrypto: sellVolumeCrypto.toFixed(4),
      realizedPnl: realizedPnl.toFixed(2),
      realizedPnlUsdt: realizedPnlUsdt.toFixed(2),
      unrealizedPnl: unrealizedPnl.toFixed(2),
      totalPnl: realizedPnl.plus(unrealizedPnl).toFixed(2),
      avgBuyPrice: avgBuy.toFixed(4),
      avgSellPrice: avgSell.toFixed(4),
      spreadPct: spread.toFixed(2),
      inventoryQty: invQty.toFixed(4),
      inventoryCostBasis: invCostBasis.toFixed(2),
      inventoryAvgCost: invAvgCost.toFixed(4),
      openLots: queue.length,
      matchedTrades: matchedTrades.slice(-50), // last 50 for API response size
    };
  }

  /**
   * Compute FIFO P&L for ALL active currencies.
   */
  async computeAll(periodStart?: Date, periodEnd?: Date): Promise<MultiCurrencyPnL> {
    // Discover which currencies have completed orders
    const activeCurrencies = await this.db.p2POrder.groupBy({
      by: ['fiat'],
      where: { status: OrderStatus.COMPLETED },
      _count: true,
    });

    const currencies: Record<string, FifoPnLResult> = {};
    let totalPnlEur = new Decimal('0');

    for (const { fiat } of activeCurrencies) {
      const result = await this.computeForCurrency(fiat, periodStart, periodEnd);
      currencies[fiat] = result;

      // Aggregate to EUR equivalent (rough conversion for non-EUR)
      const pnl = new Decimal(result.realizedPnl);
      if (fiat === 'EUR') {
        totalPnlEur = totalPnlEur.plus(pnl);
      } else if (fiat === 'GBP') {
        totalPnlEur = totalPnlEur.plus(pnl.mul('1.17')); // GBP→EUR approx
      } else if (fiat === 'COP') {
        totalPnlEur = totalPnlEur.plus(pnl.div('4500')); // COP→EUR approx
      } else if (fiat === 'MXN') {
        totalPnlEur = totalPnlEur.plus(pnl.div('18.5')); // MXN→EUR approx
      }
    }

    return {
      currencies,
      aggregatedPnlEur: totalPnlEur.toFixed(2),
      timestamp: new Date().toISOString(),
    };
  }

  /**
   * Helper: get P&L for standard periods.
   */
  async getSummary(
    currency: string,
    period: 'today' | 'yesterday' | 'week' | 'month' | 'all' = 'today',
  ): Promise<FifoPnLResult> {
    const now = new Date();
    const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());

    let fromDate: Date | undefined;
    let toDate: Date | undefined;

    switch (period) {
      case 'today':
        fromDate = todayStart;
        break;
      case 'yesterday':
        fromDate = new Date(todayStart.getTime() - 86400000);
        toDate = todayStart;
        break;
      case 'week':
        fromDate = new Date(todayStart.getTime() - 7 * 86400000);
        break;
      case 'month':
        fromDate = new Date(now.getFullYear(), now.getMonth(), 1);
        break;
      case 'all':
        break;
    }

    return this.computeForCurrency(currency, fromDate, toDate);
  }
}

export const fifoV2 = new FifoV2Engine();
