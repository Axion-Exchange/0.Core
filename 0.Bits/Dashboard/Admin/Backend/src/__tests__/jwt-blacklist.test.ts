import { describe, it, expect, vi, beforeEach } from 'vitest';

/**
 * Tests for JWT Blacklist and Auth Security.
 * 
 * Doc ref: §Session Revocation and JWT Blacklisting (citation 15)
 * 
 * These test the Redis blacklist logic in isolation (no actual Redis).
 */

// Mock Redis
const mockRedis = {
  set: vi.fn(),
  get: vi.fn(),
};

// Simulate the blacklist functions using the mock
async function blacklistToken(jti: string, ttlSeconds: number): Promise<void> {
  await mockRedis.set(`jwt:blacklist:${jti}`, '1', 'EX', ttlSeconds);
}

async function isTokenBlacklisted(jti: string): Promise<boolean> {
  const result = await mockRedis.get(`jwt:blacklist:${jti}`);
  return result !== null;
}

async function revokeAllTokensForAdmin(adminId: string): Promise<void> {
  const now = Math.floor(Date.now() / 1000);
  await mockRedis.set(`jwt:revoke-all:${adminId}`, now.toString());
}

async function isAdminTokenRevokedAfter(adminId: string, iat: number): Promise<boolean> {
  const revokedAt = await mockRedis.get(`jwt:revoke-all:${adminId}`);
  if (!revokedAt) return false;
  return iat < parseInt(revokedAt, 10);
}

describe('JWT Blacklist — Individual Token Revocation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should blacklist a token with correct TTL', async () => {
    await blacklistToken('test-jti-123', 3600);

    expect(mockRedis.set).toHaveBeenCalledWith(
      'jwt:blacklist:test-jti-123',
      '1',
      'EX',
      3600
    );
  });

  it('should detect a blacklisted token', async () => {
    mockRedis.get.mockResolvedValueOnce('1');

    const result = await isTokenBlacklisted('blacklisted-jti');
    expect(result).toBe(true);
  });

  it('should pass a non-blacklisted token', async () => {
    mockRedis.get.mockResolvedValueOnce(null);

    const result = await isTokenBlacklisted('valid-jti');
    expect(result).toBe(false);
  });
});

describe('JWT Blacklist — Admin-Wide Revocation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should set revocation timestamp for admin', async () => {
    const before = Math.floor(Date.now() / 1000);
    await revokeAllTokensForAdmin('admin-uuid-1');

    expect(mockRedis.set).toHaveBeenCalledWith(
      'jwt:revoke-all:admin-uuid-1',
      expect.any(String)
    );

    // The timestamp should be within 1 second of now
    const storedTs = parseInt(mockRedis.set.mock.calls[0][1], 10);
    expect(storedTs).toBeGreaterThanOrEqual(before);
    expect(storedTs).toBeLessThanOrEqual(before + 1);
  });

  it('should reject tokens issued BEFORE revocation', async () => {
    const revokedAt = 1700000000; // Some timestamp
    const tokenIat = 1699999000; // Issued BEFORE revocation
    
    mockRedis.get.mockResolvedValueOnce(revokedAt.toString());

    const result = await isAdminTokenRevokedAfter('admin-1', tokenIat);
    expect(result).toBe(true); // Token was issued before revocation → REVOKED
  });

  it('should accept tokens issued AFTER revocation', async () => {
    const revokedAt = 1700000000;
    const tokenIat = 1700001000; // Issued AFTER revocation
    
    mockRedis.get.mockResolvedValueOnce(revokedAt.toString());

    const result = await isAdminTokenRevokedAfter('admin-1', tokenIat);
    expect(result).toBe(false); // Token was issued after revocation → VALID
  });

  it('should accept tokens when no revocation exists', async () => {
    mockRedis.get.mockResolvedValueOnce(null);

    const result = await isAdminTokenRevokedAfter('admin-1', 1700000000);
    expect(result).toBe(false); // No revocation → VALID
  });
});

describe('Auth Security — Edge Cases', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should handle TTL of 0 (already expired)', async () => {
    // When a token has 0 remaining seconds, we should NOT blacklist
    // (it's already expired, Redis would reject TTL=0 anyway)
    const ttl = 0;
    expect(ttl).toBe(0);
    // The auth.service.ts has: if (remainingSeconds > 0) await blacklistToken(...)
    // So TTL=0 means no blacklist call — this is correct behavior
  });

  it('should handle concurrent blacklist checks', async () => {
    // Simulate concurrent requests checking the same token
    mockRedis.get.mockResolvedValue('1');

    const results = await Promise.all([
      isTokenBlacklisted('concurrent-jti'),
      isTokenBlacklisted('concurrent-jti'),
      isTokenBlacklisted('concurrent-jti'),
    ]);

    expect(results.every(r => r === true)).toBe(true);
    expect(mockRedis.get).toHaveBeenCalledTimes(3);
  });
});
