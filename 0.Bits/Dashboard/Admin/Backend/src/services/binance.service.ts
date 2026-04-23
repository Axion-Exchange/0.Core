import ccxt from 'ccxt';
import { config } from '../config/index.js';
import { logger } from '../lib/logger.js';
import { decrypt } from '../lib/crypto.js';
import { P2PAccount } from '@prisma/client';
import * as crypto from 'crypto';
import fs from 'fs';

export class BinanceService {
  private defaultClient: any;
  private defaultEnabled: boolean = false;

  constructor() {
    const hasRsaKey = config.BINANCE_API_KEY && config.BINANCE_API_PRIVATE_KEY_PATH;
    const hasHmacKey = config.BINANCE_API_KEY && config.BINANCE_API_SECRET;

    if (hasRsaKey) {
      const privateKeyPem = fs.readFileSync(config.BINANCE_API_PRIVATE_KEY_PATH!, 'utf8');
      this.defaultClient = new ccxt.binance({
        apiKey: config.BINANCE_API_KEY,
        secret: privateKeyPem,
        enableRateLimit: true,
      });
      this.defaultEnabled = true;
      logger.info('[BinanceService] Initialized with RSA key authentication.');
    } else if (hasHmacKey) {
      this.defaultClient = new ccxt.binance({
        apiKey: config.BINANCE_API_KEY,
        secret: config.BINANCE_API_SECRET,
        enableRateLimit: true,
      });
      this.defaultEnabled = true;
    } else {
      logger.warn('[BinanceService] BINANCE_API_KEY is missing. CCXT Integration is Disabled.');
      this.defaultClient = new ccxt.binance();
    }
  }

  public getClient(account?: P2PAccount): { client: any, enabled: boolean, rsaPem?: string } {
    if (!account) return { client: this.defaultClient, enabled: this.defaultEnabled, rsaPem: config.BINANCE_API_PRIVATE_KEY_PATH ? fs.readFileSync(config.BINANCE_API_PRIVATE_KEY_PATH, 'utf8') : undefined };
    
    try {
      const apiKey = decrypt(account.apiKeyEnc);
      const apiSecret = decrypt(account.apiSecretEnc);
      
      const isRsa = apiSecret.includes("-----BEGIN PRIVATE KEY-----") || apiSecret.includes("-----BEGIN RSA PRIVATE KEY-----");
      
      const client = new ccxt.binance({
        apiKey,
        secret: apiSecret,
        enableRateLimit: true,
      });
      return { client, enabled: true, rsaPem: isRsa ? apiSecret : undefined };
    } catch(err) {
      logger.error(`[BinanceService] Failed to initialize client for account ${account.id}`, err);
      return { client: this.defaultClient, enabled: false };
    }
  }

