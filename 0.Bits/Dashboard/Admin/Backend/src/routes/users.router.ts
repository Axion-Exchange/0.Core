import { Router } from 'express';
import { userService } from '../services/user.service.js';
import { kycSessionCreator } from '../services/kyc-session-creator.service.js';
import { exchangeService } from '../services/exchange.service.js';
import { prisma } from '../lib/db.js';
import { requireAuth, requireRole, optionalAuth } from '../middleware/auth.js';
import { auditLog } from '../middleware/audit.js';
import { validateBody, validateParams, validateQuery } from '../middleware/validate.js';
import { idParamSchema, param } from '../validators/common.schema.js';
import { createUserSchema, updateUserSchema, freezeUserSchema, blockUserSchema, kycDecisionSchema, userListQuerySchema } from '../validators/user.schema.js';
import { sendSuccess, sendPaginated } from '../lib/response.js';
import { buildPaginationMeta } from '../lib/pagination.js';
import archiver from 'archiver';
import { diditService } from '../services/didit.service.js';
import { z } from 'zod';

const router = Router();
router.use(optionalAuth);
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

// POST /:id/generate-kyc-link
router.post('/:id/generate-kyc-link', validateParams(idParamSchema), async (req, res, next) => {
  try {
    const result = await kycSessionCreator.createSessionForUser(param(req, 'id'));
    sendSuccess(res, result);
  } catch (err) { next(err); }
});

