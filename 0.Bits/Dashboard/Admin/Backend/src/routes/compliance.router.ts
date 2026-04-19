import { Router } from 'express';
import { complianceService } from '../services/compliance.service.js';
import { requireAuth, requireRole } from '../middleware/auth.js';
import { sendSuccess, sendPaginated } from '../lib/response.js';
import { buildPaginationMeta } from '../lib/pagination.js';

const router = Router();
router.use(requireAuth);
router.use(requireRole('ADMIN', 'SUPER_ADMIN'));

// GET /audit-trail — Full audit log
router.get('/audit-trail', async (req, res, next) => {
  try {
    const page = Number(req.query['page'] ?? 1);
    const limit = Number(req.query['limit'] ?? 50);
    const result = await complianceService.getAuditTrail({
      adminId: req.query['adminId'] as string | undefined,
      action: req.query['action'] as string | undefined,
      resource: req.query['resource'] as string | undefined,
      from: req.query['from'] ? new Date(req.query['from'] as string) : undefined,
      to: req.query['to'] ? new Date(req.query['to'] as string) : undefined,
      page,
      limit,
    });
    const meta = buildPaginationMeta({ page: result.page, limit: result.limit, skip: 0 }, result.total);
    sendPaginated(res, result.data, meta);
  } catch (err) { next(err); }
});

// GET /reports/summary — Global compliance summary
router.get('/reports/summary', async (_req, res, next) => {
  try {
    const summary = await complianceService.getSummary();
    sendSuccess(res, summary);
  } catch (err) { next(err); }
});

// GET /reports/daily-pnl — Daily P&L breakdown
router.get('/reports/daily-pnl', async (req, res, next) => {
  try {
    const days = Number(req.query['days'] ?? 14);
    const pnl = await complianceService.getDailyPnl(days);
    sendSuccess(res, pnl);
  } catch (err) { next(err); }
});

// GET /reports/counterparty-matrix — Top counterparties by volume
router.get('/reports/counterparty-matrix', async (req, res, next) => {
  try {
    const limit = Number(req.query['limit'] ?? 20);
    const matrix = await complianceService.getCounterpartyMatrix(limit);
    sendSuccess(res, matrix);
  } catch (err) { next(err); }
});

// GET /reports/export — CSV export of audit trail
router.get('/reports/export', async (req, res, next) => {
  try {
    const data = await complianceService.exportAuditCsv({
      from: req.query['from'] ? new Date(req.query['from'] as string) : undefined,
      to: req.query['to'] ? new Date(req.query['to'] as string) : undefined,
    });

    // Return as JSON (frontend converts to CSV) or set CSV headers
    if (req.query['format'] === 'csv') {
      const headers = Object.keys(data[0] ?? {}).join(',');
      const rows = data.map((row) => Object.values(row).join(','));
      res.setHeader('Content-Type', 'text/csv');
      res.setHeader('Content-Disposition', `attachment; filename=audit-export-${new Date().toISOString().slice(0, 10)}.csv`);
      res.send([headers, ...rows].join('\n'));
    } else {
      sendSuccess(res, data);
    }
  } catch (err) { next(err); }
});

export { router as complianceRouter };
