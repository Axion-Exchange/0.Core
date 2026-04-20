import { createLogger } from '../../lib/logger.js';
import { fifoPnlService } from './fifo-pnl.service.js';
import { Prisma } from '@prisma/client';

const Decimal = Prisma.Decimal;
type Decimal = Prisma.Decimal;

const log = createLogger('pricing-engine');

export interface PricingStatus {
  lastWac: string;
  lastSellPrice: string;
  targetNetMargin: string;
  feeBuffer: string;
}

/**
 * Dynamic Pricing Engine
 * Translates PearV2's `pricing_engine.py` logic exactly.
 * Applies True FIFO WAC against target profit margins to compute actual Binance SELL AD limits.
 */
export class PricingEngineService {
  private targetNetMargin: Decimal;
  private feeBuffer: Decimal;
  private minSellPrice: Decimal;
  private maxSellPrice: Decimal;
  
  private lastWac: string = '0.000';
  private lastSellPrice: string = '0.000';

  constructor() {
    // Defined dynamically as margins off env variables, defaults identical to Python port
    this.targetNetMargin = new Decimal(process.env.PRICING_TARGET_NET_MARGIN || '0.5').div(100);
    this.feeBuffer = new Decimal(process.env.PRICING_FEE_BUFFER || '0.2').div(100);
    this.minSellPrice = new Decimal(process.env.PRICING_MIN_SELL_PRICE || '0.840');
    this.maxSellPrice = new Decimal(process.env.PRICING_MAX_SELL_PRICE || '0.990');
    
    log.info(
      `PricingEngine initialized: netMargin=${this.targetNetMargin.mul(100).toFixed(2)}%, ` +
      `feeBuffer=${this.feeBuffer.mul(100).toFixed(2)}%`
    );
  }

  /**
   * Called persistently by `p2p.worker.ts` Orchestrator tick.
   */
  public async computeTargetSellPrice(): Promise<string | null> {
    try {
      // Step 1: Calculate current WAC from the newly translated FifoEngine
      // Look back 7 days by default to match PearV2 recent inventory constraints
      const fromDate = new Date();
      fromDate.setDate(fromDate.getDate() - 7);
      
      const summary = await fifoPnlService.computeFifo(fromDate);
      const wac = new Decimal(summary.inventoryAvgCost || '0');

      if (wac.lte(0)) {
         log.warn('PricingEngine: WAC unavailable or invalid (≤ 0), aborting price adjustment.');
         return null;
      }

      this.lastWac = wac.toFixed(4);

      // Step 2: Target Sell = WAC * (1.0 + net_margin + fee_buffer)
      const multiplier = new Decimal('1').plus(this.targetNetMargin).plus(this.feeBuffer);
      let targetSell = wac.mul(multiplier);

      // Clamping security bounds
      targetSell = Decimal.max(this.minSellPrice, Decimal.min(this.maxSellPrice, targetSell));

      // Round to 3 decimal places which conforms with Binance priceScale for EUR/USDT
      this.lastSellPrice = targetSell.toFixed(3);

      log.info(
        `PRICING TICK: WAC=€${this.lastWac} -> sell=€${this.lastSellPrice} ` +
        `(+${targetSell.div(wac).minus(1).mul(100).toFixed(2)}%)`
      );

      return this.lastSellPrice;
      
    } catch (error) {
      log.error('Pricing calculation error', { error });
      return null;
    }
  }

  public getStatus(): PricingStatus {
    return {
      lastWac: this.lastWac,
      lastSellPrice: this.lastSellPrice,
      targetNetMargin: `${this.targetNetMargin.mul(100).toFixed(2)}%`,
      feeBuffer: `${this.feeBuffer.mul(100).toFixed(2)}%`,
    };
  }
}

export const pricingEngineService = new PricingEngineService();
