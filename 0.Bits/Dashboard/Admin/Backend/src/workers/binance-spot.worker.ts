import { prisma } from '../lib/db.js';
import { createLogger } from '../lib/logger.js';

const log = createLogger('binance-spot-worker');

class BinanceSpotWorker {
  private intervalId?: NodeJS.Timeout;

  public start(intervalMs: number = 300000) { // Default 5 minutes
    log.info(`Booting Binance Spot Worker [rate: ${intervalMs}ms]...`);
    this.processTick();
    this.intervalId = setInterval(() => this.processTick(), intervalMs);
  }

  public stop() {
    if (this.intervalId) clearInterval(this.intervalId);
    log.info('Binance Spot Worker halted.');
  }

  public async run() {
    return this.processTick();
  }

  private async processTick() {
    try {
      const res = await fetch('https://api.binance.com/api/v3/ticker/bookTicker?symbol=USDTMXN');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      
      const json: any = await res.json();
      
      if (json.symbol === 'USDTMXN' && json.bidPrice && json.askPrice) {
        const bid = parseFloat(json.bidPrice);
        const ask = parseFloat(json.askPrice);
        const midPrice = (bid + ask) / 2;

        if (midPrice > 0) {
          await prisma.systemSetting.upsert({
            where: { key: 'BINANCE_SPOT_USDTMXN_MID' },
            create: { key: 'BINANCE_SPOT_USDTMXN_MID', value: midPrice.toString() },
            update: { value: midPrice.toString() }
          });
          log.info(`Updated BINANCE_SPOT_USDTMXN_MID to ${midPrice}`);
        }
      } else {
        log.warn(`Invalid response from Binance Spot API: ${JSON.stringify(json)}`);
      }
    } catch (err: any) {
      log.error(`[BinanceSpotWorker] Failed to fetch spot price: ${err.message}`);
    }
  }
}

export const binanceSpotWorker = new BinanceSpotWorker();
