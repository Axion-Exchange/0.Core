import { prisma } from '../lib/db.js';
import { binanceService } from '../services/binance.service.js';
import { createLogger } from '../lib/logger.js';
import { AdType, OrderStatus } from '@prisma/client';

const log = createLogger('binance-sync-worker');

class BinanceSyncWorker {
  private intervalId?: NodeJS.Timeout;
  private isRunning = false;

  public start(intervalMs: number = 30000) {
    log.info(`Booting Binance DB Sync Worker [rate: ${intervalMs}ms]...`);
    this.processTick(); // Initial trigger
    this.intervalId = setInterval(() => this.processTick(), intervalMs);
  }

  public stop() {
    if (this.intervalId) clearInterval(this.intervalId);
    log.info('Binance DB Sync Worker halted.');
  }
  /** Single-shot execution for BullMQ job processor */
  public async run() {
    return this.processTick();
  }

  private async processTick() {
    if (this.isRunning) return;
    this.isRunning = true;
    let newOrders = 0;

    try {
      const activeAccounts = await prisma.p2PAccount.findMany({
        where: { exchange: 'BINANCE', isActive: true }
      });
      
      // Fallback: If no accounts in database, try to sync default one from .env natively 
      if (activeAccounts.length === 0) {
        activeAccounts.push({ id: undefined } as any);
      }

      for (const account of activeAccounts) {
        // 1. Ask Binance CCXT service for the latest raw 100 orders
        const { enabled, client } = binanceService.getClient(account.id ? account : undefined);
        if (!enabled || !client) {
          log.warn(`Binance client disabled or missing for account ${account.id || 'default'}`);
          continue;
        }
        
        let response: any;
        try {
          response = await client.sapiGetC2cOrderMatchListUserOrderHistory();
        } catch (e: any) {
          log.error(`Failed to fetch orders for account ${account.id || 'default'}: ${e.message}`);
          continue;
        }

        if (!response || !response.data || !Array.isArray(response.data)) {
          continue;
        }

        const orders = response.data;

        // 2. Iterate backwards (to process oldest first organically) or simply upsert all safely
        for (const order of orders) {
        // Evaluate native params
        // Binance orderStatus mappings: COMPLETED, CANCELLED, PENDING, etc
        let mappedStatus: OrderStatus = OrderStatus.PENDING_FIAT;
        if (order.orderStatus === 'COMPLETED') mappedStatus = OrderStatus.COMPLETED;
        else if (order.orderStatus === 'CANCELLED' || order.orderStatus === 'CANCELLED_BY_SYSTEM') mappedStatus = OrderStatus.CANCELLED;

        const cryptoAmount = parseFloat(order.amount) || 0;
        const fiatAmount = parseFloat(order.totalPrice) || 0;
        const createTime = new Date(Number(order.createTime)); // Fix to UNIX epoch

        // Check if we already mapped this order securely beforehand to avoid 429 rate limit spamming
        const existingRecord = await prisma.p2POrder.findUnique({
          where: { externalOrderId: order.orderNumber }
        });

        let counterpartyNameStr = existingRecord?.counterpartyName;

        // Extract native Binance Legal Identities dynamically on missed records
        if (!counterpartyNameStr && mappedStatus === OrderStatus.COMPLETED) {
           const names = await binanceService.fetchTrueLegalName(order.orderNumber, account.id ? account : undefined);
           if (names) {
              // Priority map to the valid side
              counterpartyNameStr = order.tradeType === 'BUY' ? names.sellerName : names.buyerName;
           }
        }

        // Safely extract the pseudonym intelligently. 
        // If we extracted a True Legal Name dynamically off SAPI (-1000 bypassing), we FORCE that specific absolute Real Identity cleanly to naturally natively intrinsically group 100% of historical identical users gracefully!
        // If not, we physically isolate the identity utilizing the Order ID to prevent massive generic False Aggregation correctly!
        const rawNickname = order.counterPartNickName || 'Binance P2P User';
        let counterpartyNickname = rawNickname;
        if (counterpartyNameStr) {
            // Group aggressively uniquely by real biological name universally
            counterpartyNickname = counterpartyNameStr;
        } else if (rawNickname.includes('***')) {
            // Physically mathematically computationally isolate gracefully if unmasked failed due to >30d expiry elegantly
            counterpartyNickname = `${rawNickname}-${order.orderNumber}`;
        }
        
        let userNodeId: string | undefined = existingRecord?.userId || undefined;

        // Mathematically inject user aggregation precisely only on new distinct mutations safely
        if (!existingRecord) {
           const userNode = await prisma.user.upsert({
             where: { externalId: counterpartyNickname },
             create: {
               externalId: counterpartyNickname,
               displayName: counterpartyNameStr ? counterpartyNameStr : rawNickname,
               legalName: counterpartyNameStr || null,
               totalVolume: mappedStatus === OrderStatus.COMPLETED ? cryptoAmount : 0,
               totalTrades: mappedStatus === OrderStatus.COMPLETED ? 1 : 0
             },
             update: {
               ...(counterpartyNameStr ? { legalName: counterpartyNameStr, displayName: counterpartyNameStr } : {}),
               ...(mappedStatus === OrderStatus.COMPLETED ? {
                  totalVolume: { increment: cryptoAmount },
                  totalTrades: { increment: 1 }
               } : {})
             }
          });
          userNodeId = userNode.id;
        } else if (mappedStatus === OrderStatus.COMPLETED && existingRecord.status !== OrderStatus.COMPLETED) {
           const userNode = await prisma.user.update({
             where: { externalId: counterpartyNickname },
             data: {
                ...(counterpartyNameStr ? { legalName: counterpartyNameStr, displayName: counterpartyNameStr } : {}),
                totalVolume: { increment: cryptoAmount },
                totalTrades: { increment: 1 }
             }
           });
           userNodeId = userNode.id;
        } else if (counterpartyNameStr && !existingRecord.counterpartyName) {
           const userNode = await prisma.user.upsert({
             where: { externalId: counterpartyNickname },
             create: {
               externalId: counterpartyNickname,
               displayName: counterpartyNameStr,
               legalName: counterpartyNameStr,
               totalVolume: mappedStatus === OrderStatus.COMPLETED ? cryptoAmount : 0,
               totalTrades: mappedStatus === OrderStatus.COMPLETED ? 1 : 0
             },
             update: { 
               legalName: counterpartyNameStr,
               displayName: counterpartyNameStr
             }
           });
           userNodeId = userNode.id;
        }

        // Upsert into Database (ExternalOrderId enforces uniqueness)
        const orderNode = await prisma.p2POrder.upsert({
          where: { externalOrderId: order.orderNumber },
          create: {
            externalOrderId: order.orderNumber,
            userId: userNodeId,
            accountId: account.id || null, // INJECT ACCOUNT ID
            asset: order.asset, // 'USDT'
            fiat: order.fiat, // 'EUR'
            amount: cryptoAmount, 
            fiatAmount: fiatAmount,
            price: parseFloat(order.unitPrice) || 0,
            type: order.tradeType === 'BUY' ? AdType.BUY : AdType.SELL, // Their API matches our generic BUY/SELL ENUM
            counterparty: counterpartyNickname,
            counterpartyName: counterpartyNameStr, // Natively write the true identity map!
            paymentMethod: order.payMethodName,
            status: mappedStatus,
            createdAt: createTime,
            completedAt: mappedStatus === OrderStatus.COMPLETED ? new Date() : null, // Not strictly 100% accurate unless parsed from binance updates, but sufficient
            metadata: order, // DUMP FULL NATIVE RESPONSE FOR INSTITUTIONAL AUDITING
          },
          update: {
            userId: userNodeId, // Retain rigid map consistently uniquely!
            accountId: account.id || null, // RETAIN ACCOUNT ID
            status: mappedStatus,
            counterparty: counterpartyNickname, // Overwrite dynamically if Real Name unlocked successfully natively
            counterpartyName: counterpartyNameStr, // Inject dynamically onto existing backwards-synced trades
            metadata: order, // Continually refresh logs if changes happened natively (e.g. disputes)
          }
        });

        // ┌─────────────────────────────────────────────────────────┐
        // │  CHAT ARCHIVAL SYNC ENGINE NATIVELY BIND TO POSTGRES    │
        // └─────────────────────────────────────────────────────────┘
        // Bypass the rigid 30-day loop where organically available.
        try {
            const chatLog = await binanceService.fetchChatMessages(order.orderNumber, account.id ? account : undefined);
            if (chatLog && chatLog.length > 0) {
               for (const msg of chatLog) {
                  await prisma.p2PChatMessage.upsert({
                     where: { externalMsgId: msg.id || `${order.orderNumber}-${msg.createTime}` },
                     create: {
                        externalMsgId: msg.id || `${order.orderNumber}-${msg.createTime}`,
                        orderId: orderNode.id,
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
               log.info(`Archived ${chatLog.length} deep chat transcripts automatically mapped natively to Order: ${order.orderNumber}`);
            }
        } catch (charErr: any) {
            log.warn(`Chat synchronization failed for Order ${order.orderNumber} - Likely SAPI expiry limitations natively handled.`, charErr.message);
        }

        newOrders++;
      }
      
      // End of inner account loop
      }

      if (newOrders > 0) {
        log.info(`Archived ${newOrders} raw Binance orders successfully to PostgreSQL.`);
      }

    } catch (err: any) {
      console.error(`!!! RAW BINANCE SYNC ERROR !!!`, err);
      log.error(`Binance sync iteration failed:`, err?.stack || err);
    } finally {
      this.isRunning = false;
      // Run stale order reconciliation after sync (throttled to every 10th tick)
      this.reconcileStaleOrders().catch(e => log.warn('Reconciliation error:', e.message));
      // Sync advertisements from Binance (throttled to every 5th tick ~2.5 min)
      this.syncAdvertisements().catch(e => log.warn('Ad sync error:', e.message));
    }
  }

  /**
   * Sync merchant advertisements from all active Binance accounts.
   * Pulls live ad configs from SAPI and upserts into P2PAdvertisement.
   * Runs every 5th tick (~2.5 minutes at 30s intervals).
   */
  private adSyncTickCount = 0;
  private async syncAdvertisements() {
    this.adSyncTickCount++;
    if (this.adSyncTickCount % 5 !== 0) return;

    try {
      const activeAccounts = await prisma.p2PAccount.findMany({
        where: { exchange: 'BINANCE', isActive: true }
      });

      if (activeAccounts.length === 0) return;

      let totalSynced = 0;

      for (const account of activeAccounts) {
        try {
          const ads = await binanceService.fetchMerchantAds(account);
          if (!ads || ads.length === 0) continue;

          for (const ad of ads) {
            const adNo = ad.advNo || ad.adsNo || ad.adNo;
            if (!adNo) continue;

            const statusRaw = (ad.advStatus || ad.status || '').toString().toUpperCase();
            let mappedStatus: 'ACTIVE' | 'PAUSED' = 'PAUSED';
            if (statusRaw === '1' || statusRaw === 'ONLINE' || statusRaw === 'ACTIVE') {
              mappedStatus = 'ACTIVE';
            }

            await prisma.p2PAdvertisement.upsert({
              where: { externalAdId: adNo },
              create: {
                accountId: account.id,
                externalAdId: adNo,
                asset: ad.asset || ad.cryptoCurrency || 'USDT',
                fiat: ad.fiatUnit || ad.fiat || 'EUR',
                type: (ad.tradeType === 'SELL' || ad.advType === 'SELL') ? 'SELL' : 'BUY',
                price: parseFloat(ad.price || ad.advPrice || '0'),
                marginPercent: parseFloat(ad.priceFloatingRatio || ad.marginPercent || '0'),
                minLimit: parseFloat(ad.minSingleTransAmount || ad.minLimit || '0'),
                maxLimit: parseFloat(ad.maxSingleTransAmount || ad.maxLimit || '0'),
                availableQty: parseFloat(ad.surplusAmount || ad.dynamicMaxAmount || ad.availableQty || '0'),
                status: mappedStatus,
                autoReply: ad.autoReplyMsg || null,
                remarks: ad.remarks || null,
                metadata: ad,
              },
              update: {
                price: parseFloat(ad.price || ad.advPrice || '0'),
                marginPercent: parseFloat(ad.priceFloatingRatio || ad.marginPercent || '0'),
                minLimit: parseFloat(ad.minSingleTransAmount || ad.minLimit || '0'),
                maxLimit: parseFloat(ad.maxSingleTransAmount || ad.maxLimit || '0'),
                availableQty: parseFloat(ad.surplusAmount || ad.dynamicMaxAmount || ad.availableQty || '0'),
                status: mappedStatus,
                autoReply: ad.autoReplyMsg || null,
                remarks: ad.remarks || null,
                metadata: ad,
              },
            });

            totalSynced++;
          }
        } catch (accErr: any) {
          log.warn(`Ad sync failed for account ${account.label}: ${accErr.message}`);
        }
      }

      if (totalSynced > 0) {
        log.info(`[AdSync] Synchronized ${totalSynced} advertisements from ${activeAccounts.length} account(s).`);
      }
    } catch (err: any) {
      log.error(`[AdSync] Global ad sync failed:`, err.message);
    }
  }

  /**
   * Reconcile orders stuck in non-terminal states by re-fetching
   * paginated Binance history. Runs every 10th tick (~5 min).
   */
  private tickCount = 0;
  private async reconcileStaleOrders() {
    this.tickCount++;
    if (this.tickCount % 10 !== 0) return; // Only run every 10th tick

    try {
      // Find orders in non-terminal states older than 1 hour
      const staleOrders = await prisma.p2POrder.findMany({
        where: {
          status: { in: ['PENDING_FIAT', 'FIAT_RECEIVED', 'PENDING_RELEASE'] },
          createdAt: { lt: new Date(Date.now() - 60 * 60 * 1000) },
        },
        select: { externalOrderId: true },
        take: 200,
      });

      if (staleOrders.length === 0) return;

      const staleIds = new Set(staleOrders.map((o: any) => o.externalOrderId).filter(Boolean));
      log.info(`Reconciling ${staleIds.size} stale pending orders...`);

      // Fetch up to 5 pages of Binance history to find updated statuses
      for (let page = 1; page <= 5; page++) {
        try {
          const response: any = await (binanceService as any).client.sapiGetC2cOrderMatchListUserOrderHistory({ page, rows: 100 });
          if (!response?.data?.length) break;

          for (const order of response.data) {
            if (!staleIds.has(order.orderNumber)) continue;

            let newStatus: OrderStatus | null = null;
            if (order.orderStatus === 'COMPLETED') newStatus = OrderStatus.COMPLETED;
            else if (order.orderStatus === 'CANCELLED' || order.orderStatus === 'CANCELLED_BY_SYSTEM') newStatus = OrderStatus.CANCELLED;

            if (newStatus) {
              await prisma.p2POrder.update({
                where: { externalOrderId: order.orderNumber },
                data: {
                  status: newStatus,
                  ...(newStatus === OrderStatus.COMPLETED ? { completedAt: new Date() } : {}),
                },
              });
              staleIds.delete(order.orderNumber);
              log.info(`Reconciled ${order.orderNumber} → ${newStatus}`);
            }
          }

          if (staleIds.size === 0) break;
        } catch (pageErr: any) {
          log.warn(`Reconciliation page ${page} failed: ${pageErr.message}`);
          break;
        }
      }
    } catch (err: any) {
      log.error(`Stale order reconciliation failed:`, err.message);
    }
  }
}

export const binanceSyncWorker = new BinanceSyncWorker();
