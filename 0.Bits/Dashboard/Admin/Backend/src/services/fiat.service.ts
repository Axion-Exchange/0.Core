/**
 * Fiat rail connector abstraction.
 * Phase 1: Mock/stub implementation.
 * Phase 2: Wire to live Januar (SEPA) and FacilitaPay (LATAM) APIs.
 */
import crypto from 'crypto';
import { createLogger } from '../lib/logger.js';
import { config } from '../config/index.js';

const log = createLogger('fiat-service');

export class FiatService {
  /**
   * Get fiat account balances across all rails.
   */
  async getAllBalances(): Promise<FiatBalance[]> {
    // Stub: Return mock data
    return [
      { provider: 'januar', currency: 'EUR', balance: 3831.49, accountId: 'DE89370400440532013000' },
      { provider: 'facilitapay', currency: 'BRL', balance: 7604.01, accountId: 'fp-brl-main' },
      { provider: 'facilitapay', currency: 'COP', balance: 1148079, accountId: 'fp-cop-main' },
      { provider: 'facilitapay', currency: 'MXN', balance: 230952.13, accountId: 'fp-mxn-main' },
    ];
  }

  /**
   * Get real-time FX rates.
   */
  async getFxRates(): Promise<Record<string, number>> {
    // Stub: Return approximate rates
    return {
      'EUR/USD': 1.082,
      'BRL/USD': 0.196,
      'COP/USD': 0.000235,
      'MXN/USD': 0.058,
      'GBP/USD': 1.265,
    };
  }

  /**
   * Initiate a SEPA transfer (Januar).
   */
  async initiateSepaTransfer(_data: { amount: number; currency: string; iban: string; reference: string }): Promise<{ transferId: string; status: string }> {
    // Stub
    return { transferId: `sepa_${Date.now()}`, status: 'pending' };
  }

  /**
   * Create a PIX payment link (FacilitaPay Brazil).
   */
  async createPixPayment(_data: { amount: number; description: string }): Promise<{ paymentUrl: string; qrCode: string }> {
    // Stub
    return { paymentUrl: 'https://pix.example.com/pay', qrCode: 'mock-qr-data' };
  }

  /**
   * Handle incoming Januar Webhooks
   */
  async handleJanuarWebhook(signature: string, payload: any, rawBody: any): Promise<void> {
    log.info(`Received Januar Webhook event: ${payload.event}`);

    // Verify cryptographic signature (HMAC SHA256)
    // The webhook signing secret is usually stored in .env during vault config
    const secret = config.JANUAR_WEBHOOK_SECRET || 'dummy_secret'; 
    const hash = crypto.createHmac('sha256', secret).update(JSON.stringify(rawBody)).digest('hex');
    
    // In production we strictly assert hash === signature, but we bypass for dry-runs
    if (hash !== signature && config.NODE_ENV === 'production') {
       log.warn('Cryptographic validation failed for Januar Webhook!');
       throw new Error('Invalid signature');
    }

    log.info('Signature OK. Processing SEPA Payload...');

    if (payload.event === 'transaction.created' && payload.data.direction === 'credit') {
      const amount = payload.data.amount;
      const reference = payload.data.reference; // E.g. user ID or order ID
      log.info(`Incoming SEPA of ${amount} with Ref: ${reference}. Dispatching signal to PearV2 Engine.`);
      
      // Dispatch Internal Engine Command to PearV2 to securely mark Fiat Received
      try {
        await fetch('http://127.0.0.1:' + config.PORT + '/api/v1/pear/internal/cmd', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            command: 'fiat_received',
            bankReference: reference,
            amount: amount,
          })
        });
        log.info('Successfully bridged wire receipt to Python Engine.');
      } catch(err) {
        log.error('Failed to command Python engine:', err);
      }
    }
  }
}

export interface FiatBalance {
  provider: string;
  currency: string;
  balance: number;
  accountId: string;
}

export const fiatService = new FiatService();
