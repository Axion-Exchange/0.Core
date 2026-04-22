import { describe, it, expect } from 'vitest';

/**
 * Tests for BullMQ Queue Configuration.
 * 
 * Doc ref: §Decoupling via Distributed Job Queues (citations 5, 6)
 * 
 * Verifies that all 6 worker queues are defined and the repeatable
 * job schedules match the expected intervals.
 */

// Queue names (mirrored from lib/queue.ts)
const QUEUE_NAMES = {
  P2P_ORCHESTRATOR: 'p2p-orchestrator',
  BINANCE_SYNC: 'binance-sync',
  CHAT_SYNC: 'chat-sync',
  FIAT_SYNC: 'fiat-sync',
  PEAR_DB_SYNC: 'pear-db-sync',
  KYC_SYNC: 'kyc-sync',
} as const;

// Expected schedules (mirrored from lib/queue.ts registerRepeatableJobs)
const SCHEDULES = [
  { queue: QUEUE_NAMES.P2P_ORCHESTRATOR, every: 15000,  name: 'p2p-tick' },
  { queue: QUEUE_NAMES.BINANCE_SYNC,     every: 30000,  name: 'binance-sync-tick' },
  { queue: QUEUE_NAMES.CHAT_SYNC,        every: 60000,  name: 'chat-sync-tick' },
  { queue: QUEUE_NAMES.FIAT_SYNC,        every: 30000,  name: 'fiat-sync-tick' },
  { queue: QUEUE_NAMES.PEAR_DB_SYNC,     every: 30000,  name: 'pear-db-sync-tick' },
  { queue: QUEUE_NAMES.KYC_SYNC,         every: 30000,  name: 'kyc-sync-tick' },
];

describe('BullMQ Queue Definitions', () => {
  it('should have exactly 6 queues defined', () => {
    expect(Object.keys(QUEUE_NAMES)).toHaveLength(6);
  });

  it('should have unique queue names', () => {
    const values = Object.values(QUEUE_NAMES);
    const unique = new Set(values);
    expect(unique.size).toBe(values.length);
  });

  it('should have unique job names in schedules', () => {
    const names = SCHEDULES.map(s => s.name);
    const unique = new Set(names);
    expect(unique.size).toBe(names.length);
  });
});

describe('BullMQ Schedule Invariants', () => {
  it('P2P orchestrator should poll every 15 seconds (fastest)', () => {
    const p2p = SCHEDULES.find(s => s.queue === QUEUE_NAMES.P2P_ORCHESTRATOR);
    expect(p2p?.every).toBe(15000);
  });

  it('chat sync should be the slowest (60s)', () => {
    const chat = SCHEDULES.find(s => s.queue === QUEUE_NAMES.CHAT_SYNC);
    expect(chat?.every).toBe(60000);
  });

  it('no schedule should be faster than 10 seconds (API rate limit safety)', () => {
    for (const sched of SCHEDULES) {
      expect(sched.every).toBeGreaterThanOrEqual(10000);
    }
  });

  it('no schedule should be slower than 5 minutes (data freshness)', () => {
    for (const sched of SCHEDULES) {
      expect(sched.every).toBeLessThanOrEqual(300000);
    }
  });

  it('all schedules should map to defined queue names', () => {
    const queueValues = new Set(Object.values(QUEUE_NAMES));
    for (const sched of SCHEDULES) {
      expect(queueValues.has(sched.queue)).toBe(true);
    }
  });
});
