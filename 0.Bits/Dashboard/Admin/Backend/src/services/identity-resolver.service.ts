import { prisma } from '../lib/db.js';
import { binanceService } from '../services/binance.service.js';
import { createLogger } from '../lib/logger.js';
import { AdType, OrderStatus } from '@prisma/client';

const log = createLogger('identity-resolver');

/**
 * Identity Resolver Service
 * 
 * Iterates through ALL Binance P2P orders (BUY + SELL, all statuses including cancelled),
 * calls getUserOrderDetail for each to extract the real legal name, then rebuilds the
 * user aggregation graph from scratch with correct identity mapping.
 */
class IdentityResolverService {
  private isRunning = false;
  private progress = { total: 0, resolved: 0, failed: 0, skipped: 0, text: 'Idle' };

  public getStatus() {
    return { isRunning: this.isRunning, progress: { ...this.progress } };
  }

  public async triggerFullResolution() {
    if (this.isRunning) {
      log.warn('[IdentityResolver] Already running, skipping.');
      return false;
    }

    this.isRunning = true;
    this.progress = { total: 0, resolved: 0, failed: 0, skipped: 0, text: 'Starting full identity resolution...' };

    this.executeResolution().catch(e => {
      log.error('[IdentityResolver] Fatal error:', e);
    }).finally(() => {
      this.isRunning = false;
    });

    return true;
  }

  private async executeResolution() {
    // Phase 1: Fetch ALL orders from Binance API (paginated)
    log.info('[IdentityResolver] Phase 1: Fetching all orders from Binance...');
    const allOrders = await this.fetchAllBinanceOrders();
    this.progress.total = allOrders.length;
    log.info(`[IdentityResolver] Fetched ${allOrders.length} total orders from Binance.`);

    // Phase 2: For each order, resolve identity via getUserOrderDetail
    log.info('[IdentityResolver] Phase 2: Resolving identities for all orders...');
    
    for (let i = 0; i < allOrders.length; i++) {
      const order = allOrders[i];
      const orderNumber = order.orderNumber;

      try {
        // Check if this order already has a real name in the DB
        const existing = await prisma.p2POrder.findUnique({
          where: { externalOrderId: orderNumber },
          select: { counterpartyName: true }
        });

        if (existing?.counterpartyName && !existing.counterpartyName.includes('***')) {
          this.progress.skipped++;
          if (this.progress.skipped % 50 === 0) {
            log.info(`[IdentityResolver] Skipped ${this.progress.skipped} already-resolved orders...`);
          }
          continue;
        }

        // Call getUserOrderDetail to get real names
        const detail = await binanceService.fetchTrueLegalName(orderNumber);
        
        if (!detail) {
          this.progress.failed++;
          log.warn(`[IdentityResolver] Failed to resolve order ${orderNumber}`);
          await this.rateLimit(300);
          continue;
        }

        // Determine counterparty name based on trade direction
        // If we are buying, the counterparty is the seller. If selling, the counterparty is the buyer.
        const counterpartyName = order.tradeType === 'BUY' ? detail.sellerName : detail.buyerName;
        const rawNickname = order.counterPartNickName || 'Unknown';

        if (!counterpartyName) {
          this.progress.failed++;
          log.warn(`[IdentityResolver] No counterparty name for order ${orderNumber} (trade type: ${order.tradeType})`);
          await this.rateLimit(300);
          continue;
        }

        // Map order status
        let mappedStatus: OrderStatus = OrderStatus.PENDING_FIAT;
        if (order.orderStatus === 'COMPLETED') mappedStatus = OrderStatus.COMPLETED;
        else if (order.orderStatus === 'CANCELLED' || order.orderStatus === 'CANCELLED_BY_SYSTEM') mappedStatus = OrderStatus.CANCELLED;
        else if (order.orderStatus === 'BUYER_PAYED') mappedStatus = OrderStatus.FIAT_RECEIVED;

        const cryptoAmount = parseFloat(order.amount) || 0;
        const fiatAmount = parseFloat(order.totalPrice) || 0;
        const createTime = new Date(Number(order.createTime));

        // Phase 3: Upsert User by REAL legal name (not pseudonym)
        const userNode = await prisma.user.upsert({
          where: { externalId: counterpartyName },
          create: {
            externalId: counterpartyName,
            displayName: counterpartyName,
            legalName: counterpartyName,
            totalVolume: mappedStatus === OrderStatus.COMPLETED ? cryptoAmount : 0,
            totalTrades: mappedStatus === OrderStatus.COMPLETED ? 1 : 0,
          },
          update: {
            legalName: counterpartyName,
            displayName: counterpartyName,
          }
        });

        // Phase 4: Upsert Order with real identity
        await prisma.p2POrder.upsert({
          where: { externalOrderId: orderNumber },
          create: {
            externalOrderId: orderNumber,
            userId: userNode.id,
            asset: order.asset || 'USDT',
            fiat: order.fiat || 'EUR',
            amount: cryptoAmount,
            fiatAmount: fiatAmount,
            price: parseFloat(order.unitPrice) || 0,
            type: order.tradeType === 'BUY' ? AdType.BUY : AdType.SELL,
            counterparty: counterpartyName,
            counterpartyName: counterpartyName,
            paymentMethod: order.payMethodName || null,
            status: mappedStatus,
            createdAt: createTime,
            completedAt: mappedStatus === OrderStatus.COMPLETED ? createTime : null,
            metadata: order,
          },
          update: {
            userId: userNode.id,
            counterparty: counterpartyName,
            counterpartyName: counterpartyName,
            status: mappedStatus,
            metadata: order,
          }
        });

        this.progress.resolved++;

        if (this.progress.resolved % 25 === 0) {
          log.info(`[IdentityResolver] Progress: ${this.progress.resolved}/${this.progress.total} resolved | ${this.progress.failed} failed | ${this.progress.skipped} skipped | Latest: ${counterpartyName}`);
          this.progress.text = `Resolved ${this.progress.resolved}/${this.progress.total} - Latest: ${counterpartyName}`;
        }

        // Rate limit: 300ms between API calls to respect Binance limits
        await this.rateLimit(300);

      } catch (err: any) {
        this.progress.failed++;
        log.error(`[IdentityResolver] Error processing order ${orderNumber}:`, err.message);
        await this.rateLimit(500);
      }
    }

    // Phase 5: Recalculate user volumes from scratch
    log.info('[IdentityResolver] Phase 5: Recalculating user volumes...');
    await this.recalculateUserVolumes();

    // Phase 6: Cleanup orphaned user nodes
    log.info('[IdentityResolver] Phase 6: Cleaning up orphaned users...');
    await this.cleanupOrphanedUsers();

    this.progress.text = `Complete: ${this.progress.resolved} resolved, ${this.progress.failed} failed, ${this.progress.skipped} skipped`;
    log.info(`[IdentityResolver] ${this.progress.text}`);
  }

