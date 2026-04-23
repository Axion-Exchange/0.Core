import { Queue, Worker, Job } from 'bullmq';
import { redis } from './redis.js';
import { createLogger } from './logger.js';

const log = createLogger('queue');

/**
 * BullMQ Queue + Worker infrastructure.
 * 
 * Doc ref: §Decoupling via Distributed Job Queues (citations 5, 6)
 * "An institutional grade fix mandates the total separation of worker processes
 *  from HTTP server processes... leveraging BullMQ backed by Redis."
 * 
 * "BullMQ utilizes efficient Lua scripts and pipelining to ensure that
 *  even as the number of worker processes increases, jobs are distributed
 *  in a round-robin fashion or pulled by available workers without duplication."
 */

// ── Redis connection config for BullMQ ───────────────────────────────────────
// BullMQ needs its own connection options (not the ioredis instance directly)
const REDIS_CONNECTION = {
  host: process.env.REDIS_HOST || '127.0.0.1',
  port: parseInt(process.env.REDIS_PORT || '6379', 10),
  maxRetriesPerRequest: null,
};

// ── Queue Definitions ────────────────────────────────────────────────────────

export const QUEUE_NAMES = {
  P2P_ORCHESTRATOR: 'p2p-orchestrator',
  BINANCE_SYNC: 'binance-sync',
  CHAT_SYNC: 'chat-sync',
  FIAT_SYNC: 'fiat-sync',
  PEAR_DB_SYNC: 'pear-db-sync',
  KYC_SYNC: 'kyc-sync',
  HEALTH_CHECK: 'health-check',
  BIGQUERY_SYNC: 'bigquery-sync',
  FRAUD_SCAN: 'fraud-scan',
  BITGET_SPOT_SYNC: 'bitget-spot-sync',
  MEXC_SPOT_SYNC: 'mexc-spot-sync',
  CAPITAL_FLOW_SYNC: 'capital-flow-sync',
} as const;

type QueueName = typeof QUEUE_NAMES[keyof typeof QUEUE_NAMES];

// ── Queue Factory ────────────────────────────────────────────────────────────

const queues = new Map<string, Queue>();

/**
 * Get or create a BullMQ queue by name.
 * Queues are shared between the API server (for adding jobs) and workers (for processing).
 */
export function getQueue(name: QueueName): Queue {
  if (!queues.has(name)) {
    const queue = new Queue(name, {
      connection: REDIS_CONNECTION,
      defaultJobOptions: {
        removeOnComplete: { count: 100 },
        removeOnFail: { count: 50 },
        attempts: 3,
        backoff: {
          type: 'exponential',
          delay: 1000,
        },
      },
    });
    queues.set(name, queue);
    log.info(`[Queue] Created queue: ${name}`);
  }
  return queues.get(name)!;
}

// ── Worker Factory ───────────────────────────────────────────────────────────

const workers = new Map<string, Worker>();

/**
 * Create a BullMQ worker for a queue.
 * Workers pull jobs from the queue and execute the processor function.
 * 
 * Only call this in the worker entry point (worker.entry.ts),
 * NOT in the HTTP server.
 */
export function createWorker(
  name: QueueName,
  processor: (job: Job) => Promise<void>,
  options?: { concurrency?: number }
): Worker {
  const worker = new Worker(name, processor, {
    connection: REDIS_CONNECTION,
    concurrency: options?.concurrency ?? 1,
    limiter: undefined,
  });

  worker.on('completed', (job) => {
    log.info(`[Worker:${name}] Job ${job.id} completed`);
  });

  worker.on('failed', (job, error) => {
    log.error(`[Worker:${name}] Job ${job?.id} failed: ${error.message}`);
  });

  worker.on('error', (error) => {
    log.error(`[Worker:${name}] Error: ${error.message}`);
  });

  workers.set(name, worker);
  log.info(`[Worker] Registered processor for: ${name}`);
  return worker;
}

// ── Repeatable Job Setup ─────────────────────────────────────────────────────

/**
 * Register all repeatable jobs (replaces setInterval).
 * 
 * Called once from worker.entry.ts on startup.
 * BullMQ handles deduplication — if a repeatable job already exists,
 * it won't create a duplicate.
 * 
 * "Delayed or scheduled tasks survive server restarts, and complex job flows
 *  involving parent-child dependencies can be managed" (citation 6)
 */
export async function registerRepeatableJobs(): Promise<void> {
  const schedules: { queue: QueueName; every: number; name: string }[] = [
    { queue: QUEUE_NAMES.P2P_ORCHESTRATOR, every: 15000,  name: 'p2p-tick' },
    { queue: QUEUE_NAMES.BINANCE_SYNC,     every: 30000,  name: 'binance-sync-tick' },
    { queue: QUEUE_NAMES.CHAT_SYNC,        every: 60000,  name: 'chat-sync-tick' },
    { queue: QUEUE_NAMES.FIAT_SYNC,        every: 30000,  name: 'fiat-sync-tick' },
    { queue: QUEUE_NAMES.PEAR_DB_SYNC,     every: 30000,  name: 'pear-db-sync-tick' },
    { queue: QUEUE_NAMES.KYC_SYNC,         every: 30000,  name: 'kyc-sync-tick' },
    { queue: QUEUE_NAMES.HEALTH_CHECK,  every: 300000,  name: 'health-check-tick' },
    { queue: QUEUE_NAMES.BIGQUERY_SYNC,   every: 21600000, name: 'bq-sync-tick' },
    { queue: QUEUE_NAMES.FRAUD_SCAN,      every: 21600000, name: 'fraud-scan-tick' },
    { queue: QUEUE_NAMES.BITGET_SPOT_SYNC, every: 600000, name: 'bitget-spot-tick' },
    { queue: QUEUE_NAMES.MEXC_SPOT_SYNC,   every: 300000, name: 'mexc-spot-tick' },
    { queue: QUEUE_NAMES.CAPITAL_FLOW_SYNC, every: 30000, name: 'capital-flow-sync-tick' },
  ];

  for (const { queue, every, name } of schedules) {
    const q = getQueue(queue);
    await q.add(name, {}, {
      repeat: { every },
      jobId: name, // Prevent duplicates
    });
    log.info(`[Queue] Scheduled repeatable job: ${name} (every ${every / 1000}s)`);
  }
}

// ── Graceful Shutdown ────────────────────────────────────────────────────────

export async function shutdownQueues(): Promise<void> {
  log.info('[Queue] Shutting down all workers and queues...');
  
  for (const [name, worker] of workers) {
    await worker.close();
    log.info(`[Worker] Closed: ${name}`);
  }

  for (const [name, queue] of queues) {
    await queue.close();
    log.info(`[Queue] Closed: ${name}`);
  }
}
