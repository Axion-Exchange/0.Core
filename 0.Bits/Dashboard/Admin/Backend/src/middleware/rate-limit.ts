import rateLimit from 'express-rate-limit';
import RedisStore from 'rate-limit-redis';
import { redis } from '../lib/redis.js';

/**
 * Redis-backed distributed rate limiters.
 * 
 * Doc ref: §Advanced Distributed Rate Limiting (citations 7, 14, 17)
 * "rate limiting must be migrated to a centralized store such as Redis
 *  using the rate-limit-redis provider... institutional systems implement
 *  tiered policies based on user value and endpoint risk."
 * 
 * All counters are now global across PM2 cluster instances.
 */

// ── Shared Redis Store Factory ───────────────────────────────────────────────

function createRedisStore(prefix: string) {
  return new RedisStore({
    // Use the singleton ioredis client
    sendCommand: (...args: string[]) => (redis as any).call(...args),
    prefix: `rl:${prefix}:`,
  });
}

// ── Tier 1: Public (Unauthenticated) ─────────────────────────────────────────

/**
 * Public rate limiter: unauthenticated endpoints (login, health, webhooks).
 * 100 requests per 15 minutes.
 */
export const publicLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 100,
  standardHeaders: true,
  legacyHeaders: false,
  store: createRedisStore('public'),
  message: {
    success: false,
    error: {
      code: 'RATE_LIMIT',
      message: 'Too many requests — limit 100 per 15 minutes. Retry later.',
    },
  },
});

// ── Tier 2: Authenticated ────────────────────────────────────────────────────

/**
 * Authenticated rate limiter: standard admin operations.
 * 500 requests per 15 minutes.
 */
export const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 500,
  standardHeaders: true,
  legacyHeaders: false,
  store: createRedisStore('auth'),
  message: {
    success: false,
    error: {
      code: 'RATE_LIMIT',
      message: 'Too many authenticated requests — limit 500 per 15 minutes.',
    },
  },
});

// ── Tier 3: Login (Brute-Force Protection) ───────────────────────────────────

/**
 * Strict rate limiter: login attempts.
 * 10 failed attempts per 15 minutes.
 */
export const loginLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 10,
  standardHeaders: true,
  legacyHeaders: false,
  skipSuccessfulRequests: true,
  store: createRedisStore('login'),
  message: {
    success: false,
    error: {
      code: 'RATE_LIMIT',
      message: 'Too many login attempts. Account temporarily locked.',
    },
  },
});

// ── Tier 4: Critical (Ledger Mutations) ──────────────────────────────────────

/**
 * Critical rate limiter: ledger mutations, fund movements, admin actions.
 * 20 requests per 15 minutes.
 * 
 * Applied to endpoints that modify financial state.
 */
export const criticalLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 20,
  standardHeaders: true,
  legacyHeaders: false,
  store: createRedisStore('critical'),
  message: {
    success: false,
    error: {
      code: 'RATE_LIMIT',
      message: 'Too many critical operations — limit 20 per 15 minutes.',
    },
  },
});
