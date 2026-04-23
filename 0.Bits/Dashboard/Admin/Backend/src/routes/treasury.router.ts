import { Router } from 'express';
import { treasuryService } from '../services/treasury.service.js';
import { optionalAuth } from '../middleware/auth.js';
import { validateQuery, validateParams } from '../middleware/validate.js';
import { idParamSchema, param } from '../validators/common.schema.js';
import { transactionQuerySchema, balanceHistorySchema } from '../validators/treasury.schema.js';
import { sendSuccess, sendPaginated } from '../lib/response.js';
import { buildPaginationMeta } from '../lib/pagination.js';

const router = Router();
router.use(optionalAuth);

// GET /portfolio — Aggregated NAV across all currencies
router.get('/portfolio', async (req, res, next) => {
  try {
    const summary = await treasuryService.getPortfolioSummary(req.query.accountId as string);
    sendSuccess(res, summary);
  } catch (err) { next(err); }
});

// GET /portfolio/:currency — Single currency breakdown
router.get('/portfolio/:currency', async (req, res, next) => {
  try {
    const portfolio = await treasuryService.getPortfolioByCurrency(param(req, 'currency'));
    sendSuccess(res, portfolio);
  } catch (err) { next(err); }
});

// GET /balances — Live exchange + fiat balances
router.get('/balances', async (req, res, next) => {
  try {
    const balances = await treasuryService.getBalances(req.query.accountId as string);
    sendSuccess(res, balances);
  } catch (err) { next(err); }
});

// GET /balances-aggregated — For React Frontend Integration (Balances Page)
router.get('/balances-aggregated', async (req, res, next) => {
  try {
    const data = await treasuryService.getAggregatedPortfolioView(req.query.accountId as string);
    sendSuccess(res, data);
  } catch(err) { next(err); }
});

// GET /crypto-balances — For React Frontend Integration (Crypto Portfolio Page)
router.get('/crypto-balances', async (req, res, next) => {
  try {
    const data = await treasuryService.getCryptoBalances();
    sendSuccess(res, data);
  } catch(err) { next(err); }
});

// GET /balances/history — Historical snapshots for charts
router.get('/balances/history', validateQuery(balanceHistorySchema), async (req, res, next) => {
  try {
    const { currency, days } = req.query as any;
    const history = await treasuryService.getBalanceHistory(currency, days);
    sendSuccess(res, history);
  } catch (err) { next(err); }
});

// GET /transactions — Unified transaction ledger
router.get('/transactions', validateQuery(transactionQuerySchema), async (req, res, next) => {
  try {
    const result = await treasuryService.listTransactions(req.query as any);
    const meta = buildPaginationMeta({ page: result.page, limit: result.limit, skip: 0 }, result.total);
    sendPaginated(res, result.data, meta);
  } catch (err) { next(err); }
});

// GET /transactions/:id — Transaction detail
router.get('/transactions/:id', validateParams(idParamSchema), async (req, res, next) => {
  try {
    const tx = await treasuryService.getTransaction(param(req, 'id'));
    sendSuccess(res, tx);
  } catch (err) { next(err); }
});

// POST /sync — Trigger manual balance sync
router.post('/sync', async (_req, res, next) => {
  try {
    sendSuccess(res, { message: 'Sync triggered', timestamp: new Date().toISOString() });
  } catch (err) { next(err); }
});

export { router as treasuryRouter };
