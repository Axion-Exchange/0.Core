import { Router } from 'express';
import crypto from 'crypto';
import { prisma } from '../lib/db.js';
import { createLogger } from '../lib/logger.js';
import { kycOrchestrator } from '../services/kyc-orchestrator.service.js';

const log = createLogger('kyc-webhook');
const router = Router();

// ── Didit Webhook Signature Verification ─────────────────────────────────────

/**
 * Process floats to match Didit's server-side behavior.
 * Converts float values that are whole numbers to integers.
 */
function shortenFloats(data: any): any {
  if (Array.isArray(data)) {
    return data.map(shortenFloats);
  } else if (data !== null && typeof data === 'object') {
    return Object.fromEntries(
      Object.entries(data).map(([key, value]) => [key, shortenFloats(value)])
    );
  } else if (typeof data === 'number' && !Number.isInteger(data) && data % 1 === 0) {
    return Math.trunc(data);
  }
  return data;
}

/**
 * Sort object keys recursively for canonical JSON.
 */
function sortKeys(obj: any): any {
  if (Array.isArray(obj)) {
    return obj.map(sortKeys);
  } else if (obj !== null && typeof obj === 'object') {
    return Object.keys(obj).sort().reduce((result: any, key: string) => {
      result[key] = sortKeys(obj[key]);
      return result;
    }, {});
  }
  return obj;
}

/**
 * Verify X-Signature-V2 (Recommended by Didit).
 * Works even if middleware re-encodes special characters.
 */
function verifySignatureV2(jsonBody: any, signatureHeader: string, timestampHeader: string, secretKey: string): boolean {
  // Check timestamp freshness (within 5 minutes)
  const currentTime = Math.floor(Date.now() / 1000);
  const incomingTime = parseInt(timestampHeader, 10);
  if (Math.abs(currentTime - incomingTime) > 300) return false;

  const processedData = shortenFloats(jsonBody);
  const canonicalJson = JSON.stringify(sortKeys(processedData));
  const hmac = crypto.createHmac('sha256', secretKey);
  const expectedSignature = hmac.update(canonicalJson, 'utf8').digest('hex');

  try {
    return crypto.timingSafeEqual(
      Buffer.from(expectedSignature, 'utf8'),
      Buffer.from(signatureHeader, 'utf8')
    );
  } catch {
    return false;
  }
}

/**
 * Verify X-Signature-Simple (Fallback).
 * Independent of JSON encoding — verifies core fields only.
 */
function verifySignatureSimple(jsonBody: any, signatureHeader: string, timestampHeader: string, secretKey: string): boolean {
  const currentTime = Math.floor(Date.now() / 1000);
  const incomingTime = parseInt(timestampHeader, 10);
  if (Math.abs(currentTime - incomingTime) > 300) return false;

  const canonicalString = [
    jsonBody.timestamp || '',
    jsonBody.session_id || '',
    jsonBody.status || '',
    jsonBody.webhook_type || '',
  ].join(':');

  const hmac = crypto.createHmac('sha256', secretKey);
  const expectedSignature = hmac.update(canonicalString).digest('hex');

  try {
    return crypto.timingSafeEqual(
      Buffer.from(expectedSignature, 'utf8'),
      Buffer.from(signatureHeader, 'utf8')
    );
  } catch {
    return false;
  }
}

// ── Webhook Endpoint ─────────────────────────────────────────────────────────

/**
 * POST /api/v1/kyc/webhook
 * 
 * Receives real-time status updates from Didit.
 * Signature verification uses the provider's webhookSecret.
 * Falls through multiple verification methods for resilience.
 */