// POST /:id/request-kyc
router.post('/:id/request-kyc', validateParams(idParamSchema), async (req, res, next) => {
  try {
    const userId = param(req, 'id');
    const user = await userService.getById(userId);
    
    // Security Check: Only request if KYC is NOT APPROVED
    if (user.kycStatus === 'APPROVED') {
      res.status(400).json({ success: false, error: 'User is already KYC approved' });
      return;
    }

    // Spam Protection: Enforce 24-hour cooldown
    if (user.lastKycRequestedAt) {
      const hoursSinceLastRequest = (Date.now() - user.lastKycRequestedAt.getTime()) / (1000 * 60 * 60);
      if (hoursSinceLastRequest < 24) {
        const hoursLeft = Math.ceil(24 - hoursSinceLastRequest);
        res.status(429).json({ success: false, error: `Rate limited. Please wait ${hoursLeft} hours before sending another request.` });
        return;
      }
    }

    // Get the most recent order for this user
    const recentOrder = await prisma.p2POrder.findFirst({
      where: { userId },
      orderBy: { createdAt: 'desc' },
    });

    if (!recentOrder || !recentOrder.externalOrderId) {
      res.status(400).json({ success: false, error: 'No recent Binance order found to send a message to' });
      return;
    }

    // Generate link
    const session = await kycSessionCreator.createSessionForUser(userId);

    // Send chat message
    const connector = await exchangeService.getBinanceConnector(recentOrder.accountId || undefined);
    const message = `Our Banking provider is asking for your details could you please complete this: ${session.sessionUrl}`;
    await connector.sendChatMessage(recentOrder.externalOrderId, message);

    // Update last requested timestamp
    await prisma.user.update({
      where: { id: userId },
      data: { lastKycRequestedAt: new Date() }
    });

    sendSuccess(res, { message: 'KYC request sent via chat', sessionUrl: session.sessionUrl });
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
router.put('/kyc/:id/approve', validateParams(idParamSchema), async (req, res, next) => {
  try {
    await userService.approveKyc(param(req, 'id'), req.admin!.sub);
    sendSuccess(res, { message: 'KYC approved' });
  } catch (err) { next(err); }
});

// PUT /kyc/:id/reject
router.put('/kyc/:id/reject', validateParams(idParamSchema), validateBody(kycDecisionSchema), async (req, res, next) => {
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
router.put('/kyb/:id/approve', validateParams(idParamSchema), async (req, res, next) => {
  try {
    await userService.approveKyb(param(req, 'id'), req.admin!.sub);
    sendSuccess(res, { message: 'KYB approved' });
  } catch (err) { next(err); }
});

// PUT /kyb/:id/reject
router.put('/kyb/:id/reject', validateParams(idParamSchema), validateBody(kycDecisionSchema), async (req, res, next) => {
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

// POST /export-data — Bulk export user data
router.post('/export-data', async (req, res, next) => {
  try {
    const schema = z.object({
      userIds: z.array(z.string().uuid()),
      options: z.object({
        transactions: z.boolean(),
        kyc: z.boolean(),
        chats: z.boolean(),
      })
    });

    const parsed = schema.safeParse(req.body);
    if (!parsed.success) {
      res.status(400).json({ success: false, error: parsed.error });
      return;
    }

    const { userIds, options } = parsed.data;

    res.setHeader('Content-Type', 'application/zip');
    res.setHeader('Content-Disposition', 'attachment; filename="kyc_export.zip"');

    const archive = archiver('zip', { zlib: { level: 9 } });
    archive.pipe(res);

    for (const userId of userIds) {
      const user = await prisma.user.findUnique({
        where: { id: userId },
        include: { orders: true, transactions: true }
      });
      if (!user) continue;

      const folderName = `${(user.displayName || user.legalName || 'User').replace(/[^a-zA-Z0-9]/g, '_')}_${user.id.substring(0,8)}`;

      if (options.transactions && user.transactions.length > 0) {
        let csv = 'ID,Date,Amount,Currency,Type,Status\n';
        for (const tx of user.transactions) {
          csv += `${tx.id},${tx.createdAt.toISOString()},${tx.amount},${tx.currency},${tx.type},${tx.status}\n`;
        }
        archive.append(csv, { name: `${folderName}/transactions.csv` });
      }

      if (options.kyc) {
        // Find latest session
        const session = await prisma.kycSession.findFirst({
          where: { provider: { provider: 'DIDIT' } }, // Note: may need correct relation
          orderBy: { createdAt: 'desc' },
        });
        // Wait, User does not have direct kycSession link natively unless vendor_data is mapped.
        // Let's assume we fetch session by user external ID or we just fallback to user mock.
        // Actually, we can fetch all sessions and filter in memory if schema is complex, or just:
        // Actually, schema has `kycSessions` on User! (Wait, let me double check. User model had `kycSessions KycSession[]`).
        const userWithSessions = await prisma.user.findUnique({
          where: { id: userId },
          include: { kycSessions: { orderBy: { createdAt: 'desc' }, take: 1 } }
        });

        if (userWithSessions?.kycSessions && userWithSessions.kycSessions.length > 0) {
          const sessionId = userWithSessions.kycSessions[0].externalId;
          const report = await diditService.downloadSessionReport(sessionId);
          archive.append(report.data, { name: `${folderName}/kyc_report.${report.type}` });
        } else {
          // Fallback mock document
          archive.append(JSON.stringify({ note: "No KYC session found for user" }), { name: `${folderName}/kyc_report.json` });
        }
      }

      if (options.chats && user.orders.length > 0) {
        for (const order of user.orders) {
          if (!order.externalOrderId) continue;
          try {
            // we need the connector
            const connector = await exchangeService.getBinanceConnector(order.accountId || undefined);
            // SAPI chat history
            const chats = await (connector as any).client.request('c2c/chat/retrieveChatMessagesWithPagination', 'sapi', 'GET', { 
               orderNo: order.externalOrderId, page: 1, rows: 100 
            });
            let txt = `Chat Transcript for Order ${order.externalOrderId}\n\n`;
            if (chats && chats.data && Array.isArray(chats.data)) {
              for (const msg of chats.data) {
                txt += `[${new Date(msg.createTime).toISOString()}] ${msg.role}: ${msg.content}\n`;
              }
            } else {
              txt += "No messages found or API error.\n";
            }
            archive.append(txt, { name: `${folderName}/chat_${order.externalOrderId}.txt` });
          } catch (e: any) {
            archive.append(`Error fetching chat: ${e.message}`, { name: `${folderName}/chat_${order.externalOrderId}_error.txt` });
          }
        }
      }
    }

    await archive.finalize();
  } catch (err) { next(err); }
});

export { router as usersRouter };
