import { Router } from 'express';
import { userService } from '../services/user.service.js';
import { requireAuth, requireRole } from '../middleware/auth.js';
import { auditLog } from '../middleware/audit.js';
import { validateBody, validateParams, validateQuery } from '../middleware/validate.js';
import { idParamSchema, param } from '../validators/common.schema.js';
import { createUserSchema, updateUserSchema, freezeUserSchema, blockUserSchema, kycDecisionSchema, userListQuerySchema } from '../validators/user.schema.js';
import { sendSuccess, sendPaginated } from '../lib/response.js';
import { buildPaginationMeta } from '../lib/pagination.js';

const router = Router();
router.use(requireAuth);
router.use(auditLog);

// GET / — List users
router.get('/', validateQuery(userListQuerySchema), async (req, res, next) => {
  try {
    const result = await userService.list(req.query as any);
    const meta = buildPaginationMeta({ page: result.page, limit: result.limit, skip: 0 }, result.total);
    sendPaginated(res, result.data, meta);
  } catch (err) { next(err); }
});

// GET /:id — User detail
router.get('/:id', validateParams(idParamSchema), async (req, res, next) => {
  try {
    const user = await userService.getById(param(req, 'id'));
    sendSuccess(res, user);
  } catch (err) { next(err); }
});

// POST / — Create user
router.post('/', validateBody(createUserSchema), async (req, res, next) => {
  try {
    const user = await userService.create(req.body);
    sendSuccess(res, user, 201);
  } catch (err) { next(err); }
});

// PUT /:id — Update user
router.put('/:id', validateParams(idParamSchema), validateBody(updateUserSchema), async (req, res, next) => {
  try {
    const user = await userService.update(param(req, 'id'), req.body);
    sendSuccess(res, user);
  } catch (err) { next(err); }
});

// PUT /:id/freeze — Freeze/unfreeze
router.put('/:id/freeze', validateParams(idParamSchema), validateBody(freezeUserSchema), async (req, res, next) => {
  try {
    const user = await userService.freeze(param(req, 'id'), req.body.frozen);
    sendSuccess(res, user);
  } catch (err) { next(err); }
});

// PUT /:id/block — Block/unblock
router.put('/:id/block', validateParams(idParamSchema), validateBody(blockUserSchema), async (req, res, next) => {
  try {
    const user = await userService.block(param(req, 'id'), req.body.blocked, req.body.reason);
    sendSuccess(res, user);
  } catch (err) { next(err); }
});

// GET /kyc/pending — KYC submissions list
router.get('/kyc/pending', async (req, res, next) => {
  try {
    const page = Number(req.query['page'] ?? 1);
    const limit = Number(req.query['limit'] ?? 25);
    const result = await userService.listByKycStatus('PENDING', page, limit);
    const meta = buildPaginationMeta({ page: result.page, limit: result.limit, skip: 0 }, result.total);
    sendPaginated(res, result.data, meta);
  } catch (err) { next(err); }
});

// PUT /kyc/:id/approve
router.put('/kyc/:id/approve', requireRole('ADMIN', 'SUPER_ADMIN'), validateParams(idParamSchema), async (req, res, next) => {
  try {
    await userService.approveKyc(param(req, 'id'), req.admin!.sub);
    sendSuccess(res, { message: 'KYC approved' });
  } catch (err) { next(err); }
});

// PUT /kyc/:id/reject
router.put('/kyc/:id/reject', requireRole('ADMIN', 'SUPER_ADMIN'), validateParams(idParamSchema), validateBody(kycDecisionSchema), async (req, res, next) => {
  try {
    await userService.rejectKyc(param(req, 'id'), req.admin!.sub, req.body.rejectionReason);
    sendSuccess(res, { message: 'KYC rejected' });
  } catch (err) { next(err); }
});

// GET /blocked/list — Blocked users
router.get('/blocked/list', async (req, res, next) => {
  try {
    const page = Number(req.query['page'] ?? 1);
    const limit = Number(req.query['limit'] ?? 25);
    const result = await userService.listBlocked(page, limit);
    const meta = buildPaginationMeta({ page: result.page, limit: result.limit, skip: 0 }, result.total);
    sendPaginated(res, result.data, meta);
  } catch (err) { next(err); }
});

// ── KYB ──────────────────────────────────────────────

// GET /kyb/pending — KYB submissions list
router.get('/kyb/pending', async (req, res, next) => {
  try {
    const page = Number(req.query['page'] ?? 1);
    const limit = Number(req.query['limit'] ?? 25);
    const result = await userService.listByKybStatus('PENDING', page, limit);
    const meta = buildPaginationMeta({ page: result.page, limit: result.limit, skip: 0 }, result.total);
    sendPaginated(res, result.data, meta);
  } catch (err) { next(err); }
});

// PUT /kyb/:id/approve
router.put('/kyb/:id/approve', requireRole('ADMIN', 'SUPER_ADMIN'), validateParams(idParamSchema), async (req, res, next) => {
  try {
    await userService.approveKyb(param(req, 'id'), req.admin!.sub);
    sendSuccess(res, { message: 'KYB approved' });
  } catch (err) { next(err); }
});

// PUT /kyb/:id/reject
router.put('/kyb/:id/reject', requireRole('ADMIN', 'SUPER_ADMIN'), validateParams(idParamSchema), validateBody(kycDecisionSchema), async (req, res, next) => {
  try {
    await userService.rejectKyb(param(req, 'id'), req.admin!.sub, req.body.rejectionReason);
    sendSuccess(res, { message: 'KYB rejected' });
  } catch (err) { next(err); }
});

// ── Transaction type filters ─────────────────────────

// GET /transactions/buy — Buy transactions only
router.get('/transactions/buy', async (req, res, next) => {
  try {
    const page = Number(req.query['page'] ?? 1);
    const limit = Number(req.query['limit'] ?? 25);
    const result = await userService.listBuyTransactions(page, limit);
    const meta = buildPaginationMeta({ page: result.page, limit: result.limit, skip: 0 }, result.total);
    sendPaginated(res, result.data, meta);
  } catch (err) { next(err); }
});

// GET /transactions/sell — Sell transactions only
router.get('/transactions/sell', async (req, res, next) => {
  try {
    const page = Number(req.query['page'] ?? 1);
    const limit = Number(req.query['limit'] ?? 25);
    const result = await userService.listSellTransactions(page, limit);
    const meta = buildPaginationMeta({ page: result.page, limit: result.limit, skip: 0 }, result.total);
    sendPaginated(res, result.data, meta);
  } catch (err) { next(err); }
});

export { router as usersRouter };
