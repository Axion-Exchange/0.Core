import { prisma } from '../lib/db.js';
import { createLogger } from '../lib/logger.js';

const log = createLogger('bitget-spot-worker');

class BitgetSpotWorker {
  private intervalId?: NodeJS.Timeout;

  public start(intervalMs: number = 600000) { // Default 10 minutes
    log.info(`Booting Bitget Spot Worker [rate: ${intervalMs}ms]...`);
    this.processTick();
    this.intervalId = setInterval(() => this.processTick(), intervalMs);
  }

  public stop() {
    if (this.intervalId) clearInterval(this.intervalId);
    log.info('Bitget Spot Worker halted.');
  }

  public async run() {
    return this.processTick();
  }

  private async processTick() {
    try {
      const res = await fetch('https://api.bitget.com/api/v2/spot/market/tickers?symbol=USDTEUR');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      
      const json: any = await res.json();
      
      if (json.code === '00000' && json.data && json.data.length > 0) {
        const data = json.data[0];
        const bid = parseFloat(data.bidPr);
        const ask = parseFloat(data.askPr);
        const midPrice = (bid + ask) / 2;

        await prisma.systemSetting.upsert({
          where: { key: 'BITGET_SPOT_USDTEUR_MID' },
          create: { key: 'BITGET_SPOT_USDTEUR_MID', value: midPrice.toString() },
          update: { value: midPrice.toString() }
        });

        log.info(`Updated BITGET_SPOT_USDTEUR_MID to ${midPrice}`);
      } else {
        log.warn(`Invalid response from Bitget Spot API: ${JSON.stringify(json)}`);
      }
    } catch (err: any) {
      log.error(`[BitgetSpotWorker] Failed to fetch spot price: ${err.message}`);
    }
  }
}

export const bitgetSpotWorker = new BitgetSpotWorker();
