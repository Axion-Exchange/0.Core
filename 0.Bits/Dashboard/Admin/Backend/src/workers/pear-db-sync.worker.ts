import Database from 'better-sqlite3';
import * as path from 'path';
import fs from 'fs';
import { prisma, checkDatabaseHealth } from '../lib/db.js';
import { createLogger } from '../lib/logger.js';
import { getSocket } from '../lib/socket.js';
import { AdType, OrderStatus } from '@prisma/client';

const log = createLogger('pear-db-sync');

export class PearDbSyncWorker {
  private intervalId: NodeJS.Timeout | null = null;
  private isRunning = false;
  private readonly dbPath: string;

  constructor() {
    this.dbPath = path.resolve(process.cwd(), 'p2p-engine/data/orders.db');
  }

  public start(intervalMs = 30000) {
    if (this.intervalId) return;
    log.info(`Booting PearV2 DB Sync DAEMON [rate: ${intervalMs}ms] bridging SQLite to Postgres...`);
    this.intervalId = setInterval(() => this.run(), intervalMs);
    // Execute immediately
    this.run();
  }

  public stop() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
      log.info('PearV2 DB Sync halted.');
    }
  }

  async run() {
    if (this.isRunning) return;
    this.isRunning = true;

    try {
      if (!fs.existsSync(this.dbPath)) {
        log.warn('PearV2 orders.db safely ignored (Python daemon has not created it yet).');
        return;
      }
      
      const pgHealthy = await checkDatabaseHealth();
      if (!pgHealthy) {
          log.warn('Skipping SQlite sync -> Postgres is unhealthy.');
          return;
      }
      
      // Connect specifically in readonly safe mode preventing locks
      const sqldb = new Database(this.dbPath, { readonly: true });
      
      // Pull only completed and cancelled trades for heavy dashboard metrics 
      // (Pending trades fluctuate too much for 30s bridging loops over huge structures)
      const rows = sqldb.prepare(`
        SELECT external_id, state, order_data, created_at, updated_at 
        FROM orders 
        WHERE state IN ('completed', 'cancelled')
      `).all() as any[];
      
      sqldb.close();

      let upsertCount = 0;

      // Pipe mappings straight directly into Prisma
      for (const row of rows) {
        let parsedPayload: any = {};
        try {
            parsedPayload = JSON.parse(row.order_data);
        } catch(e) { continue; }

        const mappedStatus = this.mapStatus(row.state);
        const mappedType = parsedPayload.side?.toUpperCase() === 'BUY' ? AdType.BUY : AdType.SELL;
        
        await prisma.p2POrder.upsert({
          where: { externalOrderId: row.external_id },
          update: {
            status: mappedStatus,
            metadata: parsedPayload,
          },
          create: {
            externalOrderId: row.external_id,
            asset: parsedPayload.crypto_currency || 'USDT',
            amount: parseFloat(parsedPayload.crypto_amount || '0'),
            fiat: parsedPayload.fiat_currency || 'EUR',
            fiatAmount: parseFloat(parsedPayload.fiat_amount || '0'),
            price: parseFloat(parsedPayload.price || '0'),
            fee: 0,
            type: mappedType,
            status: mappedStatus,
            metadata: parsedPayload,
            createdAt: new Date(row.created_at || Date.now()),
            updatedAt: new Date(row.updated_at || Date.now())
          }
        });
        
        upsertCount++;
      }

      if (upsertCount > 0) {
        log.info(`✅ Synced ${upsertCount} native SQLite records perfectly to Postgres UI bounds.`);
        try {
          getSocket().emit('trade_update', { count: upsertCount, timestamp: Date.now() });
        } catch(e) {
          log.warn('Could not emit socket event (maybe not initialized yet)');
        }
      }

    } catch (error) {
      log.error('Fatal Failure traversing PearV2 DB map', { error });
    } finally {
      this.isRunning = false;
    }
  }

  private mapStatus(pythonState: string): OrderStatus {
    const stateMap: Record<string, OrderStatus> = {
      'completed': OrderStatus.COMPLETED,
      'cancelled': OrderStatus.CANCELLED,
      'expired': OrderStatus.EXPIRED,
      'pending_fiat': OrderStatus.PENDING_FIAT,
      'fiat_received': OrderStatus.FIAT_RECEIVED,
      'pending_release': OrderStatus.PENDING_RELEASE,
      'released': OrderStatus.RELEASED,
      'appealed': OrderStatus.APPEALING
    };
    return stateMap[pythonState.toLowerCase()] || OrderStatus.PENDING_FIAT;
  }
}

export const pearDbSyncWorker = new PearDbSyncWorker();
