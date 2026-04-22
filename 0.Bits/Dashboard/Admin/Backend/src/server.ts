import express from 'express';
import helmet from 'helmet';
import { createServer } from 'http';
import { v4 as uuid } from 'uuid';

import { config } from './config/index.js';
import { createLogger } from './lib/logger.js';
import { checkDatabaseHealth, disconnectDatabase } from './lib/db.js';
import { sendSuccess, sendError } from './lib/response.js';
import { initSocket } from './lib/socket.js';

// Middleware
import { createCorsMiddleware } from './middleware/cors.js';
import { publicLimiter, authLimiter } from './middleware/rate-limit.js';
import { errorHandler } from './middleware/error.js';

// Routers
import { authRouter } from './routes/auth.router.js';
import { p2pRouter } from './routes/p2p.router.js';
import { treasuryRouter } from './routes/treasury.router.js';
import { usersRouter } from './routes/users.router.js';
import { operationsRouter } from './routes/operations.router.js';
import { complianceRouter } from './routes/compliance.router.js';
import { notificationsRouter } from './routes/notifications.router.js';
import { teamRouter } from './routes/team.router.js';
import { tasksRouter } from './routes/tasks.router.js';
import { dashboardRouter } from './routes/dashboard.router.js';
import { kycRouter } from './routes/kyc.router.js';
import { pearRouter } from './routes/pear.router.js';
import { fiatRouter } from './routes/fiat.router.js';
import { reconciliationRouter } from './routes/reconciliation.router.js';
import { currencyLedgerRouter } from './routes/currency-ledger.router.js';
import { orchestratorWorker } from './workers/p2p.worker.js';
import { pearDbSyncWorker } from './workers/pear-db-sync.worker.js';
import { binanceSyncWorker } from './workers/binance-sync.worker.js';
import { chatSyncWorker } from './workers/chat-sync.worker.js';
import { fiatSyncWorker } from './workers/fiat-sync.worker.js';

const log = createLogger('server');

// ── App Factory ──────────────────────────────────────

const app = express();

// 1. Security headers
app.use(helmet({
  hsts: { maxAge: 31536000, includeSubDomains: true, preload: true },
  frameguard: { action: 'deny' },
  contentSecurityPolicy: config.NODE_ENV === 'production' ? undefined : false,
}));

// 2. CORS
app.use(createCorsMiddleware());

// 3. Body parsing
app.use(express.json({ limit: '2mb' }));
app.use(express.urlencoded({ extended: true, limit: '2mb' }));

// 4. Correlation ID injection (for request tracing)
app.use((req, _res, next) => {
  req.correlationId = (req.headers['x-correlation-id'] as string) ?? uuid();
  next();
});

// 5. Request logging
app.use((req, res, next) => {
  const start = Date.now();
  res.on('finish', () => {
    const duration = Date.now() - start;
    log.info(`${req.method} ${req.path} ${res.statusCode} ${duration}ms`, {
      correlationId: req.correlationId,
    });
  });
  next();
});

// ── Public Routes (no auth required) ─────────────────

// Health check (public, for load balancers / uptime monitors)
app.get('/api/v1/health', publicLimiter, async (_req, res) => {
  const dbHealthy = await checkDatabaseHealth();
  sendSuccess(res, {
    status: dbHealthy ? 'operational' : 'degraded',
    version: '1.0.0',
    timestamp: new Date().toISOString(),
    uptime: Math.floor(process.uptime()),
  });
});

// Auth routes (login is public, others require auth internally)
app.use('/api/v1/auth', publicLimiter, authRouter);

// ── Authenticated Routes ─────────────────────────────

app.use('/api/v1/p2p', authLimiter, p2pRouter);
app.use('/api/v1/treasury', authLimiter, treasuryRouter);
app.use('/api/v1/treasury/currency', authLimiter, currencyLedgerRouter);
app.use('/api/v1/users', authLimiter, usersRouter);
app.use('/api/v1/operations', authLimiter, operationsRouter);
app.use('/api/v1/compliance', authLimiter, complianceRouter);
app.use('/api/v1/notifications', authLimiter, notificationsRouter);
app.use('/api/v1/team', authLimiter, teamRouter);
app.use('/api/v1/tasks', authLimiter, tasksRouter);
app.use('/api/v1/dashboard', authLimiter, dashboardRouter);
app.use('/api/v1/kyc', authLimiter, kycRouter);
app.use('/api/v1/pear', authLimiter, pearRouter);
app.use('/api/v1/reconciliation', authLimiter, reconciliationRouter);
app.use('/api/v1/fiat', publicLimiter, fiatRouter); // Webhooks are authenticated via HMAC signature, not JWT

// ── 404 Handler ──────────────────────────────────────

app.use((_req, res) => {
  sendError(res, 404, 'NOT_FOUND', 'The requested endpoint does not exist');
});

// ── Global Error Handler ─────────────────────────────

app.use(errorHandler);

// ── Server Startup ───────────────────────────────────

const PORT = config.PORT;

const httpServer = createServer(app);
initSocket(httpServer);

const server = httpServer.listen(PORT, () => {
  log.info(`0.Bits API server running on port ${PORT}`, {
    env: config.NODE_ENV,
    port: PORT,
  });
  
  // Ignite the background P2P execution loop
  orchestratorWorker.start();
  
  // Ignite Python-Postgres DB Syncer
  pearDbSyncWorker.start(30000);
  
  // Ignite Binance Auditing Archiver
  binanceSyncWorker.start(30000);
  
  // Ignite Institutional Bank Polling
  fiatSyncWorker.start(30000);
  
  // Ignite P2P Chat Polling
  chatSyncWorker.start();
});

// ── Graceful Shutdown ────────────────────────────────

async function shutdown(signal: string) {
  log.info(`${signal} received — shutting down gracefully...`);

  server.close(async () => {
    log.info('HTTP server closed');
    orchestratorWorker.stop();
    pearDbSyncWorker.stop();
    binanceSyncWorker.stop();
    chatSyncWorker.stop();
    fiatSyncWorker.stop();
    await disconnectDatabase();
    log.info('Database disconnected');
    process.exit(0);
  });

  // Force shutdown after 10s
  setTimeout(() => {
    log.error('Forced shutdown after 10s timeout');
    process.exit(1);
  }, 10000);
}

process.on('SIGTERM', () => shutdown('SIGTERM'));
process.on('SIGINT', () => shutdown('SIGINT'));

export default app;
