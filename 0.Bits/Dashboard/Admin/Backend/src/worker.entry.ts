/**
 * Worker Entry Point — Standalone BullMQ Job Processor
 * 
 * Doc ref: §Decoupling via Distributed Job Queues (citations 5, 6)
 * "An institutional grade fix mandates the TOTAL SEPARATION of worker processes
 *  from HTTP server processes."
 * 
 * This file runs as a SEPARATE PM2 process from server.ts.
 * It registers all job processors and starts consuming from the queues.
 * 
 * PM2 config:
 *   { name: '0core-workers', script: 'dist/worker.entry.js', instances: 1 }
 */

import 'dotenv/config';
import { createLogger } from './lib/logger.js';
import { createWorker, registerRepeatableJobs, shutdownQueues, QUEUE_NAMES } from './lib/queue.js';
import { disconnectRedis } from './lib/redis.js';
import { disconnectDatabase } from './lib/db.js';

// ── Worker Processors (re-using existing service logic) ──────────────────────
import { exchangeService } from './services/exchange.service.js';
import { pricingEngineService } from './services/intelligence/pricing-engine.service.js';

const log = createLogger('worker-entry');

// ── P2P Orchestrator ─────────────────────────────────────────────────────────
createWorker(QUEUE_NAMES.P2P_ORCHESTRATOR, async (job) => {
  const orders = await exchangeService.fetchConcurrentP2POrders();
  const ads = await exchangeService.fetchConcurrentP2PAds();
  log.info(`[P2P] Pinged CCXT Matrix. Orders: ${orders.length} | Ads: ${ads.length}`);
  
  const newSpread = await pricingEngineService.computeTargetSellPrice();
  if (newSpread) {
    log.info(`[P2P] Arbitrage Spread Locked. SELL => €${newSpread}`);
  }
});

// ── Binance Sync ─────────────────────────────────────────────────────────────
createWorker(QUEUE_NAMES.BINANCE_SYNC, async (job) => {
  // Re-use existing binance-sync logic
  const { binanceSyncWorker } = await import('./workers/binance-sync.worker.js');
  await binanceSyncWorker.run();
});

// ── Chat Sync ────────────────────────────────────────────────────────────────
createWorker(QUEUE_NAMES.CHAT_SYNC, async (job) => {
  const { chatSyncWorker } = await import('./workers/chat-sync.worker.js');
  await chatSyncWorker.run();
});

// ── Fiat Sync ────────────────────────────────────────────────────────────────
createWorker(QUEUE_NAMES.FIAT_SYNC, async (job) => {
  const { fiatSyncWorker } = await import('./workers/fiat-sync.worker.js');
  await fiatSyncWorker.run();
});

// ── Pear DB Sync ─────────────────────────────────────────────────────────────
createWorker(QUEUE_NAMES.PEAR_DB_SYNC, async (job) => {
  const { pearDbSyncWorker } = await import('./workers/pear-db-sync.worker.js');
  await pearDbSyncWorker.run();
});

// ── KYC Sync ─────────────────────────────────────────────────────────────────
createWorker(QUEUE_NAMES.KYC_SYNC, async (job) => {
  const { kycSyncWorker } = await import('./workers/kyc-sync.worker.js');
  await kycSyncWorker.run();
});

// ── Health Check Worker ────────────────────────────────
import { runAllHealthChecks } from "./services/health-checker.service.js";
createWorker(QUEUE_NAMES.HEALTH_CHECK, async () => {
  log.info("[HealthCheck] Running infrastructure probes...");
  const results = await runAllHealthChecks();
  const failures = results.filter((r: any) => r.status !== "healthy");
  if (failures.length > 0) {
    log.warn("[HealthCheck] " + failures.length + " service(s) degraded: " + failures.map((f: any) => f.service).join(", "));
  } else {
    log.info("[HealthCheck] All " + results.length + " services healthy");
  }
});

// ── BigQuery Sync Worker ─────────────────────────────────
createWorker(QUEUE_NAMES.BIGQUERY_SYNC, async () => {
  const { syncToBigQuery } = await import("./services/bigquery-sync.service.js");
  await syncToBigQuery();
});

// ── Fraud Scan Worker (READ-ONLY, notification only) ────
createWorker(QUEUE_NAMES.FRAUD_SCAN, async () => {
  const { runFraudScan } = await import("./services/fraud-notifier.service.js");
  await runFraudScan();
});

// ── Boot ─────────────────────────────────────────────────────────────────────

async function boot() {
  log.info('═══ BullMQ Worker Process Starting ═══');
  
  await registerRepeatableJobs();
  
  log.info('═══ All workers registered. Consuming jobs from Redis. ═══');
}

boot().catch((err) => {
  log.error(`Worker boot failed: ${err.message}`);
  process.exit(1);
});

// ── Graceful Shutdown ────────────────────────────────────────────────────────

async function shutdown(signal: string) {
  log.info(`${signal} received — shutting down workers...`);
  await shutdownQueues();
  await disconnectRedis();
  await disconnectDatabase();
  log.info('Worker process exited cleanly.');
  process.exit(0);
}

process.on('SIGTERM', () => shutdown('SIGTERM'));
process.on('SIGINT', () => shutdown('SIGINT'));
