import { prisma } from '../lib/db.js';
import { createLogger } from '../lib/logger.js';

const log = createLogger('mexc-spot-worker');

class MexcSpotWorker {
  private intervalId?: NodeJS.Timeout;

  public start(intervalMs: number = 300000) { // Default 5 minutes
    log.info(`Booting MEXC Spot Worker [rate: ${intervalMs}ms]...`);
    this.processTick();
    this.intervalId = setInterval(() => this.processTick(), intervalMs);
  }

  public stop() {
    if (this.intervalId) clearInterval(this.intervalId);
    log.info('MEXC Spot Worker halted.');
  }

  public async run() {
    return this.processTick();
  }

  private async processTick() {
    try {
      const res = await fetch('https://api.mexc.com/api/v3/ticker/bookTicker?symbol=MXNUSDT');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      
      const json: any = await res.json();
      
      if (json.symbol === 'MXNUSDT' && json.bidPrice && json.askPrice) {
        const bid = parseFloat(json.bidPrice);
        const ask = parseFloat(json.askPrice);
        const midPrice = (bid + ask) / 2;

        // Invert the price (1 / MXNUSDT) to get the USDT/MXN rate suitable for P2P margins
        // e.g., 1 / 0.05458 = ~18.32 MXN per USDT
        const invertedPrice = midPrice > 0 ? 1 / midPrice : 0;

        if (invertedPrice > 0) {
          await prisma.systemSetting.upsert({
            where: { key: 'MEXC_SPOT_USDTMXN_MID' },
            create: { key: 'MEXC_SPOT_USDTMXN_MID', value: invertedPrice.toString() },
            update: { value: invertedPrice.toString() }
          });
          log.info(`Updated MEXC_SPOT_USDTMXN_MID to ${invertedPrice} (Original MXNUSDT: ${midPrice})`);
        }
      } else {
        log.warn(`Invalid response from MEXC Spot API: ${JSON.stringify(json)}`);
      }
    } catch (err: any) {
      log.error(`[MexcSpotWorker] Failed to fetch spot price: ${err.message}`);
    }
  }
}

export const mexcSpotWorker = new MexcSpotWorker();
