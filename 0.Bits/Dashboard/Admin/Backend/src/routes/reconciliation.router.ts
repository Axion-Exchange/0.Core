import { Router } from 'express';
import { ReconciliationController } from '../controllers/reconciliation.controller.js';
import multer from 'multer';
import os from 'os';

// Use OS temp dir safely
const upload = multer({ dest: os.tmpdir() });

const router = Router();

// Endpoint for reconciling P2P orders from Binance CSV
router.post('/csv', upload.single('csvFile'), ReconciliationController.uploadCSV);

export const reconciliationRouter = router;
