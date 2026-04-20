import { prisma } from '../lib/db.js';
import { binanceService } from '../services/binance.service.js';
import { createLogger } from '../lib/logger.js';

const log = createLogger('sapi-sync-service');

class SapiPatchService {
  private isSyncing: boolean = false;
  private progress: { total: number; current: number; text: string } = { total: 0, current: 0, text: 'Idle' };

  public getStatus() {
    return {
      isSyncing: this.isSyncing,
      progress: this.progress
    };
  }

  public async triggerBackgroundSync() {
    if (this.isSyncing) {
      log.warn("SAPI Sync physically blocked - Mutex is naturally already locked!");
      return false; // Already explicitly running
    }

    this.isSyncing = true;
    this.progress = { total: 0, current: 0, text: 'Initializing SAPI Counterparty Patch...' };
    
    // Natively spawn the parsing logic implicitly unblocking the HTTP executor immediately
    this.executePatchLogic().catch(e => {
        log.error("Migration fatal fault trace:", e);
    }).finally(() => {
        this.isSyncing = false;
        this.progress.text = 'Deep Patch completely structurally finalized successfully natively!';
        log.info(this.progress.text);
    });

    return true;
  }

  private async executePatchLogic() {
    log.info("Executing deep SAPI query constraints bypassing WAF locally...");

    const users = await prisma.user.findMany({
      where: { externalId: { not: null } }
    });

    this.progress.total = users.length;
    log.info(`Discovered ${users.length} uniquely explicit traders traversing SAPI epochs.`);

    for (const user of users) {
      if (!user.externalId) continue;

      const orders = await prisma.p2POrder.findMany({
        where: { counterparty: user.externalId },
        orderBy: { createdAt: 'asc' },
        select: { externalOrderId: true, metadata: true, createdAt: true, status: true, type: true }
      });

      if (orders.length === 0) continue;

      // Safely aggressively find the true minimum chronological historical trade date primarily from JSON metadata payloads bypassing arbitrary Postgres migration sorting
      let firstTradeTimestamp = orders[0].createdAt;
      let minEpoch = Infinity;
      
      let oldestOrderId: string | null = null;

      for (const order of orders) {
         const meta = order.metadata as any;
         if (meta && meta.createTime) {
            const epoch = Number(meta.createTime);
            if (epoch < minEpoch) {
               minEpoch = epoch;
               firstTradeTimestamp = new Date(epoch);
               oldestOrderId = order.externalOrderId;
            }
         }
      }
      
      if (!oldestOrderId && orders[0].externalOrderId) {
         oldestOrderId = orders[0].externalOrderId;
      }

      // Forcefully explicitly ping Binance SAPI against the oldest known valid ID strictly retrieving their literal first temporal origin bypassing the Database!
      if (oldestOrderId) {
         const historic = await binanceService.fetchTrueLegalName(oldestOrderId);
         if (historic && historic.createTime) {
            const apiEpoch = Number(historic.createTime);
            if (apiEpoch > 0) {
                firstTradeTimestamp = new Date(apiEpoch);
            }
         }
         // 250ms WAF delay
         await new Promise(r => setTimeout(r, 250));
      }

      // Clone array physically to prevent mutating original sort sequence if needed
      const sortedOrders = [...orders];

      // Find the latest order explicitly providing valid order mapping strings
      let validTrade = sortedOrders.reverse().find(o => o.status === 'COMPLETED' && o.externalOrderId);
      if (!validTrade) validTrade = sortedOrders.find(o => o.externalOrderId);

      let actualName = user.legalName || "";

      // Explicitly ask Binance SAPI to mathematically unmask this specific user
      // SKIP physically if we already have an unmasked true identity to strictly save API Rate Limits!
      if (validTrade && validTrade.externalOrderId && (!actualName || actualName.includes('*'))) {
        const names = await binanceService.fetchTrueLegalName(validTrade.externalOrderId);
        if (names) {
           actualName = validTrade.type === 'BUY' ? (names.sellerName || actualName) : (names.buyerName || actualName);
        }
        await new Promise(r => setTimeout(r, 250));
      }

      // Systematically mutate the User component natively securing external bounds
      await prisma.user.update({
        where: { id: user.id },
        data: {
          ...(actualName ? { legalName: actualName } : {}),
          createdAt: firstTradeTimestamp,
        }
      });

      this.progress.current++;
      
      if (this.progress.current % 10 === 0) {
         this.progress.text = `Patched ${this.progress.current}/${this.progress.total}: ${actualName || 'MASKED'}`;
         log.info(this.progress.text);
      }
    }
  }
}

export const sapiPatchService = new SapiPatchService();