router.post('/webhook', async (req, res) => {
  try {
    const signatureV2 = req.get('X-Signature-V2') || '';
    const signatureSimple = req.get('X-Signature-Simple') || '';
    const timestamp = req.get('X-Timestamp') || '';
    const jsonBody = req.body;

    if (!timestamp) {
      log.warn('[Webhook] Missing X-Timestamp header');
      return res.status(401).json({ message: 'Missing required headers' });
    }

    const { session_id, status, vendor_data, webhook_type } = jsonBody;

    log.info(`[Webhook] Received: type=${webhook_type}, session=${session_id}, status=${status}`);

    // Find the provider by matching the session
    const existingSession = await prisma.kycSession.findFirst({
      where: { externalId: session_id },
      include: { provider: true },
    });

    let verified = false;

    if (existingSession?.provider.webhookSecret) {
      const secret = existingSession.provider.webhookSecret;

      // Try V2 first (recommended)
      if (signatureV2 && verifySignatureV2(jsonBody, signatureV2, timestamp, secret)) {
        verified = true;
        log.info('[Webhook] Verified via X-Signature-V2');
      }
      // Fallback to Simple
      else if (signatureSimple && verifySignatureSimple(jsonBody, signatureSimple, timestamp, secret)) {
        verified = true;
        log.info('[Webhook] Verified via X-Signature-Simple');
      }
    }

    if (!verified) {
      // Try all providers' secrets (session might be new)
      const providers = await prisma.kycProvider.findMany({
        where: { isActive: true, webhookSecret: { not: null } },
      });

      for (const prov of providers) {
        if (!prov.webhookSecret) continue;
        if (signatureV2 && verifySignatureV2(jsonBody, signatureV2, timestamp, prov.webhookSecret)) {
          verified = true;
          log.info(`[Webhook] Verified via ${prov.name} secret`);
          break;
        }
        if (signatureSimple && verifySignatureSimple(jsonBody, signatureSimple, timestamp, prov.webhookSecret)) {
          verified = true;
          log.info(`[Webhook] Verified via ${prov.name} secret (simple)`);
          break;
        }
      }
    }

    if (!verified) {
      // Accept without verification if no secrets configured (graceful degradation)
      const hasAnySecret = await prisma.kycProvider.count({
        where: { webhookSecret: { not: null } },
      });
      if (hasAnySecret > 0) {
        log.warn('[Webhook] Signature verification failed — rejecting');
        return res.status(401).json({ message: 'Invalid signature' });
      }
      log.warn('[Webhook] No webhook secrets configured — accepting without verification');
    }

    // ── Process the webhook ──────────────────────────────────────────────────

    if (webhook_type === 'status.updated' && session_id && status) {
      // Upsert session in our DB
      if (existingSession) {
        const normalizedStatus = status.toUpperCase();
        const previousStatus = existingSession.status;

        await prisma.kycSession.update({
          where: { id: existingSession.id },
          data: {
            status: normalizedStatus,
            rawPayload: { ...existingSession.rawPayload as any, ...jsonBody },
          },
        });

        log.info(`[Webhook] Session ${session_id}: ${previousStatus} → ${normalizedStatus}`);

        // Propagate to matched user immediately
        if (existingSession.matchedUserId && normalizedStatus !== previousStatus) {
          const newKycStatus = kycOrchestrator.mapStatus(normalizedStatus);
          await prisma.user.update({
            where: { id: existingSession.matchedUserId },
            data: { kycStatus: newKycStatus },
          });
          log.info(`[Webhook] User ${existingSession.matchedUserId} kycStatus → ${newKycStatus} (instant)`);
        }
      } else {
        log.info(`[Webhook] Session ${session_id} not in DB yet — will be picked up by poller`);
      }

      // If vendor_data contains our internal user/order ID, log it
      if (vendor_data) {
        log.info(`[Webhook] vendor_data: ${vendor_data}`);
      }
    }

    return res.json({ message: 'Webhook event dispatched' });

  } catch (error: any) {
    log.error(`[Webhook] Error: ${error.message}`);
    return res.status(500).json({ message: 'Internal error' });
  }
});

export const kycWebhookRouter = router;
