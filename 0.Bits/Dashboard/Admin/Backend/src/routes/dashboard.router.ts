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

import { sapiPatchService } from '../services/sapi-patch.service.js';

// POST /sync-users — Asynchronously trigger deep Binance SAPI history resolution
router.post('/sync-users', async (_req, res, next) => {
  try {
    const started = await sapiPatchService.triggerBackgroundSync();
    if (started) {
      res.status(202).json({ success: true, message: 'Deep Background SAPI Sync initiated successfully. The Dashboard cache will organically populate.' });
    } else {
      res.status(409).json({ success: false, message: 'Sync is physically already running sequentially.' });
    }
  } catch (err) { next(err); }
});

// GET /sync-users/status — Polling hook for UI mapping
router.get('/sync-users/status', async (_req, res) => {
  res.json({ success: true, data: sapiPatchService.getStatus() });
});

// GET /users/:id — Granular CRM entity structurally mapped including order histories seamlessly
router.get('/users/:id', async (req, res, next) => {
  try {
    const profile = await dashboardService.getUserProfile(req.params.id);
    if (!profile) {
      res.status(404).json({ success: false, message: 'Counterparty physically untraceable' });
      return;
    }
    sendSuccess(res, profile);
  } catch (err) { next(err); }
});

// POST /orders/:orderId/sync-chat — Undocumented SAPI Chat extractor mapped natively into metadata
router.post('/orders/:orderId/sync-chat', async (req, res, next) => {
  try {
    const syncStatus = await dashboardService.syncOrderChat(req.params.orderId);
    sendSuccess(res, syncStatus);
  } catch (err) { next(err); }
});

export { router as dashboardRouter };

// ── Daily P&L chart data (public, consumed by frontend Overview) ────────────
import { getPnlTimeSeries } from "../services/pnl-snapshot.service.js";

router.get("/pnl-daily", async (req, res, next) => {
  try {
    const currency = ((req.query.currency as string) || "EUR").toUpperCase();
    const days = parseInt((req.query.days as string) || "180", 10);
    const snapshots = await getPnlTimeSeries(currency, days, req.query.accountId as string);
    
    // Map to chart-friendly format
    const chartData = snapshots.map((s: any) => ({
      date: new Date(s.date).toISOString().split("T")[0],
      pnl: Number(s.realizedPnl),
      buyVolume: Number(s.buyVolume),
      sellVolume: Number(s.sellVolume),
      spread: Number(s.spreadPct),
      buyCount: s.buyCount,
      sellCount: s.sellCount,
    }));
    
    res.json({ success: true, data: chartData });
  } catch (err) { next(err); }
});
