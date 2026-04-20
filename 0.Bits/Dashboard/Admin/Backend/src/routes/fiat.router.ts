import { Router } from 'express';
import { z } from 'zod';
import { sendSuccess, sendError } from '../lib/response.js';
import { createLogger } from '../lib/logger.js';
import { fiatService } from '../services/fiat.service.js';

const router = Router();
const log = createLogger('fiat-router');

const WebhookSchema = z.object({
  id: z.string(),
  event: z.string(),
  data: z.any()
});

/**
 * @route POST /api/v1/fiat/januar/webhook
 * @desc Secure incoming webhook from Januar Banking API
 */
router.post('/januar/webhook', async (req, res) => {
  try {
    const signature = req.headers['x-januar-signature'];
    
    if (!signature) {
      log.warn('Incoming webhook missing signature');
      return sendError(res, 401, 'UNAUTHORIZED', 'Missing signature header');
    }

    const payload = WebhookSchema.parse(req.body);
    
    // Process the webhook in the service
    await fiatService.handleJanuarWebhook(signature as string, payload, req.body);

    // Always return 200 OK fast so Januar doesn't retry
    return sendSuccess(res, { status: 'acknowledged' });
  } catch (error) {
    log.error('Januar webhook parsing failed', { error });
    return sendError(res, 400, 'BAD_REQUEST', 'Invalid webhook payload');
  }
});

export { router as fiatRouter };
