/**
 * Yield Accrual Engine
 * 
 * Runs daily (midnight UTC) and calculates yield for each active position
 * based on the pool's APY rate. Creates Yield records and updates position value.
 * 
 * Platform fee is deducted from gross yield before crediting to user.
 * Fee revenue is tracked in the system_logs table for reporting.
 * 
 * Usage:
 *   - Import and call `runYieldAccrual()` from a cron scheduler
 *   - Or run directly: `tsx src/cron/yield-accrual.ts`
 */

import prisma from '../lib/prisma';

export async function runYieldAccrual(): Promise<{ processed: number; totalYield: number; totalFees: number }> {
  console.log('[YIELD] Starting daily yield accrual...');

  const activePositions = await prisma.position.findMany({
    where: { status: 'ACTIVE' },
    include: { pool: true, user: true },
  });

  let processed = 0;
  let totalYield = 0;
  let totalFees = 0;

  for (const position of activePositions) {
    try {
      const pool = position.pool;
      if (!pool.isActive) continue;

      // Daily yield = currentValue * (APY / 365)
      const dailyRate = Number(pool.apy) / 100 / 365;
      const grossYield = Number(position.currentValue) * dailyRate;

      if (grossYield < 0.01) continue; // Skip dust amounts

      // Platform fee deduction
      const feeRate = Number(pool.feeRate) / 100;
      const platformFee = grossYield * feeRate;
      const netYield = grossYield - platformFee;

      // Create yield record
      await prisma.yield.create({
        data: {
          positionId: position.id,
          poolId: pool.id,
          userId: position.userId,
          amount: netYield,
          date: new Date(),
        },
      });

      // Update position value
      await prisma.position.update({
        where: { id: position.id },
        data: {
          currentValue: { increment: netYield },
        },
      });

      // Track fee revenue
      if (platformFee > 0.001) {
        await prisma.systemLog.create({
          data: {
            event: 'PLATFORM_FEE_COLLECTED',
            userId: position.userId,
            entityId: position.id,
            entityType: 'position',
            description: `Fee: $${platformFee.toFixed(4)} from ${pool.name} yield. Gross: $${grossYield.toFixed(4)}, Net: $${netYield.toFixed(4)}`,
            meta: {
              poolId: pool.id,
              poolName: pool.name,
              grossYield,
              platformFee,
              netYield,
              apy: Number(pool.apy),
              feeRate: Number(pool.feeRate),
              positionValue: Number(position.currentValue),
            },
          },
        });
      }

      processed++;
      totalYield += netYield;
      totalFees += platformFee;
    } catch (error) {
      console.error(`[YIELD] Error processing position ${position.id}:`, error);
    }
  }

  // Summary log
  await prisma.systemLog.create({
    data: {
      event: 'YIELD_ACCRUAL_COMPLETE',
      userId: 'SYSTEM',
      description: `Daily yield accrual: ${processed} positions, $${totalYield.toFixed(2)} yield distributed, $${totalFees.toFixed(2)} platform fees collected.`,
      meta: { processed, totalYield, totalFees, date: new Date().toISOString() },
    },
  });

  console.log(`[YIELD] Complete: ${processed} positions, $${totalYield.toFixed(2)} yield, $${totalFees.toFixed(2)} fees`);

  return { processed, totalYield, totalFees };
}

// Run directly if invoked as script
if (require.main === module) {
  runYieldAccrual()
    .then((result) => {
      console.log('[YIELD] Result:', result);
      process.exit(0);
    })
    .catch((error) => {
      console.error('[YIELD] Fatal error:', error);
      process.exit(1);
    });
}
