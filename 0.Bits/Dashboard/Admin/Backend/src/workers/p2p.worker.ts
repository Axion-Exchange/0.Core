import { createLogger } from '../lib/logger.js';
import { exchangeService } from '../services/exchange.service.js';
import { prisma } from '../lib/db.js';
import { pricingEngineService } from '../services/intelligence/pricing-engine.service.js';

const log = createLogger('p2p-orchestrator-worker');

/**
 * P2P Orchestrator Daemon
 * Runs on a configured interval to ping all active P2P connections,
 * scrape order matching histories, and fetch public market depth.
 */
export class P2POrchestratorWorker {
  private intervalId: NodeJS.Timeout | null = null;
  private intervalMs: number;
  private isRunning = false;

  constructor(intervalMs = 15000) {
    this.intervalMs = intervalMs;
  }

  start() {
    if (this.intervalId) return;
    
    log.info(`Booting P2P Polling Core [rate: ${this.intervalMs}ms]`);
    
    this.intervalId = setInterval(() => this.tick(), this.intervalMs);
  }

  stop() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
      log.info('P2P Polling Core safely halted.');
    }
  }

  private async tick() {
    if (this.isRunning) {
      log.warn('Orchestrator tick overlapped—skipping cycle.');
      return;
    }
    
    this.isRunning = true;

    try {
      log.info('--- Engine Tick Start ---');
      
      const orders = await exchangeService.fetchConcurrentP2POrders();
      const ads = await exchangeService.fetchConcurrentP2PAds();

      log.info(`Pinged CCXT Matrix. Active Orders: ${orders.length} | Scraped Ads: ${ads.length}`);
      
      // Compute intelligent Arbitrage bounds over the new metrics
      const newSpread = await pricingEngineService.computeTargetSellPrice();
      if (newSpread) {
         log.info(`Arbitrage Spread Locked. Rebalancing Target SELL => €${newSpread}`);
      }

    } catch (error) {
      log.error('Fatal failure in P2P Orchestrator loop', { error });
    } finally {
      this.isRunning = false;
    }
  }
}

export const orchestratorWorker = new P2POrchestratorWorker();
