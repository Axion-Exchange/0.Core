import RedisLib from 'ioredis';
const Redis = RedisLib as unknown as typeof RedisLib.default;
import { createLogger } from './logger.js';

const log = createLogger('redis');

/**
 * Singleton Redis client.
 * 
 * Used by:
 *  - Rate limiting (RedisStore for express-rate-limit)
 *  - JWT blacklist (session revocation)
 *  - Future: BullMQ job queue
 * 
 * Doc ref: §Distributed Security, §Session Revocation (citations 7, 14, 15)
 */
const redis = new Redis({
  host: process.env.REDIS_HOST || '127.0.0.1',
  port: parseInt(process.env.REDIS_PORT || '6379', 10),
  maxRetriesPerRequest: null, // Required for BullMQ compatibility
  enableReadyCheck: true,
  retryStrategy(times: number) {
    const delay = Math.min(times * 200, 5000);
    log.warn(`[Redis] Reconnecting attempt ${times} in ${delay}ms`);
    return delay;
  },
  lazyConnect: false,
});

redis.on('connect', () => log.info('[Redis] Connected'));
redis.on('error', (err: Error) => log.error(`[Redis] Error: ${err.message}`));
redis.on('close', () => log.warn('[Redis] Connection closed'));

// ── JWT Blacklist Operations ─────────────────────────────────────────────────

/**
 * Add a JWT to the blacklist.
 * TTL = remaining validity of the token (seconds).
 * 
 * Doc ref: §Session Revocation and JWT Blacklisting (citation 15)
 */
export async function blacklistToken(jti: string, ttlSeconds: number): Promise<void> {
  await redis.set(`jwt:blacklist:${jti}`, '1', 'EX', ttlSeconds);
  log.info(`[JWT Blacklist] Token ${jti.substring(0, 8)}... blacklisted for ${ttlSeconds}s`);
}

/**
 * Check if a JWT is blacklisted.
 */
export async function isTokenBlacklisted(jti: string): Promise<boolean> {
  const result = await redis.get(`jwt:blacklist:${jti}`);
  return result !== null;
}

/**
 * Revoke all tokens for an admin by adding a "revoke-all" marker.
 */
export async function revokeAllTokensForAdmin(adminId: string): Promise<void> {
  const now = Math.floor(Date.now() / 1000);
  await redis.set(`jwt:revoke-all:${adminId}`, now.toString());
  log.info(`[JWT Blacklist] All tokens revoked for admin ${adminId}`);
}

/**
 * Check if all tokens for an admin were revoked after a given timestamp.
 */
export async function isAdminTokenRevokedAfter(adminId: string, iat: number): Promise<boolean> {
  const revokedAt = await redis.get(`jwt:revoke-all:${adminId}`);
  if (!revokedAt) return false;
  return iat < parseInt(revokedAt, 10);
}

/**
 * Graceful shutdown — close Redis connection.
 */
export async function disconnectRedis(): Promise<void> {
  await redis.quit();
  log.info('[Redis] Disconnected gracefully');
}

export { redis };
export default redis;
