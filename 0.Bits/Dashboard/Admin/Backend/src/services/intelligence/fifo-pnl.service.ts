import { PrismaClient, AdType, OrderStatus, Prisma } from '@prisma/client';
import { createLogger } from '../../lib/logger.js';
const Decimal = Prisma.Decimal;

const log = createLogger('fifo-pnl');

export interface PnLSummary {
  periodStart: Date;
  periodEnd: Date;
  buyCount: number;
  sellCount: number;
  buyVolumeEur: string;
  sellVolumeEur: string;
  buyVolumeCrypto: string;
  sellVolumeCrypto: string;
  realizedPnl: string;
  avgBuyPrice: string;
  avgSellPrice: string;
  avgSpreadPct: string;
  inventoryQty: string;
  inventoryAvgCost: string;
}

export class FifoPnlService {
  private db: PrismaClient;

  constructor(db?: PrismaClient) {
    this.db = db || new PrismaClient();
  }

  /**
   * Translates the True-FIFO Unified Weighted Average Cost Tracking Engine.
   * Leverages Prisma P2P Orders to dynamically map all trades and output Realized PnL.
   */
  public async computeFifo(fromDate?: Date, toDate?: Date): Promise<PnLSummary> {
    const whereClause: any = {
      fiat: 'EUR',
      status: OrderStatus.COMPLETED,
    };

    if (fromDate || toDate) {
      whereClause.createdAt = {};
      if (fromDate) whereClause.createdAt.gte = fromDate;
      if (toDate) whereClause.createdAt.lte = toDate;
    }

    const orders = await this.db.p2POrder.findMany({
      where: whereClause,
      orderBy: { createdAt: 'asc' },
    });

    log.info(`Computing FIFO PnL across ${orders.length} orders.`);

    let invQty = new Decimal('0');
    let invAvgCost = new Decimal('0');
    let realizedPnl = new Decimal('0');
    let buyCount = 0;
    let sellCount = 0;
    let buyVolumeEur = new Decimal('0');
    let sellVolumeEur = new Decimal('0');
    let buyVolumeCrypto = new Decimal('0');
    let sellVolumeCrypto = new Decimal('0');

    for (const order of orders) {
      const cryptoAmount = new Decimal(order.amount.toString());
      const fiatAmount = new Decimal(order.fiatAmount.toString());

      if (order.type === AdType.BUY) {
        buyCount++;
        buyVolumeEur = buyVolumeEur.plus(fiatAmount);
        buyVolumeCrypto = buyVolumeCrypto.plus(cryptoAmount);

        // Update WAC (Weighted Average Cost)
        const oldTotalCost = invQty.mul(invAvgCost);
        const newTotalCost = oldTotalCost.plus(fiatAmount);
        invQty = invQty.plus(cryptoAmount);
        invAvgCost = invQty.greaterThan(0) ? newTotalCost.div(invQty) : new Decimal('0');

      } else if (order.type === AdType.SELL) {
        sellCount++;
        sellVolumeEur = sellVolumeEur.plus(fiatAmount);
        sellVolumeCrypto = sellVolumeCrypto.plus(cryptoAmount);

        // P&L = (Revenue - Cost Basis)
        const sellQty = cryptoAmount;
        const costBasis = invAvgCost.mul(sellQty);
        const revenue = fiatAmount;
        const tradePnl = revenue.minus(costBasis);

        realizedPnl = realizedPnl.plus(tradePnl);

        // Reduce inventory
        invQty = Decimal.max(0, invQty.minus(sellQty));
      }
    }

    const avgBuy = buyVolumeCrypto.greaterThan(0)
      ? buyVolumeEur.div(buyVolumeCrypto).toDecimalPlaces(4)
      : new Decimal('0');

    const avgSell = sellVolumeCrypto.greaterThan(0)
      ? sellVolumeEur.div(sellVolumeCrypto).toDecimalPlaces(4)
      : new Decimal('0');

    const spread = avgBuy.greaterThan(0)
      ? avgSell.minus(avgBuy).div(avgBuy).mul(100).toDecimalPlaces(2)
      : new Decimal('0');

    const now = new Date();
    const periodStart = fromDate || (orders.length > 0 ? orders[0]!.createdAt : now);
    const periodEnd = toDate || now;
    
    return {
      periodStart,
      periodEnd,
      buyCount,
      sellCount,
      buyVolumeEur: buyVolumeEur.toFixed(2),
      sellVolumeEur: sellVolumeEur.toFixed(2),
      buyVolumeCrypto: buyVolumeCrypto.toFixed(4),
      sellVolumeCrypto: sellVolumeCrypto.toFixed(4),
      realizedPnl: realizedPnl.toFixed(2),
      avgBuyPrice: avgBuy.toFixed(4),
      avgSellPrice: avgSell.toFixed(4),
      avgSpreadPct: spread.toFixed(2),
      inventoryQty: invQty.toFixed(4),
      inventoryAvgCost: invAvgCost.toDecimalPlaces(4).toFixed(4),
    };
  }

  public async getSummary(period: 'today' | 'yesterday' | 'week' | 'month' | 'all' = 'today'): Promise<PnLSummary> {
    const now = new Date();
    const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());

    let fromDate: Date | undefined;
    let toDate: Date | undefined;

    switch (period) {
      case 'today':
        fromDate = todayStart;
        break;
      case 'yesterday':
        fromDate = new Date(todayStart.getTime() - 24 * 60 * 60 * 1000);
        toDate = todayStart;
        break;
      case 'week':
        const day = todayStart.getDay();
        const diff = todayStart.getDate() - day + (day === 0 ? -6 : 1); 
        fromDate = new Date(todayStart.setDate(diff));
        break;
      case 'month':
        fromDate = new Date(now.getFullYear(), now.getMonth(), 1);
        break;
      case 'all':
        fromDate = undefined;
        toDate = undefined;
        break;
    }

    return this.computeFifo(fromDate, toDate);
  }
}

export const fifoPnlService = new FifoPnlService();
