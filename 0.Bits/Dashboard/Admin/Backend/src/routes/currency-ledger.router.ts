/**
 * Currency Ledger Router
 * 
 * Per-currency (EUR / COP / MXN) endpoints for the institutional
 * treasury dashboard tabs.
 */
import { Router } from 'express';
import { currencyLedgerService } from '../services/currency-ledger.service.js';
import { optionalAuth } from '../middleware/auth.js';
import { sendSuccess, sendPaginated } from '../lib/response.js';
import { buildPaginationMeta } from '../lib/pagination.js';

const router = Router();
router.use(optionalAuth);

const VALID_FIATS = ['EUR', 'COP', 'MXN'];

// GET /currency/:fiat/summary — Balance card data
router.get('/:fiat/summary', async (req, res, next): Promise<void> => {
  try {
    const fiat = req.params.fiat?.toUpperCase();
    if (!VALID_FIATS.includes(fiat)) {
      res.status(400).json({ success: false, error: { code: 'INVALID_FIAT', message: `Supported: ${VALID_FIATS.join(', ')}` }});
    }
    const summary = await currencyLedgerService.getBalanceSummary(fiat);
    sendSuccess(res, summary);
  } catch (err) { next(err); }
});

// GET /currency/:fiat/metrics — Daily chart card data
router.get('/:fiat/metrics', async (req, res, next): Promise<void> => {
  try {
    const fiat = req.params.fiat?.toUpperCase();
    if (!VALID_FIATS.includes(fiat)) {
      res.status(400).json({ success: false, error: { code: 'INVALID_FIAT', message: `Supported: ${VALID_FIATS.join(', ')}` }});
    }
    const from = req.query.from ? new Date(req.query.from as string) : undefined;
    const to = req.query.to ? new Date(req.query.to as string) : undefined;
    const metrics = await currencyLedgerService.getDailyMetrics(fiat, from, to);
    sendSuccess(res, metrics);
  } catch (err) { next(err); }
});

// GET /currency/:fiat/orders — P2P orders table
router.get('/:fiat/orders', async (req, res, next): Promise<void> => {
  try {
    const fiat = req.params.fiat?.toUpperCase();
    if (!VALID_FIATS.includes(fiat)) {
      res.status(400).json({ success: false, error: { code: 'INVALID_FIAT', message: `Supported: ${VALID_FIATS.join(', ')}` }});
    }
    const limit = Math.min(parseInt(req.query.limit as string) || 50, 200);
    const page = parseInt(req.query.page as string) || 1;
    const result = await currencyLedgerService.getOrdersTable(fiat, limit, page);
    const meta = buildPaginationMeta({ page, limit, skip: (page - 1) * limit }, result.total);
    sendPaginated(res, result.data, meta);
  } catch (err) { next(err); }
});

export { router as currencyLedgerRouter };
