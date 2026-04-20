import { Router } from 'express';
import { dashboardService } from '../services/dashboard.service.js';
import { optionalAuth } from '../middleware/auth.js';
import { sendSuccess } from '../lib/response.js';

const router = Router();
router.use(optionalAuth);

// GET /summary — Aggregated home dashboard metrics
router.get('/summary', async (_req, res, next) => {
  try {
    const summary = await dashboardService.getSummary();
    sendSuccess(res, summary);
  } catch (err) { next(err); }
});

// GET /transactions — High definition P2P orders for the frontend Tremor charts
router.get('/transactions', async (_req, res, next) => {
  try {
    const tx = await dashboardService.getTransactions();
    sendSuccess(res, tx);
  } catch (err) { next(err); }
});

// GET /users — Clean Counterparty mapping natively extracting unique Binancial strings
router.get('/users', async (_req, res, next) => {
  try {
    const users = await dashboardService.getUsers();
    sendSuccess(res, users);
  } catch (err) { next(err); }
});

export { router as dashboardRouter };
