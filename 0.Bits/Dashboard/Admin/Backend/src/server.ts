import express from 'express';
import helmet from 'helmet';
import { createServer } from 'http';
import { v4 as uuid } from 'uuid';

import { config } from './config/index.js';
import { createLogger } from './lib/logger.js';
import { checkDatabaseHealth, disconnectDatabase } from './lib/db.js';
import { disconnectRedis } from './lib/redis.js';
import { sendSuccess, sendError } from './lib/response.js';
import { initSocket } from './lib/socket.js';

// Middleware
import { createCorsMiddleware } from './middleware/cors.js';
import { publicLimiter, authLimiter } from './middleware/rate-limit.js';
import { errorHandler } from './middleware/error.js';
import { sanitizeInput, securityHeaders, enforcePayloadLimits } from './middleware/security.js';
import hpp from 'hpp';

// Routers
import { authRouter } from './routes/auth.router.js';
import { p2pRouter } from './routes/p2p.router.js';
import { p2pService } from './services/p2p.service.js';
import { treasuryRouter } from './routes/treasury.router.js';
import { usersRouter } from './routes/users.router.js';
import { operationsRouter } from './routes/operations.router.js';
import { opsExtRouter } from './routes/ops-ext.router.js';
import { featureFlags } from './services/feature-flags.service.js';
import { startPnLEmitter } from './services/pnl-realtime.service.js';
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
import { kycWebhookRouter } from './routes/kyc-webhook.router.js';

const log = createLogger('server');

// ── App Factory ──────────────────────────────────────

const app = express();

// Trust Cloudflare proxy (required for express-rate-limit behind CDN)
app.set('trust proxy', 1);

// 1. Security headers (Helmet + OWASP extras)
app.use(helmet({
  hsts: { maxAge: 31536000, includeSubDomains: true, preload: true },
  frameguard: { action: 'deny' },
  contentSecurityPolicy: config.NODE_ENV === 'production' ? undefined : false,
}));
app.use(securityHeaders);

// 2. CORS
app.use(createCorsMiddleware());

// 3. HTTP Parameter Pollution prevention (OWASP)
// Doc ref: §Mitigating OWASP API Risks (citation 36)
app.use(hpp());

// 4. Payload size enforcement
app.use(enforcePayloadLimits);

// 5. Body parsing
app.use(express.json({ limit: '2mb' }));
app.use(express.urlencoded({ extended: true, limit: '2mb' }));

// 6. Input sanitization (blocks NoSQL injection, prototype pollution, path traversal)
app.use(sanitizeInput);

// 7. Correlation ID injection (for request tracing)
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
app.use('/api/v1/operations', authLimiter, opsExtRouter);
app.use('/api/v1/compliance', authLimiter, complianceRouter);
app.use('/api/v1/notifications', authLimiter, notificationsRouter);
app.use('/api/v1/team', authLimiter, teamRouter);
app.use('/api/v1/tasks', authLimiter, tasksRouter);
app.use('/api/v1/dashboard', authLimiter, dashboardRouter);
app.use('/api/v1/kyc', authLimiter, kycRouter);
app.use('/api/v1/pear', authLimiter, pearRouter);
app.use('/api/v1/reconciliation', authLimiter, reconciliationRouter);
app.use('/api/v1/fiat', publicLimiter, fiatRouter); // Webhooks are authenticated via HMAC signature, not JWT
app.use('/api/v1/webhooks/kyc', publicLimiter, kycWebhookRouter); // Didit webhooks authenticated via HMAC, not JWT

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

// Initialize feature flags in Redis
featureFlags.initialize().catch((err) => log.error("Feature flags init failed:", err));

// Auto-seed .env credentials into the database
p2pService.seedEnvAccountIfNeeded().catch((err) => log.error("Seed account failed:", err));

// Start real-time PnL WebSocket emitter
startPnLEmitter();

const server = httpServer.listen(PORT, () => {
  log.info(`0.Bits API server running on port ${PORT}`, {
    env: config.NODE_ENV,
    port: PORT,
  });
  
  // ── Workers decoupled to BullMQ (Phase 2) ──────────────────────────────
  // Doc ref: §Decoupling via Distributed Job Queues (citations 5, 6)
  // "total separation of worker processes from HTTP server processes"
  //
  // All background workers now run in a separate PM2 process:
  //   pm2 start dist/worker.entry.js --name 0core-workers
  //
  // This HTTP server is now STATELESS and horizontally scalable.
  // Scaling to PM2 cluster mode will NOT cause duplicate polling or IP bans.
  log.info('HTTP server is worker-free. Background jobs managed by BullMQ.');
});

// ── Graceful Shutdown ────────────────────────────────

async function shutdown(signal: string) {
  log.info(`${signal} received — shutting down gracefully...`);

  server.close(async () => {
    log.info('HTTP server closed');
    await disconnectRedis();
    await disconnectDatabase();
    log.info('All connections closed');
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