  /**
   * Binance SAPI endpoint to extract True Legal Identity from order details.
   */
  async fetchTrueLegalName(orderNumber: string, account?: P2PAccount): Promise<{ buyerName?: string, sellerName?: string, createTime?: number } | null> {
    const { enabled, rsaPem, client } = this.getClient(account);
    if (!enabled) return null;
    
    try {
      if (!rsaPem) {
        logger.warn('[BinanceService] RSA key not configured for account, cannot fetch real names');
        return null;
      }

      const timestamp = Date.now();
      const queryPayload = `timestamp=${timestamp}`;
      
      // RSA-SHA256 sign the query string only
      const signer = crypto.createSign('RSA-SHA256');
      signer.update(queryPayload);
      signer.end();
      const signature = encodeURIComponent(signer.sign(rsaPem, 'base64'));
      
      // adOrderNo goes in JSON body, timestamp+signature in query string
      const rawRes = await fetch(`https://api.binance.com/sapi/v1/c2c/orderMatch/getUserOrderDetail?${queryPayload}&signature=${signature}`, {
          method: 'POST',
          headers: {
            'X-MBX-APIKEY': client.apiKey,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ adOrderNo: orderNumber })
      });
      
      const json: any = await rawRes.json();
      
      if (json && json.code === '000000' && json.data) {
        return {
          buyerName: json.data.buyerName || undefined,
          sellerName: json.data.sellerName || undefined,
          createTime: json.data.createTime || undefined
        };
      }
      
      logger.warn(`[BinanceService] getUserOrderDetail returned: ${json?.code} ${json?.msg || json?.message}`);
      return null;
    } catch(err) {
      logger.error(`[BinanceService] fetchTrueLegalName error for ${orderNumber}:`, err);
      return null;
    }
  }

  /**
   * Fetches real Funding wallet balances from Binance
   */
  async fetchFundingBalances(account?: P2PAccount) {
    const { enabled, client } = this.getClient(account);
    if (!enabled) return [];
    
    try {
      // The funding wallet mapping in CCXT
      const response = await client.sapiPostAssetGetFundingAsset();
      
      return response.map((asset: any) => ({
        id: asset.asset,
        currency: asset.asset,
        type: 'FIAT', // Standardize loosely based on asset type if needed
        balance: parseFloat(asset.free) + parseFloat(asset.freeze) + parseFloat(asset.locked),
        available: parseFloat(asset.free),
        locked: parseFloat(asset.locked) + parseFloat(asset.freeze),
        exchange: 'Binance (Funding)',
        status: 'ACTIVE',
        updatedAt: new Date(),
      })).filter((asset: any) => asset.balance > 0);
    } catch (err) {
      logger.error('[BinanceService] fetchFundingBalances error:', err);
      return [];
    }
  }

  /**
   * Directly fetches authenticated user order history for P2P off Binance servers
   */
  async fetchP2PVolume(account?: P2PAccount) {
    const { enabled, client } = this.getClient(account);
    if (!enabled) return [];

    try {
      // Direct raw API hit to c2c endpoint via CCXT implicit API
      // ccxt parses implicit APIs dynamically
      const response = await client.sapiGetC2cOrderMatchListUserOrderHistory();
      
      if (!response || !response.data) {
        return [];
      }

      // Format to dashboard expected schema
      return response.data.map((order: any) => ({
        id: order.orderNumber,
        transaction_date: new Date(Number(order.createTime)).toISOString(),
        amount: parseFloat(order.amount), // Fiat amount traded
        expense_status: order.orderStatus === 'COMPLETED' ? 'successful' : 'pending',
        category: order.tradeType === 'BUY' ? 'Arbitrage Buy' : 'Arbitrage Sell',
        merchant: order.counterPartNickName || 'Binance P2P User',
        country: 'Global',
      }));

    } catch(err) {
      logger.error('[BinanceService] fetchP2PVolume error:', err);
      return [];
    }
  }
  /**
   * Undocumented Binance SAPI extraction stub resolving the raw conversational payloads bound perfectly to exact Order IDs.
   * Note: This will naturally drop an exception alerting the service layer if the exact SAPI URL signature isn't mapped functionally natively!
   */
  async fetchChatMessages(orderId: string, account?: P2PAccount): Promise<any[]> {
    const { client } = this.getClient(account);
    try {
      // Removed the strict CCXT .has[] check because CCXT lacks explicit definitions for the V7.4 SAPI chat pagination array.
      // We natively execute the raw request against Binance's Gateway bypassing the implicit wrapper.
      const payload = await client.request('c2c/chat/retrieveChatMessagesWithPagination', 'sapi', 'GET', { 
         orderNo: orderId,
         page: 1,
         rows: 100
      });
      
      if (payload && payload.data && Array.isArray(payload.data)) {
        return payload.data;
      }
      return [];
    } catch (e: any) {
       console.warn(`CCXT SAPI Chat Explicit Sync Fault Mapping: ${e.message}`);
       throw e;
    }
  }
}

export const binanceService = new BinanceService();