  /**
   * Fetch ALL orders from Binance history API, paginated (100 per page).
   * Includes both BUY and SELL, all statuses.
   */
  private async fetchAllBinanceOrders(): Promise<any[]> {
    const client = (binanceService as any).client;
    const allOrders: any[] = [];

    for (const tradeType of ['BUY', 'SELL']) {
      let page = 1;
      let hasMore = true;
      let fetchedForType = 0;

      while (hasMore) {
        try {
          const response = await client.request('c2c/orderMatch/listUserOrderHistory', 'sapi', 'GET', {
            tradeType,
            rows: 50,
            page,
          });

          if (!response || !response.data || !Array.isArray(response.data) || response.data.length === 0) {
            hasMore = false;
            break;
          }

          allOrders.push(...response.data);
          fetchedForType += response.data.length;
          
          const total = Number(response.total) || 0;
          log.info(`[IdentityResolver] Fetched page ${page} of ${tradeType}: ${fetchedForType}/${total} orders`);

          // Binance caps at 50 per page. Stop when we've fetched all for this type.
          if (fetchedForType >= total || response.data.length < 50) {
            hasMore = false;
          } else {
            page++;
            await this.rateLimit(200);
          }
        } catch (err: any) {
          log.error(`[IdentityResolver] Error fetching ${tradeType} page ${page}:`, err.message);
          hasMore = false;
        }
      }
    }

    return allOrders;
  }

  /**
   * Recalculate totalVolume and totalTrades for every user based on their linked completed orders.
   */
  private async recalculateUserVolumes() {
    const users = await prisma.user.findMany({ select: { id: true, externalId: true } });
    let updated = 0;

    for (const user of users) {
      const stats = await prisma.p2POrder.aggregate({
        where: { userId: user.id, status: OrderStatus.COMPLETED },
        _sum: { amount: true },
        _count: true,
      });

      await prisma.user.update({
        where: { id: user.id },
        data: {
          totalVolume: stats._sum.amount || 0,
          totalTrades: stats._count,
        }
      });
      updated++;
    }

    log.info(`[IdentityResolver] Recalculated volumes for ${updated} users.`);
  }

  /**
   * Delete user nodes that have zero orders linked to them (orphaned from pseudonym fragmentation).
   */
  private async cleanupOrphanedUsers() {
    const orphans = await prisma.user.findMany({
      where: {
        p2pOrders: { none: {} }
      },
      select: { id: true, externalId: true }
    });

    if (orphans.length > 0) {
      await prisma.user.deleteMany({
        where: { id: { in: orphans.map(o => o.id) } }
      });
      log.info(`[IdentityResolver] Cleaned up ${orphans.length} orphaned user nodes.`);
    }
  }

  private rateLimit(ms: number) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

export const identityResolverService = new IdentityResolverService();
