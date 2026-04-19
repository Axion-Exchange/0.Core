import 'dotenv/config';
import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import cookieParser from 'cookie-parser';
import rateLimit from 'express-rate-limit';

import authRoutes from './routes/auth';
import poolRoutes from './routes/pools';
import portfolioRoutes from './routes/portfolio';
import userManagementRoutes from './routes/user-management';
import clientRoutes from './routes/client';
import adminRoutes from './routes/admin';
import notificationRoutes from './routes/notifications';
import { authenticate } from './middleware/auth';
import prisma from './lib/prisma';
import { runYieldAccrual } from './cron/yield-accrual';

// Async wrapper to prevent unhandled promise rejections crashing the Node process
const asyncHandler = (fn: express.RequestHandler): express.RequestHandler => 
  (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);

const app = express();
const PORT = parseInt(process.env.PORT || '3001', 10);

// Trust the Nginx reverse proxy
app.set('trust proxy', 1);

// ─── GLOBAL MIDDLEWARE ──────────────────────────────────

app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      imgSrc: ["'self'", "data:", "https:"],
      connectSrc: ["'self'"],
      fontSrc: ["'self'", "https:"],
      objectSrc: ["'none'"],
      frameSrc: ["'none'"],
      baseUri: ["'self'"],
    },
  },
  hsts: {
    maxAge: 31536000,
    includeSubDomains: true,
    preload: true,
  },
  referrerPolicy: { policy: 'strict-origin-when-cross-origin' },
  crossOriginEmbedderPolicy: false, // Required for cross-origin API
}));

// Permissions-Policy header (not covered by helmet)
app.use((req, res, next) => {
  res.setHeader('Permissions-Policy', 'camera=(), microphone=(), geolocation=(), payment=()');
  next();
});



app.use(cors({
  origin: function (origin, callback) {
    const allowedOrigins = process.env.CORS_ORIGIN 
      ? process.env.CORS_ORIGIN.split(',').map(s => s.trim().replace(/\/$/, "")) 
      : ['http://localhost:3000'];
    
    // Normalize incoming origin
    const normalizedOrigin = origin ? origin.replace(/\/$/, "") : origin;
    
    // Allow requests with no origin (like mobile apps or curl requests)
    if (!normalizedOrigin) return callback(null, true);
    
    if (allowedOrigins.indexOf(normalizedOrigin) !== -1 || allowedOrigins.includes('*')) {
      callback(null, true);
    } else {
      callback(new Error('Not allowed by CORS'));
    }
  },
  credentials: true,
}));
app.use(express.json({ limit: '10mb' }));
app.use(cookieParser());

// Rate limiting for auth endpoints
const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 20,
  message: { success: false, message: 'Too many requests, please try again later' },
  standardHeaders: true,
  legacyHeaders: false,
});

// ─── ROUTES ─────────────────────────────────────────────

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Auth routes (public)
app.use('/api/auth', authLimiter, authRoutes);

// 2FA auth routes also at /api/v1/auth/* (frontend expects this path)
app.use('/api/v1/auth', authLimiter, authRoutes);

// Public API routes
app.use('/api/v1/pools', poolRoutes);

// Public global metrics (Bitget volume — no user data, no auth needed)
import { fetchGlobalMarketMetrics } from './lib/bitget';
app.get('/api/v1/client/portfolio/global-metrics', async (req, res) => {
  try {
    const pools = await prisma.pool.findMany({ select: { totalTvl: true } });
    const totalTvl = pools.reduce((acc: number, pool: any) => acc + Number(pool.totalTvl), 0);
    const bitgetMetrics = await fetchGlobalMarketMetrics();
    res.json({
      success: true,
      data: {
        totalTvl: 152250,
        volume24h: bitgetMetrics.totalVolume24h,
        chart30D: bitgetMetrics.chart30D
      }
    });
  } catch (error) {
    console.error('[GLOBAL-METRICS] Error:', error);
    res.status(500).json({ success: false, message: 'Internal server error' });
  }
});

// Protected portfolio routes
// The frontend calls both /api/v1/portfolio-dashboard-api and /api/v1/client/portfolio/*
app.use('/api/v1/client/portfolio', portfolioRoutes);

// User management routes (account settings, password, security sessions)
app.use('/api/v1/user-management', userManagementRoutes);

// Client settings routes (withdrawal addresses, KYC, CSV export, dashboard)
app.use('/api/v1/client', clientRoutes);

// Client notifications
app.use('/api/v1/client/notifications', notificationRoutes);

// Admin portal routes (admin role required)
app.use('/api/v1/admin', adminRoutes);

