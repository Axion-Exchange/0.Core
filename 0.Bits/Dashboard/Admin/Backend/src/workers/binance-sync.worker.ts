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

  private async processTick() {
    if (this.isRunning) return;
    this.isRunning = true;

    try {
      // 1. Ask Binance CCXT service for the latest raw 100 orders
      if (!binanceService['enabled']) {
        this.isRunning = false;
        return;
      }
      
      const response: any = await (binanceService as any).client.sapiGetC2cOrderMatchListUserOrderHistory();
      if (!response || !response.data || !Array.isArray(response.data)) {
        this.isRunning = false;
        return;
      }

      const orders = response.data;
      let newOrders = 0;

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
           const names = await binanceService.fetchTrueLegalName(order.orderNumber);
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
            const chatLog = await binanceService.fetchChatMessages(order.orderNumber);
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

      if (newOrders > 0) {
        log.info(`Archived ${newOrders} raw Binance orders successfully to PostgreSQL.`);
      }

    } catch (err: any) {
      log.error(`Binance sync iteration failed:`, err.message);
    } finally {
      this.isRunning = false;
    }
  }
}

export const binanceSyncWorker = new BinanceSyncWorker();
