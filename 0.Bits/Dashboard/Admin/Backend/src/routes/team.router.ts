import { Router } from 'express';
import { teamService } from '../services/team.service.js';
import { requireAuth } from '../middleware/auth.js';
import { auditLog } from '../middleware/audit.js';
import { validateBody, validateParams, validateQuery } from '../middleware/validate.js';
import { idParamSchema, param } from '../validators/common.schema.js';
import { createMemberSchema, updateMemberSchema, createMeetingSchema, createScheduleSchema, createTaskSchema, updateTaskSchema, taskQuerySchema } from '../validators/team.schema.js';
import { sendSuccess, sendPaginated } from '../lib/response.js';
import { buildPaginationMeta } from '../lib/pagination.js';

const router = Router();
router.use(requireAuth);
router.use(auditLog);

// ── Members ──────────────────────────────────────────

router.get('/members', async (_req, res, next) => {
  try {
    const members = await teamService.listMembers();
    sendSuccess(res, members);
  } catch (err) { next(err); }
});

router.post('/members', validateBody(createMemberSchema), async (req, res, next) => {
  try {
    const member = await teamService.createMember(req.body);
    sendSuccess(res, member, 201);
  } catch (err) { next(err); }
});

router.put('/members/:id', validateParams(idParamSchema), validateBody(updateMemberSchema), async (req, res, next) => {
  try {
    const member = await teamService.updateMember(param(req, 'id'), req.body);
    sendSuccess(res, member);
  } catch (err) { next(err); }
});

router.delete('/members/:id', validateParams(idParamSchema), async (req, res, next) => {
  try {
    await teamService.deleteMember(param(req, 'id'));
    sendSuccess(res, { message: 'Member removed' });
  } catch (err) { next(err); }
});

// ── Meetings ─────────────────────────────────────────

router.get('/meetings', async (req, res, next) => {
  try {
    const page = Number(req.query['page'] ?? 1);
    const limit = Number(req.query['limit'] ?? 25);
    const result = await teamService.listMeetings({ ...req.query as any, page, limit });
    const meta = buildPaginationMeta({ page: result.page, limit: result.limit, skip: 0 }, result.total);
    sendPaginated(res, result.data, meta);
  } catch (err) { next(err); }
});

router.post('/meetings', validateBody(createMeetingSchema), async (req, res, next) => {
  try {
    const meeting = await teamService.createMeeting(req.body);
    sendSuccess(res, meeting, 201);
  } catch (err) { next(err); }
});

router.put('/meetings/:id', validateParams(idParamSchema), async (req, res, next) => {
  try {
    const meeting = await teamService.updateMeeting(param(req, 'id'), req.body);
    sendSuccess(res, meeting);
  } catch (err) { next(err); }
});

router.delete('/meetings/:id', validateParams(idParamSchema), async (req, res, next) => {
  try {
    await teamService.deleteMeeting(param(req, 'id'));
    sendSuccess(res, { message: 'Meeting deleted' });
  } catch (err) { next(err); }
});

// ── Schedules ────────────────────────────────────────

router.get('/schedules', async (req, res, next) => {
  try {
    const schedules = await teamService.listSchedules(req.query as any);
    sendSuccess(res, schedules);
  } catch (err) { next(err); }
});

router.post('/schedules', validateBody(createScheduleSchema), async (req, res, next) => {
  try {
    const schedule = await teamService.createSchedule(req.body);
    sendSuccess(res, schedule, 201);
  } catch (err) { next(err); }
});

router.put('/schedules/:id', validateParams(idParamSchema), async (req, res, next) => {
  try {
    const schedule = await teamService.updateSchedule(param(req, 'id'), req.body);
    sendSuccess(res, schedule);
  } catch (err) { next(err); }
});

router.delete('/schedules/:id', validateParams(idParamSchema), async (req, res, next) => {
  try {
    await teamService.deleteSchedule(param(req, 'id'));
    sendSuccess(res, { message: 'Schedule deleted' });
  } catch (err) { next(err); }
});

export { router as teamRouter };
