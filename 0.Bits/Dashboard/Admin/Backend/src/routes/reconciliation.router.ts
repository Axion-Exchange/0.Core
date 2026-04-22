import { Router } from 'express';
import { ReconciliationController } from '../controllers/reconciliation.controller.js';
import { identityResolverService } from '../services/identity-resolver.service.js';
import { kycOrchestrator } from '../services/kyc-orchestrator.service.js';
import multer from 'multer';
import os from 'os';

// Use OS temp dir safely
const upload = multer({ dest: os.tmpdir() });

const router = Router();

// ── P2P Reconciliation ────────────────────────────────────────────────────────

// Endpoint for reconciling P2P orders from Binance CSV
router.post('/csv', upload.single('csvFile'), ReconciliationController.uploadCSV);

// Trigger full identity resolution (resolves ALL real names from Binance API)
router.post('/resolve-identities', async (_req, res) => {
  const started = await identityResolverService.triggerFullResolution();
  if (started) {
    res.json({ success: true, message: 'Identity resolution started. Check /status for progress.' });
  } else {
    res.json({ success: false, message: 'Identity resolution is already running.' });
  }
});

// Check identity resolution progress
router.get('/resolve-identities/status', async (_req, res) => {
  res.json(identityResolverService.getStatus());
});

// ── KYC Provider Registry ─────────────────────────────────────────────────────

// List all registered KYC providers
router.get('/kyc/providers', async (_req, res) => {
  try {
    const providers = await kycOrchestrator.listProviders();
    res.json({ success: true, providers });
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// Register a new KYC provider/app
router.post('/kyc/providers', async (req, res) => {
  try {
    const { name, provider, appId, apiKey, baseUrl } = req.body;
    if (!name || !provider || !appId || !apiKey) {
      res.status(400).json({ success: false, error: 'name, provider, appId, apiKey are required' });
      return;
    }
    const result = await kycOrchestrator.addProvider({ name, provider, appId, apiKey, baseUrl });
    res.json({ success: true, provider: { id: result.id, name: result.name, provider: result.provider } });
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// ── KYC Orchestration ─────────────────────────────────────────────────────────

// Run full pipeline: sync all providers → match sessions → update users
router.post('/kyc/sync', async (_req, res) => {
  try {
    const result = await kycOrchestrator.runFullPipeline();
    res.json({ success: true, ...result });
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// List all KYC sessions across all providers
router.get('/kyc/sessions', async (req, res) => {
  try {
    const status = req.query.status as string | undefined;
    const matched = req.query.matched === 'true' ? true : req.query.matched === 'false' ? false : undefined;
    const sessions = await kycOrchestrator.listSessions({ status, matched });
    res.json({ success: true, count: sessions.length, sessions });
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// Get unified KYC status for a specific user
router.get('/kyc/users/:userId/status', async (req, res) => {
  try {
    const result = await kycOrchestrator.getUnifiedStatus(req.params.userId);
    res.json({ success: true, ...result });
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

export const reconciliationRouter = router;
