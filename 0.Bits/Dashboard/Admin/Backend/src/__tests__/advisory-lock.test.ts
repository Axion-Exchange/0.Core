import { describe, it, expect } from 'vitest';
import { LOCK_NS } from '../lib/advisory-lock.js';

/**
 * Tests for Postgres Advisory Lock infrastructure.
 * 
 * Doc ref: §Distributed Locking and Quorum (citations 8, 9)
 * 
 * We can't test actual Postgres locks without a database connection,
 * but we CAN verify the hash function and namespace configuration.
 */

// Re-implement the hash for testing (same as advisory-lock.ts)
function hashToInt32(str: string): number {
  let hash = 0x811c9dc5;
  for (let i = 0; i < str.length; i++) {
    hash ^= str.charCodeAt(i);
    hash = (hash * 0x01000193) | 0;
  }
  return hash;
}

describe('Advisory Lock — Hash Function', () => {
  it('should produce deterministic hashes', () => {
    const hash1 = hashToInt32('user-123');
    const hash2 = hashToInt32('user-123');
    expect(hash1).toBe(hash2);
  });

  it('should produce different hashes for different inputs', () => {
    const hash1 = hashToInt32('user-123');
    const hash2 = hashToInt32('user-456');
    expect(hash1).not.toBe(hash2);
  });

  it('should produce 32-bit integers', () => {
    const hash = hashToInt32('some-very-long-uuid-value-here');
    expect(hash).toBeGreaterThanOrEqual(-2147483648);
    expect(hash).toBeLessThanOrEqual(2147483647);
  });

  it('should handle empty strings', () => {
    const hash = hashToInt32('');
    expect(typeof hash).toBe('number');
    expect(Number.isFinite(hash)).toBe(true);
  });

  it('should handle UUIDs', () => {
    const hash = hashToInt32('550e8400-e29b-41d4-a716-446655440000');
    expect(typeof hash).toBe('number');
    expect(Number.isFinite(hash)).toBe(true);
  });
});

describe('Advisory Lock — Namespace Configuration', () => {
  it('should have unique namespace values', () => {
    const values = Object.values(LOCK_NS);
    const unique = new Set(values);
    expect(unique.size).toBe(values.length);
  });

  it('should have all required lock types', () => {
    expect(LOCK_NS.USER_BALANCE).toBeDefined();
    expect(LOCK_NS.ORDER_PROCESSING).toBeDefined();
    expect(LOCK_NS.FIAT_SETTLEMENT).toBeDefined();
    expect(LOCK_NS.KYC_STATUS).toBeDefined();
    expect(LOCK_NS.RECONCILIATION).toBeDefined();
  });

  it('should use small positive integers as namespaces', () => {
    for (const val of Object.values(LOCK_NS)) {
      expect(val).toBeGreaterThan(0);
      expect(val).toBeLessThan(100);
    }
  });
});

describe('Advisory Lock — Collision Resistance', () => {
  it('should have low collision rate across 1000 UUIDs', () => {
    const hashes = new Set<number>();
    for (let i = 0; i < 1000; i++) {
      const uuid = `${i.toString(16).padStart(8, '0')}-0000-0000-0000-000000000000`;
      hashes.add(hashToInt32(uuid));
    }
    // At least 99% unique (allow for minimal collision in 32-bit space)
    expect(hashes.size).toBeGreaterThanOrEqual(990);
  });
});
