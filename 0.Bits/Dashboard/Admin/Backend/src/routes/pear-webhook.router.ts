import { Router } from 'express';
import { createLogger } from '../lib/logger.js';

const log = createLogger('pear-webhook');
export const pearWebhookRouter = Router();

// Endpoint for PearV2 to push state updates
pearWebhookRouter.post('/', async (req, res) => {
  try {
    const { orderId, state, fiatAmount, cryptoAmount, currency, pnl } = req.body;
    
    // Quick validation
    if (!orderId || !state) {
      res.status(400).json({ error: 'Missing orderId or state in webhook payload' });
      return;
    }

    log.info(`Received PearV2 webhook for order ${orderId} -> ${state}`);

    // NOTE: Once Prisma schema is updated, we will write to the database here.
    // Example:
    // await prisma.pearV2Trade.upsert({
    //   where: { orderId },
    //   update: { state, updatedAt: new Date() },
    //   create: { orderId, state, fiatAmount, cryptoAmount, currency, pnl }
    // });

    // NOTE: Trigger WebSocket push to Dashboard here.

    res.status(200).json({ received: true });
  } catch (error: any) {
    log.error('Failed to process PearV2 webhook', { error: error.message });
    res.status(500).json({ error: 'Internal webhook processing error' });
  }
});
