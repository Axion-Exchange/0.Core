import { createLogger } from '../lib/logger.js';
import { kycOrchestrator } from '../services/kyc-orchestrator.service.js';

const log = createLogger('kyc-sync');

/**
 * KYC Sync Worker — Polls Didit providers every 30 seconds.
 * 
 * Pipeline per tick:
 *   1. syncAllProviders()        — Pull latest sessions from all Didit apps
 *   2. matchAllSessions()        — Match new unmatched sessions to users (PearV2)
 *   3. propagateStatusChanges()  — Update user kycStatus if Didit status changed
 * 
 * This catches:
 *   - New KYC verifications completing
 *   - Manual approvals/declines on Didit console
 *   - KYC expirations
 *   - Status transitions (IN_REVIEW → APPROVED, etc.)
 */
export class KycSyncWorker {
  private isRunning = false;
  private intervalId: NodeJS.Timeout | null = null;
  private pollInterval: number;
  private tickCount = 0;

  constructor(pollIntervalMs = 30000) {
    this.pollInterval = pollIntervalMs;
  }

  start(intervalMs?: number) {
    if (this.intervalId) return;
    const interval = intervalMs || this.pollInterval;
    log.info(`[KYC Sync] Initialized ${interval / 1000}s polling for KYC status updates.`);
    this.intervalId = setInterval(() => this.run(), interval);
    // First run after 10s delay (let other workers initialize first)
    setTimeout(() => this.run(), 10000);
  }

  stop() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
      log.info('[KYC Sync] Polling halted.');
    }
  }

  async run() {
    if (this.isRunning) return;
    this.isRunning = true;
    this.tickCount++;

    try {
      // Sync sessions from all Didit apps
      const syncResult = await kycOrchestrator.syncAllProviders();

      // Only run matching + propagation every 2nd tick (every 60s) to reduce DB load
      // Status propagation runs every tick (every 30s) for fast reaction
      const statusResult = await kycOrchestrator.propagateStatusChanges();

      if (statusResult.updated > 0) {
        log.info(`[KYC Sync] ${statusResult.updated} status changes propagated:`);
        for (const change of statusResult.changes) {
          log.info(`  ${change.user}: ${change.from} → ${change.to}`);
        }
      }

      // Run matching every 2nd tick to avoid hammering DB
      if (this.tickCount % 2 === 0) {
        const matchResult = await kycOrchestrator.matchAllSessions();
        if (matchResult.matched > 0) {
          log.info(`[KYC Sync] New matches: ${matchResult.matched} (${matchResult.approved} approved, ${matchResult.declined} declined)`);
        }
      }

    } catch (err: any) {
      log.error(`[KYC Sync] Tick failed: ${err.message}`);
    } finally {
      this.isRunning = false;
    }
  }
}

export const kycSyncWorker = new KycSyncWorker();