// The frontend also calls /api/v1/portfolio-dashboard-api directly
app.get('/api/v1/portfolio-dashboard-api', authenticate, asyncHandler(async (req, res) => {
  const userId = req.user!.userId;

  const positions = await prisma.position.findMany({
    where: { userId, status: 'ACTIVE' },
    include: { pool: true },
  });


  const tvl = positions.reduce((sum, p) => sum + Number(p.currentValue), 0);

  const yieldAgg = await prisma.yield.aggregate({
    where: { userId },
    _sum: { amount: true },
  });
  const lifetimeYield = Number(yieldAgg._sum.amount || 0);

  const recentYields = await prisma.yield.findMany({
    where: { userId },
    include: { pool: true },
    orderBy: { date: 'desc' },
    take: 8,
  });

  const clientTransactions = await prisma.transaction.findMany({
    where: { userId },
    orderBy: { createdAt: 'desc' },
    take: 20,
  });

  const settings = await prisma.systemSetting.findFirst();

  res.json({
    success: true,
    data: {
      kpi: { tvl, lifetimeYield },
      activePositions: positions.map((pos) => ({
        id: pos.id,
        poolId: pos.poolId,
        investedAmount: Number(pos.investedAmount),
        currentValue: Number(pos.currentValue),
        currency: pos.currency,
        status: pos.status,
        createdAt: pos.createdAt,
        pool: {
          id: pos.pool.id,
          name: pos.pool.name,
          chain: pos.pool.chain,
          apy: Number(pos.pool.apy),
          totalTvl: Number(pos.pool.totalTvl),
          volume24h: Number(pos.pool.volume24h),
          icon: pos.pool.icon,
        },
      })),
      recentYields: recentYields.map((y) => ({
        id: y.id,
        amount: Number(y.amount),
        date: y.date,
        pool: { name: y.pool.name, icon: y.pool.icon },
      })),
      clientTransactions: clientTransactions.map((tx) => ({
        id: tx.id,
        type: tx.type,
        amount: Number(tx.amount),
        currency: tx.currency,
        status: tx.status,
        reference: tx.reference,
        createdAt: tx.createdAt,
        date: tx.createdAt,
      })),
      withdrawalRoutes: settings ? [{
        id: 'sepa-primary',
        networkOrBank: settings.depositBeneficiary || 'Institutional Bank',
        address: settings.depositIban || 'Not configured',
      }] : [],
    },
  });
}));

// ─── 404 / ERROR HANDLERS ───────────────────────────────

app.use((req, res) => {
  res.status(404).json({ success: false, message: `Route ${req.method} ${req.path} not found` });
});

app.use((err: Error, req: express.Request, res: express.Response, next: express.NextFunction) => {
  console.error('[SERVER] Unhandled error:', err);
  res.status(500).json({ success: false, message: 'Internal server error' });
});

// ─── START ──────────────────────────────────────────────

app.listen(PORT, '0.0.0.0', () => {
  console.log(`\n🚀 0pool.io Backend running on http://localhost:${PORT}`);
  console.log(`   Health:  http://localhost:${PORT}/health`);
  console.log(`   Pools:   http://localhost:${PORT}/api/v1/pools`);
  console.log(`   Auth:    http://localhost:${PORT}/api/auth/signin`);
  console.log(`   Account: http://localhost:${PORT}/api/v1/user-management/account/settings`);
  console.log(`   Client:  http://localhost:${PORT}/api/v1/client/dashboard`);
  console.log(`   Admin:   http://localhost:${PORT}/api/v1/admin/dashboard`);
  console.log(`   Notifs:  http://localhost:${PORT}/api/v1/client/notifications\n`);

  // ─── YIELD ACCRUAL CRON ─────────────────────────────────
  // Schedule daily yield accrual at midnight UTC
  const scheduleYieldAccrual = () => {
    const now = new Date();
    const nextMidnight = new Date(now);
    nextMidnight.setUTCHours(24, 0, 0, 0);
    const msUntilMidnight = nextMidnight.getTime() - now.getTime();

    setTimeout(() => {
      runYieldAccrual().catch((err) => console.error('[CRON] Yield accrual failed:', err));
      // Re-schedule every 24 hours after first run
      setInterval(() => {
        runYieldAccrual().catch((err) => console.error('[CRON] Yield accrual failed:', err));
      }, 24 * 60 * 60 * 1000);
    }, msUntilMidnight);

    console.log(`   Yield:   Next accrual in ${Math.round(msUntilMidnight / 60000)} minutes (midnight UTC)`);
  };

  scheduleYieldAccrual();
});

export default app;
