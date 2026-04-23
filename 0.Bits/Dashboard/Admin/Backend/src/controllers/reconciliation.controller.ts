import { Request, Response } from 'express';
import { ReconciliationService } from '../services/reconciliation.service.js';
import fs from 'fs';
import path from 'path';

export class ReconciliationController {
  static async uploadCSV(req: Request, res: Response): Promise<void> {
    try {
      if (!req.file) {
        res.status(400).json({ error: 'No CSV file provided' });
        return;
      }

      const filePath = req.file.path;
      const accountId = req.body.accountId; // Ensure it's passed from frontend
      
      // Process the CSV using our robust service
      const stats = await ReconciliationService.processCSV(filePath, accountId);

      // Clean up the uploaded file
      fs.unlink(filePath, (err) => {
        if (err) console.error(`Error deleting temp file: ${filePath}`, err);
      });

      res.status(200).json({
        message: 'CSV Reconiliation Successful',
        stats
      });

    } catch (error) {
      console.error('[Reconciliation Controller] CSV Processing Error:', error);
      res.status(500).json({ error: 'Failed to process reconciliation CSV.' });
    }
  }
}
