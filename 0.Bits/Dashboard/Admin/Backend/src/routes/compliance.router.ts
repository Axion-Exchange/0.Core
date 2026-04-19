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

export { router as complianceRouter };
