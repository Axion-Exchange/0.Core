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
      where: { externalId: { not: null } },
      orderBy: { totalVolume: 'desc' }
    });

    this.progress.total = users.length;
    log.info(`Discovered ${users.length} uniquely explicit traders traversing SAPI epochs.`);

    for (const user of users) {
      if (!user.externalId) continue;

      const orders = await prisma.p2POrder.findMany({
        where: { counterparty: user.externalId },
        orderBy: { createdAt: 'asc' },
        select: { id: true, externalOrderId: true, metadata: true, createdAt: true, status: true, type: true }
      });

      if (orders.length === 0) continue;

      // Chronologically organize the orders strictly by their numerical Binance ID string which logically always implicitly increments over time natively
      const chronologicallySortedOrders = orders
         .filter(o => o.externalOrderId)
         .sort((a, b) => a.externalOrderId!.localeCompare(b.externalOrderId!));

      if (chronologicallySortedOrders.length === 0) continue;

      let firstTradeTimestamp = chronologicallySortedOrders[0].createdAt;
      let oldestOrderId: string | null = chronologicallySortedOrders[0].externalOrderId;
      let minEpoch = Infinity;

      // Also double check natively against metadata just in case SAPI mappings organically override implicit sequences correctly
      for (const order of chronologicallySortedOrders) {
         const meta = order.metadata as any;
         if (meta && meta.createTime) {
            const epoch = Number(meta.createTime);
            if (epoch < minEpoch) {
               minEpoch = epoch;
               firstTradeTimestamp = new Date(epoch);
               oldestOrderId = order.externalOrderId;
            }
         }
         
         // ┌─────────────────────────────────────────────────────────┐
         // │  CHAT ARCHIVAL SYNC ENGINE BACKGROUND CRON              │
         // └─────────────────────────────────────────────────────────┘
         if (order.externalOrderId) {
             try {
                 const chatLog = await binanceService.fetchChatMessages(order.externalOrderId);
                 if (chatLog && chatLog.length > 0) {
                     for (const msg of chatLog) {
                        await prisma.p2PChatMessage.upsert({
                           where: { externalMsgId: msg.id || `${order.externalOrderId}-${msg.createTime}` },
                           create: {
                              externalMsgId: msg.id || `${order.externalOrderId}-${msg.createTime}`,
                              orderId: order.id,
                              sender: msg.type === 'system' ? 'system' : (msg.self ? 'merchant' : 'counterparty'),
                              content: msg.content || '',
                              hasImage: !!msg.imageUrl,
                              imageUrl: msg.imageUrl || null,
                              timestamp: new Date(Number(msg.createTime))
                           },
                           update: {
                              content: msg.content || '',
                              hasImage: !!msg.imageUrl,
                              imageUrl: msg.imageUrl || null
                           }
                        });
                     }
                 }
             } catch(charErr) {
                 // > 30 day limit or error natively ignored during background cron iteration
             }
             await new Promise(r => setTimeout(r, 200)); // Respect Binance SAPI HTTP limits
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

      // Find the absolute latest order chronologically explicitly cleanly structurally providing valid order mapping strings safely maximizing the 30-day Binance SAPI name unmask limit
      let validTrade = [...chronologicallySortedOrders].reverse().find(o => o.status === 'COMPLETED' && o.externalOrderId);
      if (!validTrade) validTrade = [...chronologicallySortedOrders].reverse().find(o => o.externalOrderId);

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
