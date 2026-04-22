import { Prisma, PrismaClient } from '@prisma/client';
import { prisma } from './db.js';
import { createLogger } from './logger.js';

const log = createLogger('transaction');

/**
 * Safe transaction wrapper with retry logic.
 * 
 * Doc ref: §Ledger Integrity and Transactional Invariants (citations 9, 28, 29)
 * "A safe retry mechanism with jitter must be implemented to handle
 *  serialization failures (SQLSTATE 40001) or deadlocks (SQLSTATE 40P01)."
 * 
 * Uses Serializable isolation by default for financial-grade consistency.
 */

interface SafeTransactionOptions {
  /** Max retry attempts for serialization failures / deadlocks */
  maxRetries?: number;
  /** Base delay in ms for exponential backoff */
  baseDelayMs?: number;
  /** Isolation level (defaults to Serializable for financial ops) */
  isolationLevel?: Prisma.TransactionIsolationLevel;
  /** Max time to wait for transaction to start (ms) */
  maxWait?: number;
  /** Max time for the transaction to complete (ms) */
  timeout?: number;
  /** Human-readable label for logging */
  label?: string;
}

const DEFAULT_OPTIONS: Required<SafeTransactionOptions> = {
  maxRetries: 3,
  baseDelayMs: 100,
  isolationLevel: Prisma.TransactionIsolationLevel.Serializable,
  maxWait: 5000,
  timeout: 10000,
  label: 'unnamed',
};

/**
 * Execute a Prisma interactive transaction with automatic retry
 * on serialization failures (40001) and deadlocks (40P01).
 * 
 * Usage:
 * ```ts
 * await safeTransaction(async (tx) => {
 *   const sortedIds = [accountA, accountB].sort();
 *   for (const id of sortedIds) {
 *     await tx.account.update({ where: { id }, data: { ... } });
 *   }
 * }, { label: 'balance-transfer' });
 * ```
 */
export async function safeTransaction<T>(
  fn: (tx: Prisma.TransactionClient) => Promise<T>,
  options?: SafeTransactionOptions,
): Promise<T> {
  const opts = { ...DEFAULT_OPTIONS, ...options };
  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= opts.maxRetries; attempt++) {
    try {
      const result = await prisma.$transaction(fn, {
        isolationLevel: opts.isolationLevel,
        maxWait: opts.maxWait,
        timeout: opts.timeout,
      });

      if (attempt > 0) {
        log.info(`[Transaction] "${opts.label}" succeeded on retry ${attempt}`);
      }

      return result;
    } catch (error: any) {
      lastError = error;

      // Check if this is a retryable Postgres error
      const isSerializationFailure = error.code === 'P2034' || // Prisma serialization
        error.message?.includes('40001') ||                     // SQLSTATE serialization
        error.message?.includes('40P01') ||                     // SQLSTATE deadlock
        error.message?.includes('could not serialize') ||
        error.message?.includes('deadlock detected');

      if (!isSerializationFailure || attempt === opts.maxRetries) {
        // Non-retryable error or exhausted retries
        log.error(`[Transaction] "${opts.label}" failed permanently after ${attempt + 1} attempts: ${error.message}`);
        throw error;
      }

      // Exponential backoff with jitter
      const jitter = Math.random() * opts.baseDelayMs;
      const delay = opts.baseDelayMs * Math.pow(2, attempt) + jitter;
      log.warn(`[Transaction] "${opts.label}" serialization failure (attempt ${attempt + 1}/${opts.maxRetries + 1}), retrying in ${Math.round(delay)}ms`);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }

  // Should never reach here, but TypeScript needs it
  throw lastError || new Error('Transaction failed');
}

/**
 * Sort entity IDs deterministically before updating.
 * Prevents deadlocks by ensuring all concurrent transactions
 * acquire locks in the same order.
 * 
 * Doc ref: §Ledger Integrity (citation 9)
 * "the application must implement deterministic row ordering—
 *  sorting account IDs before updates"
 */
export function deterministicOrder<T extends string>(ids: T[]): T[] {
  return [...ids].sort();
}
