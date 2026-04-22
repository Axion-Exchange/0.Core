import { Prisma } from '@prisma/client';
import { prisma } from './db.js';
import { createLogger } from './logger.js';

const log = createLogger('advisory-lock');

/**
 * Postgres Advisory Locks for distributed mutual exclusion.
 * 
 * Doc ref: §Distributed Locking and Quorum (citations 8, 9)
 * "Redlock or Postgres advisory locks (such as pg_advisory_xact_lock) are the
 *  standard for high-risk financial backend operations."
 * "Advisory locks provide a mechanism to lock a logical resource ID rather than
 *  an entire table, significantly reducing lock contention while maintaining integrity."
 * 
 * Uses pg_advisory_xact_lock which auto-releases when the transaction ends.
 * This prevents:
 *   - Concurrent ledger updates for the same user
 *   - Double-processing of the same P2P order
 *   - Race conditions in balance mutations
 * 
 * Usage:
 * ```ts
 * await withAdvisoryLock('user-balance', userId, async () => {
 *   // This block has exclusive access to this user's balance
 *   const balance = await prisma.balanceLedger.findFirst({ where: { userId } });
 *   await prisma.balanceLedger.update({ where: { id: balance.id }, data: { ... } });
 * });
 * ```
 */

// Lock namespace constants — prevent collisions between different lock types
export const LOCK_NS = {
  USER_BALANCE: 1,
  ORDER_PROCESSING: 2,
  FIAT_SETTLEMENT: 3,
  KYC_STATUS: 4,
  RECONCILIATION: 5,
} as const;

/**
 * Convert a string ID to a 32-bit integer for Postgres advisory lock.
 * Uses FNV-1a hash for good distribution.
 */
function hashToInt32(str: string): number {
  let hash = 0x811c9dc5; // FNV offset basis
  for (let i = 0; i < str.length; i++) {
    hash ^= str.charCodeAt(i);
    hash = (hash * 0x01000193) | 0; // FNV prime, keep as 32-bit int
  }
  return hash;
}

/**
 * Execute a function while holding a Postgres advisory lock.
 * 
 * Uses pg_advisory_xact_lock(namespace, resource_id) which:
 * - Blocks until the lock is acquired (no spinning)
 * - Auto-releases when the transaction commits/rollbacks
 * - Works across all PM2 instances (it's in Postgres, not in-memory)
 * 
 * @param namespace - Lock type from LOCK_NS
 * @param resourceId - String ID of the resource to lock (e.g., userId, orderId)
 * @param fn - Function to execute while holding the lock
 */
export async function withAdvisoryLock<T>(
  namespace: number,
  resourceId: string,
  fn: (tx: Prisma.TransactionClient) => Promise<T>,
): Promise<T> {
  const lockId = hashToInt32(resourceId);

  return prisma.$transaction(async (tx: any) => {
    // Acquire the advisory lock — blocks until available
    await tx.$queryRawUnsafe(
      `SELECT pg_advisory_xact_lock($1, $2)`,
      namespace,
      lockId,
    );

    log.info(`[Lock] Acquired (ns=${namespace}, id=${lockId}, resource=${resourceId.substring(0, 8)}...)`);

    // Execute the protected operation
    return fn(tx);
  }, {
    isolationLevel: 'Serializable',
    maxWait: 5000,
    timeout: 10000,
  });
}

/**
 * Try to acquire an advisory lock without blocking.
 * Returns false immediately if the lock is held by another session.
 * 
 * Useful for:
 * - Idempotent operations that should skip if already running
 * - "Try once, fail fast" patterns
 */
export async function tryAdvisoryLock<T>(
  namespace: number,
  resourceId: string,
  fn: (tx: Prisma.TransactionClient) => Promise<T>,
): Promise<{ acquired: boolean; result?: T }> {
  const lockId = hashToInt32(resourceId);

  return prisma.$transaction(async (tx: any) => {
    const [row]: any[] = await tx.$queryRawUnsafe(
      `SELECT pg_try_advisory_xact_lock($1, $2) AS acquired`,
      namespace,
      lockId,
    );

    if (!row.acquired) {
      log.warn(`[Lock] Could not acquire (ns=${namespace}, resource=${resourceId.substring(0, 8)}...) — already held`);
      return { acquired: false };
    }

    const result = await fn(tx);
    return { acquired: true, result };
  }, {
    isolationLevel: 'Serializable',
    maxWait: 5000,
    timeout: 10000,
  });
}
