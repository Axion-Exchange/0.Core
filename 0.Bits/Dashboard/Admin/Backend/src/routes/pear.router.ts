import { Router } from 'express';
import { pearManagerService } from '../services/pear-manager.service.js';

export const pearRouter = Router();

// 1. GET Status
pearRouter.get('/status', (req, res) => {
  try {
    const status = pearManagerService.getStatus();
    res.status(200).json(status);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// 2. POST Lifecycle (Action: 'start' | 'stop')
pearRouter.post('/lifecycle', async (req, res) => {
  const { action } = req.body;

  try {
    if (action === 'start') {
      await pearManagerService.start();
      res.status(200).json({ message: 'PearV2 Daemon boot sequence initiated.' });
    } else if (action === 'stop') {
      pearManagerService.stop();
      res.status(200).json({ message: 'PearV2 Daemon was stopped.' });
    } else {
      res.status(400).json({ error: 'Invalid action. Must be "start" or "stop".' });
    }
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// 3. POST Config (Updates Python .env)
pearRouter.post('/config', async (req, res) => {
  const { config } = req.body; // config should be a Record<string, string>

  if (!config || typeof config !== 'object') {
    res.status(400).json({ error: 'Config payload must be a key-value object.' });
    return;
  }

  try {
    await pearManagerService.updateConfig(config);
    res.status(200).json({ message: 'PearV2 .env safely overwritten.' });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});
