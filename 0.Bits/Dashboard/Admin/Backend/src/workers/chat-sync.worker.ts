import { PrismaClient, OrderStatus } from '@prisma/client';
import { binanceService } from '../services/binance.service.js';
import { log } from '../lib/logger.js';

const prisma = new PrismaClient();

export class ChatSyncWorker {
  private isRunning = false;
  private intervalId: NodeJS.Timeout | null = null;

  start() {
    if (this.intervalId) return;
    log.info('[Chat Sync Worker] Initialized 60-second polling for active order communications.');
    // Run exactly every 60 seconds (1 minute)
    this.intervalId = setInterval(() => this.run(), 60000);
    // Execute immediately on boot
    this.run();
  }

  stop() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
      log.info('[Chat Sync Worker] Polling halted.');
    }
  }

  async run() {
    if (this.isRunning) return;
    this.isRunning = true;

    try {
      // 1. Fetch only ACTIVE orders that could legitimately have ongoing chats.
      const activeOrders = await prisma.p2POrder.findMany({
        where: {
          status: {
            in: [OrderStatus.PENDING_FIAT, OrderStatus.FIAT_RECEIVED, OrderStatus.PENDING_RELEASE, OrderStatus.APPEALING],
          },
        },
      });

      if (activeOrders.length === 0) {
        this.isRunning = false;
        return; // Nothing to poll, peacefully exit to save API limits
      }

      let syncedMessagesCount = 0;

      // 2. Poll chats for each natively
      for (const order of activeOrders) {
        if (!order.externalOrderId) continue;

        try {
          const chats = await binanceService.fetchChatMessages(order.externalOrderId);
          
          if (!Array.isArray(chats)) continue;

          for (const chat of chats) {
            if (!chat.messageId) continue;
            
            // Systematically map the generic chat payload natively
            // Upsert guarantees we don't duplicate existing messages!
            await prisma.p2PChatMessage.upsert({
              where: { externalMsgId: chat.messageId },
              create: {
                orderId: order.id,
                externalMsgId: chat.messageId,
                sender: chat.messageSource === 'SYSTEM' ? 'system' : (chat.senderNo === order.userId ? 'buyer' : 'seller'), // Basic heuristic, refine natively if needed
                content: chat.content || '',
                hasImage: chat.type === 'IMAGE',
                imageUrl: chat.type === 'IMAGE' ? chat.messageUrl : null,
                timestamp: new Date(chat.createTime),
              },
              update: {} // No update needed, chats are practically immutable
            });
            syncedMessagesCount++;
          }
          
          // Secure 500ms delay to respect Binance SAPI WAF limits
          await new Promise(resolve => setTimeout(resolve, 500));
        } catch (pollErr: any) {
          log.warn(`[Chat Sync Worker] Failed to correctly poll chat specifically for order ${order.externalOrderId}: ${pollErr.message}`);
        }
      }

      if (syncedMessagesCount > 0) {
        log.info(`[Chat Sync Worker] Organically absorbed ${syncedMessagesCount} new messages directly into Database.`);
      }

    } catch (err: any) {
      log.error(`[Chat Sync Worker] Global iteration failure: ${err.message}`);
    } finally {
      this.isRunning = false;
    }
  }
}

export const chatSyncWorker = new ChatSyncWorker();
