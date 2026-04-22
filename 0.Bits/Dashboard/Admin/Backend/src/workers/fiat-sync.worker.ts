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
      // 1. Fetch live balances from all rails
      const balances = await fiatService.getAllBalances();
      
      for (const bal of balances) {
        // Upsert fiat ledger safely (existing behavior — backward compat)
        await prisma.fiatLedger.upsert({
          where: { 
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

        // ──────────────────────────────────────────────────────
        // NEW: Append-only balance snapshot into balance_ledger
        // Each tick creates a NEW ROW — never updates/deletes.
        // ──────────────────────────────────────────────────────
        
        // Calculate pending (escrowed P2P orders) for this currency
        const escrowAgg = await prisma.p2POrder.aggregate({
          where: {
            fiat: bal.currency,
            status: { in: ['PENDING_FIAT', 'FIAT_RECEIVED', 'PENDING_RELEASE', 'APPEALING'] },
          },
          _sum: { fiatAmount: true },
        });
        const pendingAmount = Number(escrowAgg._sum.fiatAmount || 0);

        await prisma.balanceLedger.create({
          data: {
            source: bal.provider,
            currency: bal.currency,
            available: bal.balance,
            pending: pendingAmount,
            metadata: { rawBalance: bal.balance, provider: bal.provider },
            snapshotAt: new Date(),
          }
        });
      }

      // 2. Fetch live transactions to preserve maximum information 
      const rawTransactions = await fiatService.getRecentTransactions();
      let importedCount = 0;

      for (const tx of rawTransactions) {
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
                  metadata: tx.rawPayload,
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
