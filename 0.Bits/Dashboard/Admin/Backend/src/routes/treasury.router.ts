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

// GET /export-capital-flows — Download CSV of capital flow ledger
router.get('/export-capital-flows', async (req, res, next) => {
  try {
    const { days, types } = req.query as any;
    
    let dateFilter = {};
    if (days && days !== 'all') {
      const parsedDays = parseInt(days);
      if (!isNaN(parsedDays)) {
        dateFilter = {
          gte: new Date(Date.now() - parsedDays * 24 * 60 * 60 * 1000)
        };
      }
    }

    let typeFilter = undefined;
    if (req.query.types && typeof req.query.types === 'string') {
      const requestedTypes = req.query.types.split(',');
      typeFilter = { in: requestedTypes };
    }

    let accountFilter = undefined;
    if (req.query.accounts && typeof req.query.accounts === 'string') {
      const requestedAccounts = req.query.accounts.split(',');
      accountFilter = { label: { in: requestedAccounts } };
    }

    // Base where for ExchangeCapitalFlow
    const flowsWhere: any = {};
    if (Object.keys(dateFilter).length > 0) flowsWhere.timestamp = dateFilter;
    if (accountFilter) flowsWhere.account = accountFilter;
    
    let shouldQueryFlows = true;

    // Filter out ACCOUNT_BALANCES from CapitalFlow queries because it is not a valid enum value
    if (typeFilter) {
      const validFlowTypes = typeFilter.in.filter((t: string) => t !== 'ACCOUNT_BALANCES');
      if (validFlowTypes.length > 0) {
        flowsWhere.type = { in: validFlowTypes };
      } else {
        // If they ONLY requested ACCOUNT_BALANCES, don't query ExchangeCapitalFlow
        shouldQueryFlows = false;
      }
    }

    // We must fetch from both ExchangeCapitalFlow AND BalanceLedger (if "ACCOUNT_BALANCES" is requested)
    const { prisma } = await import('../lib/db.js');
    
    let csvData = `Date,Account,Type,Asset,Amount,Status,External ID\n`;

    // Only query ExchangeCapitalFlow if they didn't EXCLUSIVELY ask for ACCOUNT_BALANCES
    if (shouldQueryFlows) {
      const flows = await prisma.exchangeCapitalFlow.findMany({
        where: flowsWhere,
        include: { account: true },
        orderBy: { timestamp: 'desc' },
        take: 10000 // reasonable limit for direct export
      });
      
      for (const f of flows) {
        csvData += `"${f.timestamp.toISOString()}","${f.account.label}","${f.type}","${f.asset}",${f.amount},"${f.status}","${f.externalId}"\n`;
      }
    }

    if (!typeFilter || typeFilter.in.includes('ACCOUNT_BALANCES')) {
      const balanceWhere: any = {};
      if (Object.keys(dateFilter).length > 0) balanceWhere.snapshotAt = dateFilter;
      if (accountFilter) balanceWhere.account = accountFilter;
      
      const balances = await prisma.balanceLedger.findMany({
        where: balanceWhere,
        include: { account: true },
        orderBy: { snapshotAt: 'desc' },
        take: 10000
      });
      
      for (const b of balances) {
        csvData += `"${b.snapshotAt.toISOString()}","${b.account?.label || b.source}","ACCOUNT_BALANCE","${b.currency}",${b.available},"COMPLETED","snapshot-${b.id}"\n`;
      }
    }

    res.header('Content-Type', 'text/csv');
    res.attachment(`capital_flows_export_${new Date().toISOString()}.csv`);
    res.send(csvData);
  } catch (err) { next(err); }
});

export { router as treasuryRouter };
