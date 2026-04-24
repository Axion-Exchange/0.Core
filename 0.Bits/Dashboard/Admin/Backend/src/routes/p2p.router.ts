import { Router } from 'express';
import { p2pService } from '../services/p2p.service.js';
import { validateBody, validateParams } from '../middleware/validate.js';
import { requireAuth, optionalAuth } from '../middleware/auth.js';
import { auditLog } from '../middleware/audit.js';
import { idParamSchema, param } from '../validators/common.schema.js';
import { createAdSchema, updateAdSchema, toggleAdSchema, createAccountSchema, createDisputeSchema, resolveDisputeSchema, createPaymentMethodSchema } from '../validators/p2p.schema.js';
import { sendSuccess, sendPaginated } from '../lib/response.js';
import { buildPaginationMeta } from '../lib/pagination.js';

const router = Router();

// All P2P routes require authentication (except GET /accounts for now)
router.use(auditLog);

// ── Accounts ─────────────────────────────────────────

router.get('/accounts', optionalAuth, async (_req, res, next) => {
  try {
    const accounts = await p2pService.listAccounts();
    sendSuccess(res, accounts);
  } catch (err) { next(err); }
});

// P2P Mutations require strict authentication

router.post('/accounts', optionalAuth, validateBody(createAccountSchema), async (req, res, next) => {
  try {
    const account = await p2pService.createAccount(req.body);
    sendSuccess(res, account, 201);
  } catch (err) { next(err); }
});

router.get('/ads', optionalAuth, async (req, res, next) => {
  try {
    const result = await p2pService.listAds(req.query as any);
    const meta = buildPaginationMeta({ page: result.page, limit: result.limit, skip: 0 }, result.total);
    sendPaginated(res, result.data, { ...meta, ...result.meta });
  } catch (err) { next(err); }
});

router.get('/orders', optionalAuth, async (req, res, next) => {
  try {
    const result = await p2pService.listOrders(req.query as any);
    const meta = buildPaginationMeta({ page: result.page, limit: result.limit, skip: 0 }, result.total);
    sendPaginated(res, result.data, meta);
  } catch (err) { next(err); }
});

router.get('/orders/:id', optionalAuth, validateParams(idParamSchema), async (req, res, next) => {
  try {
    const order = await p2pService.getOrder(param(req, 'id'));
    sendSuccess(res, order);
  } catch (err) { next(err); }
});

router.use(requireAuth);

router.put('/accounts/:id', requireAuth, validateParams(idParamSchema), async (req, res, next) => {
  try {
    const account = await p2pService.updateAccount(param(req, 'id'), req.body);
    sendSuccess(res, account);
  } catch (err) { next(err); }
});

router.delete('/accounts/:id', requireAuth, validateParams(idParamSchema), async (req, res, next) => {
  try {
    await p2pService.deleteAccount(param(req, 'id'));
    sendSuccess(res, { message: 'Account deleted' });
  } catch (err) { next(err); }
});

// ── Advertisements ───────────────────────────────────



router.post('/ads', requireAuth, validateBody(createAdSchema), async (req, res, next) => {
  try {
    const ad = await p2pService.createAd(req.body);
    sendSuccess(res, ad, 201);
  } catch (err) { next(err); }
});

router.put('/ads/:id', requireAuth, validateParams(idParamSchema), validateBody(updateAdSchema), async (req, res, next) => {
  try {
    const ad = await p2pService.updateAd(param(req, 'id'), req.body);
    sendSuccess(res, ad);
  } catch (err) { next(err); }
});

router.put('/ads/:id/toggle', requireAuth, validateParams(idParamSchema), validateBody(toggleAdSchema), async (req, res, next) => {
  try {
    const ad = await p2pService.toggleAd(param(req, 'id'), req.body.enabled);
    sendSuccess(res, ad);
  } catch (err) { next(err); }
});



router.put('/orders/:id/release', requireAuth, validateParams(idParamSchema), async (req, res, next) => {
  try {
    const order = await p2pService.updateOrderStatus(param(req, 'id'), 'RELEASED');
    sendSuccess(res, order);
  } catch (err) { next(err); }
});

router.put('/orders/:id/cancel', validateParams(idParamSchema), async (req, res, next) => {
  try {
    const order = await p2pService.updateOrderStatus(param(req, 'id'), 'CANCELLED');
    sendSuccess(res, order);
  } catch (err) { next(err); }
});

// ── Disputes ─────────────────────────────────────────

router.get('/disputes', async (req, res, next) => {
  try {
    const result = await p2pService.listDisputes(req.query as any);
    const meta = buildPaginationMeta({ page: result.page, limit: result.limit, skip: 0 }, result.total);
    sendPaginated(res, result.data, meta);
  } catch (err) { next(err); }
});

router.post('/disputes', validateBody(createDisputeSchema), async (req, res, next) => {
  try {
    const dispute = await p2pService.createDispute({
      ...req.body,
      filedBy: req.admin!.email,
    });
    sendSuccess(res, dispute, 201);
  } catch (err) { next(err); }
});

router.put('/disputes/:id/resolve', validateParams(idParamSchema), validateBody(resolveDisputeSchema), async (req, res, next) => {
  try {
    const dispute = await p2pService.resolveDispute(param(req, 'id'), {
      ...req.body,
      adminId: req.admin!.sub,
    });
    sendSuccess(res, dispute);
  } catch (err) { next(err); }
});

// ── Payment Methods ──────────────────────────────────

router.get('/payment-methods', async (_req, res, next) => {
  try {
    const methods = await p2pService.listPaymentMethods();
    sendSuccess(res, methods);
  } catch (err) { next(err); }
});

router.post('/payment-methods', validateBody(createPaymentMethodSchema), async (req, res, next) => {
  try {
    const method = await p2pService.createPaymentMethod(req.body);
    sendSuccess(res, method, 201);
  } catch (err) { next(err); }
});

router.put('/payment-methods/:id', validateParams(idParamSchema), async (req, res, next) => {
  try {
    const method = await p2pService.updatePaymentMethod(param(req, 'id'), req.body);
    sendSuccess(res, method);
  } catch (err) { next(err); }
});

router.delete('/payment-methods/:id', validateParams(idParamSchema), async (req, res, next) => {
  try {
    await p2pService.deletePaymentMethod(param(req, 'id'));
    sendSuccess(res, { message: 'Payment method deleted' });
  } catch (err) { next(err); }
});

export { router as p2pRouter };
