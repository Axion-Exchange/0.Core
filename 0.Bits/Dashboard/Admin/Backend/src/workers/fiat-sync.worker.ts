import { prisma } from '../lib/db.js';
import { fiatService } from '../services/fiat.service.js';
import { createLogger } from '../lib/logger.js';
import { TransactionStatus, TransactionType } from '@prisma/client';

const log = createLogger('fiat-sync-worker');

class FiatSyncWorker {
  private intervalId?: NodeJS.Timeout;
  private isRunning = false;

  public start(intervalMs: number = 30000) {
    log.info(`Booting Institutional Bank Sync Worker [rate: ${intervalMs}ms]...`);
    this.processTick(); // Initial run
    this.intervalId = setInterval(() => this.processTick(), intervalMs);
  }

  public stop() {
    if (this.intervalId) clearInterval(this.intervalId);
    log.info('Institutional Bank Sync Worker halted.');
  }

  private async processTick() {
    if (this.isRunning) return;
    this.isRunning = true;

    try {
      // 1. Fetch live balances
      const balances = await fiatService.getAllBalances();
      
      for (const bal of balances) {
        // Upsert fiat ledger safely
        await prisma.fiatLedger.upsert({
          where: { 
            // Workaround for composite keys if they do not exist
            id: bal.accountId 
          },
          create: {
             id: bal.accountId,
             currency: bal.currency,
             balance: bal.balance,
             source: bal.provider,
             lastSyncAt: new Date()
          },
          update: {
             balance: bal.balance,
             lastSyncAt: new Date()
          }
        }).catch(async (e) => {
          // If ID constraint fails, findFirst and update logic
          const existing = await prisma.fiatLedger.findFirst({
            where: { source: bal.provider, currency: bal.currency }
          });
          if (existing) {
             await prisma.fiatLedger.update({
               where: { id: existing.id },
               data: { balance: bal.balance, lastSyncAt: new Date() }
             });
          } else {
             await prisma.fiatLedger.create({
               data: { currency: bal.currency, balance: bal.balance, source: bal.provider, lastSyncAt: new Date() }
             });
          }
        });
      }

      // 2. Fetch live transactions to preserve maximum information 
      const rawTransactions = await fiatService.getRecentTransactions();
      let importedCount = 0;

      for (const tx of rawTransactions) {
         // Prevent redundant imports
         const existing = await prisma.transaction.findUnique({
            where: { externalId: tx.externalId }
         });

         if (!existing) {
            await prisma.transaction.create({
               data: {
                  externalId: tx.externalId,
                  type: tx.amount > 0 ? TransactionType.TRANSFER_IN : TransactionType.TRANSFER_OUT,
                  asset: tx.currency,
                  amount: Math.abs(tx.amount),
                  status: TransactionStatus.COMPLETED,
                  source: tx.provider,
                  description: tx.description,
                  metadata: tx.rawPayload, // Maximum information logged
                  completedAt: tx.timestamp,
                  createdAt: tx.timestamp
               }
            });
            importedCount++;
         }
      }

      if (importedCount > 0) {
         log.info(`Ingested ${importedCount} new raw transactions from institutional banks.`);
      }

    } catch (err: any) {
      log.error(`Fiat bank sync iteration failed:`, err.message);
    } finally {
      this.isRunning = false;
    }
  }
}

export const fiatSyncWorker = new FiatSyncWorker();
