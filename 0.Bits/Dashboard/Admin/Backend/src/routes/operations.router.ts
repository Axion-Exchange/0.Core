import { Router } from 'express';
import { operationsService } from '../services/operations.service.js';
import { requireAuth, requireRole } from '../middleware/auth.js';
import { auditLog } from '../middleware/audit.js';
import { validateBody, validateParams, validateQuery } from '../middleware/validate.js';
import { idParamSchema, param } from '../validators/common.schema.js';
import { createApiKeySchema, registerNodeSchema, nodeHeartbeatSchema, logQuerySchema } from '../validators/operations.schema.js';
import { sendSuccess, sendPaginated } from '../lib/response.js';
import { buildPaginationMeta } from '../lib/pagination.js';

const router = Router();
router.use(requireAuth);

// ── Health ───────────────────────────────────────────

router.get('/health', async (_req, res, next) => {
  try {
    const health = await operationsService.getSystemHealth();
    sendSuccess(res, health);
  } catch (err) { next(err); }
});

// ── API Keys ─────────────────────────────────────────

router.get('/api-keys', requireRole('ADMIN', 'SUPER_ADMIN'), async (_req, res, next) => {
  try {
    const keys = await operationsService.listApiKeys();
    sendSuccess(res, keys);
  } catch (err) { next(err); }
});

router.post('/api-keys', requireRole('SUPER_ADMIN'), auditLog, validateBody(createApiKeySchema), async (req, res, next) => {
  try {
    const key = await operationsService.createApiKey({
      ...req.body,
      createdById: req.admin!.sub,
    });
    sendSuccess(res, key, 201);
  } catch (err) { next(err); }
});

router.delete('/api-keys/:id', requireRole('SUPER_ADMIN'), auditLog, validateParams(idParamSchema), async (req, res, next) => {
  try {
    await operationsService.revokeApiKey(param(req, 'id'));
    sendSuccess(res, { message: 'API key revoked' });
  } catch (err) { next(err); }
});

// ── Nodes ────────────────────────────────────────────

router.get('/nodes', async (_req, res, next) => {
  try {
    const nodes = await operationsService.listNodes();
    sendSuccess(res, nodes);
  } catch (err) { next(err); }
});

router.post('/nodes', auditLog, validateBody(registerNodeSchema), async (req, res, next) => {
  try {
    const node = await operationsService.registerNode(req.body);
    sendSuccess(res, node, 201);
  } catch (err) { next(err); }
});

router.put('/nodes/:id/heartbeat', validateParams(idParamSchema), validateBody(nodeHeartbeatSchema), async (req, res, next) => {
  try {
    const node = await operationsService.nodeHeartbeat(param(req, 'id'), req.body);
    sendSuccess(res, node);
  } catch (err) { next(err); }
});

// ── Logs ─────────────────────────────────────────────

router.get('/logs', validateQuery(logQuerySchema), async (req, res, next) => {
  try {
    const result = await operationsService.listLogs(req.query as any);
    const meta = buildPaginationMeta({ page: result.page, limit: result.limit, skip: 0 }, result.total);
    sendPaginated(res, result.data, meta);
  } catch (err) { next(err); }
});


// ── Health Dashboard (Institutional Monitoring) ──────

import { getHealthDashboard, runAllHealthChecks, getServiceHistory } from '../services/health-checker.service.js';

router.get('/health/dashboard', async (_req, res, next) => {
  try {
    const dashboard = await getHealthDashboard();
    sendSuccess(res, dashboard);
  } catch (err) { next(err); }
});

router.post('/health/run', requireRole('ADMIN', 'SUPER_ADMIN'), async (_req, res, next) => {
  try {
    const results = await runAllHealthChecks();
    sendSuccess(res, results);
  } catch (err) { next(err); }
});

router.get('/health/history/:service', async (req, res, next) => {
  try {
    const history = await getServiceHistory(req.params.service, 30);
    sendSuccess(res, history);
  } catch (err) { next(err); }
});

export { router as operationsRouter };
