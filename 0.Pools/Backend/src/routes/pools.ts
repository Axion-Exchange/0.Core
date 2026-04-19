import { Router, Request, Response } from 'express';
import prisma from '../lib/prisma';

const router = Router();

// ─── GET /api/v1/pools ──────────────────────────────────
// Public endpoint — returns all active liquidity pools

router.get('/', async (req: Request, res: Response) => {
  try {
    const pools = await prisma.pool.findMany({
      where: { isActive: true },
      orderBy: { totalTvl: 'desc' },
    });

    res.json({
      success: true,
      data: pools.map((p) => ({
        id: p.id,
        name: p.name,
        chain: p.chain,
        riskTier: p.riskTier,
        apy: Number(p.apy),
        feeRate: Number(p.feeRate),
        totalTvl: Number(p.totalTvl),
        volume24h: Number(p.volume24h),
        icon: p.icon,
        description: p.description,
        cryptoDepositAddress: p.cryptoDepositAddress,
      })),
    });
  } catch (error) {
    console.error('[POOLS] List error:', error);
    res.status(500).json({ success: false, message: 'Internal server error' });
  }
});

// ─── GET /api/v1/pools/volume ───────────────────────────
// Public endpoint — volume chart timeseries

router.get('/volume', async (req: Request, res: Response) => {
  try {
    const timeframe = (req.query.timeframe as string) || '30D';

    let period: string;
    let limit: number;

    switch (timeframe) {
      case '12W':
        period = 'weekly';
        limit = 12;
        break;
      case '6M':
        period = 'monthly';
        limit = 6;
        break;
      default:
        period = 'daily';
        limit = 30;
    }

    const snapshots = await prisma.poolVolumeSnapshot.findMany({
      where: { period },
      orderBy: { date: 'desc' },
      take: limit,
    });

    // Aggregate across all pools per date
    const dateMap = new Map<string, number>();
    for (const s of snapshots) {
      const key = s.date.toISOString().split('T')[0];
      dateMap.set(key, (dateMap.get(key) || 0) + Number(s.volume));
    }

    const chartData = Array.from(dateMap.entries())
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([date, volume]) => ({ date, volume }));

    res.json({ success: true, data: chartData });
  } catch (error) {
    console.error('[POOLS] Volume error:', error);
    res.status(500).json({ success: false, message: 'Internal server error' });
  }
});

export default router;
