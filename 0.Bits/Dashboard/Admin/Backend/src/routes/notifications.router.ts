import { Router } from 'express';
import { notificationService } from '../services/notification.service.js';
import { requireAuth } from '../middleware/auth.js';
import { validateParams } from '../middleware/validate.js';
import { idParamSchema, param } from '../validators/common.schema.js';
import { sendSuccess, sendPaginated } from '../lib/response.js';
import { buildPaginationMeta } from '../lib/pagination.js';

const router = Router();
router.use(requireAuth);

// GET / — List notifications for current admin
router.get('/', async (req, res, next) => {
  try {
    const page = Number(req.query['page'] ?? 1);
    const limit = Number(req.query['limit'] ?? 25);
    const result = await notificationService.listForAdmin(req.admin!.sub, page, limit);
    const meta = buildPaginationMeta({ page: result.page, limit: result.limit, skip: 0 }, result.total);
    sendPaginated(res, result.data, meta);
  } catch (err) { next(err); }
});

// GET /unread-count — Badge count
router.get('/unread-count', async (req, res, next) => {
  try {
    const count = await notificationService.getUnreadCount(req.admin!.sub);
    sendSuccess(res, { count });
  } catch (err) { next(err); }
});

// PUT /:id/read — Mark single notification as read
router.put('/:id/read', validateParams(idParamSchema), async (req, res, next) => {
  try {
    await notificationService.markAsRead(param(req, 'id'), req.admin!.sub);
    sendSuccess(res, { message: 'Marked as read' });
  } catch (err) { next(err); }
});

// PUT /read-all — Mark all as read
router.put('/read-all', async (req, res, next) => {
  try {
    await notificationService.markAllAsRead(req.admin!.sub);
    sendSuccess(res, { message: 'All notifications marked as read' });
  } catch (err) { next(err); }
});

export { router as notificationsRouter };
