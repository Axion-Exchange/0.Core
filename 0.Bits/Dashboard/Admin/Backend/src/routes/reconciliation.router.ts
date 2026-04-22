import { Router } from 'express';
import { ReconciliationController } from '../controllers/reconciliation.controller.js';
import { identityResolverService } from '../services/identity-resolver.service.js';
import { diditKycMatcher } from '../services/didit-kyc-matcher.service.js';
import multer from 'multer';
import os from 'os';

// Use OS temp dir safely
const upload = multer({ dest: os.tmpdir() });

const router = Router();

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

// Trigger Didit KYC ↔ P2P identity name matching
router.post('/match-kyc', async (_req, res) => {
  try {
    const result = await diditKycMatcher.runFullMatch();
    res.json({ success: true, ...result });
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

export const reconciliationRouter = router;
