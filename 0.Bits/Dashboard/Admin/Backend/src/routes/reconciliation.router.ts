import { Router } from 'express';
import { ReconciliationController } from '../controllers/reconciliation.controller.js';
import { identityResolverService } from '../services/identity-resolver.service.js';
import multer from 'multer';
import os from 'os';

const upload = multer({ dest: os.tmpdir() });
const router = Router();

router.post('/csv', upload.single('csvFile'), ReconciliationController.uploadCSV);

router.post('/resolve-identities', async (_req, res) => {
  const started = await identityResolverService.triggerFullResolution();
  if (started) {
    res.json({ success: true, message: 'Identity resolution started.' });
  } else {
    res.json({ success: false, message: 'Already running.' });
  }
});

router.get('/resolve-identities/status', async (_req, res) => {
  res.json(identityResolverService.getStatus());
});

export const reconciliationRouter = router;
