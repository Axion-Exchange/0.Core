import { prisma } from '../lib/db.js';
import { binanceService } from '../services/binance.service.js';
import { createLogger } from '../lib/logger.js';
import { CapitalFlowType } from '@prisma/client';

const log = createLogger('capital-flow-sync');

export class CapitalFlowSyncWorker {
  private intervalId?: NodeJS.Timeout;
  private isRunning = false;

  // Poll every 60 seconds to avoid overly aggressive SAPI weight consumption
  public start(intervalMs: number = 60000) {
    log.info(`Booting Binance Capital Flow Sync Worker [rate: ${intervalMs}ms]...`);
    this.processTick();
    this.intervalId = setInterval(() => this.processTick(), intervalMs);
  }

  public stop() {
    if (this.intervalId) clearInterval(this.intervalId);
    log.info('Binance Capital Flow Sync Worker halted.');
  }

  public async run() {
    return this.processTick();
  }

  private async processTick() {
    if (this.isRunning) return;
    this.isRunning = true;

    try {
      const activeAccounts = await prisma.p2PAccount.findMany({
        where: { exchange: 'BINANCE', isActive: true },
      });

      for (const account of activeAccounts) {
        const { enabled, client } = binanceService.getClient(account);
        if (!enabled) continue;

        try {
          // Determine startTime dynamically. Default to 30 days ago if no records exist.
          // For delta updates, look back 1 hour to overlap just in case.
          const lastRecord = await prisma.exchangeCapitalFlow.findFirst({
            where: { accountId: account.id },
            orderBy: { timestamp: 'desc' },
          });

          const startTime = lastRecord 
            ? new Date(lastRecord.timestamp.getTime() - 60 * 60 * 1000).getTime() 
            : new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).getTime();
          
          const endTime = Date.now();

          // 1. Deposits (sapiGetCapitalDepositHisrec)
          // Weight: 1
          const deposits = await client.sapiGetCapitalDepositHisrec({ startTime, endTime });
          for (const d of deposits) {
             await this.upsertFlow({
               accountId: account.id,
               externalId: `dep-${d.txId || d.id}`,
               asset: d.coin,
               amount: parseFloat(d.amount),
               type: CapitalFlowType.DEPOSIT,
               status: d.status === 1 ? 'COMPLETED' : 'PENDING',
               timestamp: new Date(Number(d.insertTime)),
               metadata: d
             });
          }

          // 2. Withdrawals (sapiGetCapitalWithdrawHistory)
          // Weight: 1
          const withdrawals = await client.sapiGetCapitalWithdrawHistory({ startTime, endTime });
          for (const w of withdrawals) {
             await this.upsertFlow({
               accountId: account.id,
               externalId: `wit-${w.id}`,
               asset: w.coin,
               amount: parseFloat(w.amount),
               type: CapitalFlowType.WITHDRAWAL,
               status: w.status === 6 ? 'COMPLETED' : 'PENDING',
               timestamp: new Date(Number(w.applyTime)),
               metadata: w
             });
          }

          // 3. Asset Transfer (Funding <-> Spot) (sapiGetAssetTransfer)
          // Weight: 1
          const transfers = await client.sapiGetAssetTransfer({ type: 'MAIN_FUNDING', startTime, endTime, size: 100 });
          if (transfers && transfers.rows) {
            for (const t of transfers.rows) {
               await this.upsertFlow({
                 accountId: account.id,
                 externalId: `trf-${t.tranId}`,
                 asset: t.asset,
                 amount: parseFloat(t.amount),
                 type: CapitalFlowType.INTERNAL_TRANSFER,
                 status: t.status,
                 timestamp: new Date(Number(t.timestamp)),
                 metadata: t
               });
            }
          }

          // Reverse transfers (Funding to Main)
          const transfersRev = await client.sapiGetAssetTransfer({ type: 'FUNDING_MAIN', startTime, endTime, size: 100 });
          if (transfersRev && transfersRev.rows) {
            for (const t of transfersRev.rows) {
               await this.upsertFlow({
                 accountId: account.id,
                 externalId: `trf-rev-${t.tranId}`,
                 asset: t.asset,
                 amount: parseFloat(t.amount),
                 type: CapitalFlowType.INTERNAL_TRANSFER,
                 status: t.status,
                 timestamp: new Date(Number(t.timestamp)),
                 metadata: t
               });
            }
          }

          // 4. Convert Trade Flow (sapiGetConvertTradeFlow)
          // Weight: 3000 (VERY EXPENSIVE)
          // Binance only allows pulling max 30 days. We MUST be careful.
          const convertStartTime = new Date(Date.now() - 29 * 24 * 60 * 60 * 1000).getTime();
          const convertTime = Math.max(startTime, convertStartTime);
          const conversions = await client.sapiGetConvertTradeFlow({ startTime: convertTime, endTime });
          if (conversions && conversions.list) {
            for (const c of conversions.list) {
               await this.upsertFlow({
                 accountId: account.id,
                 externalId: `cnv-${c.quoteId}`,
                 asset: c.toAsset,
                 amount: parseFloat(c.toAmount),
                 type: CapitalFlowType.CONVERSION,
                 status: c.orderStatus,
                 timestamp: new Date(Number(c.createTime)),
                 metadata: c
               });
            }
          }

        } catch (err: any) {
          log.error(`[CapitalFlowWorker] Failed to sync account ${account.label}: ${err.message}`);
        }
      }

    } catch (err: any) {
      log.error(`Capital Flow sync iteration failed:`, err.message);
    } finally {
      this.isRunning = false;
    }
  }

  private async upsertFlow(data: {
    accountId: string;
    externalId: string;
    asset: string;
    amount: number;
    type: CapitalFlowType;
    status: string;
    timestamp: Date;
    metadata: any;
  }) {
    await prisma.exchangeCapitalFlow.upsert({
      where: { externalId: data.externalId },
      create: data,
      update: {
        status: data.status,
      }
    });
  }
}

export const capitalFlowSyncWorker = new CapitalFlowSyncWorker();
