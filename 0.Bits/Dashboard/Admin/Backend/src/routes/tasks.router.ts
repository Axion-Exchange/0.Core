import { Router } from 'express';
import { teamService } from '../services/team.service.js';
import { requireAuth } from '../middleware/auth.js';
import { auditLog } from '../middleware/audit.js';
import { validateBody, validateParams, validateQuery } from '../middleware/validate.js';
import { idParamSchema, param } from '../validators/common.schema.js';
import { createTaskSchema, updateTaskSchema, taskQuerySchema } from '../validators/team.schema.js';
import { sendSuccess, sendPaginated } from '../lib/response.js';
import { buildPaginationMeta } from '../lib/pagination.js';

const router = Router();
router.use(requireAuth);
router.use(auditLog);

// GET / — List tasks
router.get('/', validateQuery(taskQuerySchema), async (req, res, next) => {
  try {
    const result = await teamService.listTasks(req.query as any);
    const meta = buildPaginationMeta({ page: result.page, limit: result.limit, skip: 0 }, result.total);
    sendPaginated(res, result.data, meta);
  } catch (err) { next(err); }
});

// POST / — Create task
router.post('/', validateBody(createTaskSchema), async (req, res, next) => {
  try {
    const task = await teamService.createTask({
      ...req.body,
      reporterId: req.admin!.sub,
      reporterName: req.admin!.email,
    });
    sendSuccess(res, task, 201);
  } catch (err) { next(err); }
});

// PUT /:id — Update task
router.put('/:id', validateParams(idParamSchema), validateBody(updateTaskSchema), async (req, res, next) => {
  try {
    const task = await teamService.updateTask(param(req, 'id'), req.body);
    sendSuccess(res, task);
  } catch (err) { next(err); }
});

// DELETE /:id — Delete task
router.delete('/:id', validateParams(idParamSchema), async (req, res, next) => {
  try {
    await teamService.deleteTask(param(req, 'id'));
    sendSuccess(res, { message: 'Task deleted' });
  } catch (err) { next(err); }
});

export { router as tasksRouter };
