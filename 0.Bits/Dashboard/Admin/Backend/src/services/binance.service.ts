import ccxt from 'ccxt';
import { config } from '../config/index.js';
import { logger } from '../lib/logger.js';

import * as crypto from 'crypto';
import fs from 'fs';

export class BinanceService {
  private client: any;
  private enabled: boolean = false;

  constructor() {
    if (config.BINANCE_API_KEY && config.BINANCE_API_SECRET) {
      this.client = new ccxt.binance({
        apiKey: config.BINANCE_API_KEY,
        secret: config.BINANCE_API_SECRET,
        enableRateLimit: true,
      });
      this.enabled = true;
    } else {
      logger.warn('[BinanceService] BINANCE_API_KEY is missing. CCXT Integration is Disabled.');
      // Stub it for typescript to compile, but flag to false
      this.client = new ccxt.binance();
    }
  }

  /**
   * Undocumented Binance SAPI endpoint to explicitly extract True Legal Identity
   */
  async fetchTrueLegalName(orderNumber: string): Promise<{ buyerName?: string, sellerName?: string, createTime?: number } | null> {
    if (!this.enabled) return null;
    
    try {
      let buyerName, sellerName, createTime;

      if (config.BINANCE_API_PRIVATE_KEY_PATH) {
        // Authenticate with RSA if configured
        const privateKey = fs.readFileSync(config.BINANCE_API_PRIVATE_KEY_PATH, 'utf8');
        const timestamp = Date.now();
        const payload = \`adOrderNo=\${orderNumber}&timestamp=\${timestamp}\`;
        
        const signer = crypto.createSign('RSA-SHA256');
        signer.update(payload);
        signer.end();
        const signature = encodeURIComponent(signer.sign(privateKey, 'base64'));
        
        const finalBody = \`\${payload}&signature=\${signature}\`;
        
        const rawRes = await fetch(\`https://api.binance.com/sapi/v1/c2c/orderMatch/getUserOrderDetail\`, {
            method: 'POST',
            headers: {
              'X-MBX-APIKEY': config.BINANCE_API_KEY!,
              'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: finalBody
        });
        
        const json = await rawRes.json();
        
        if (json && json.data) {
          buyerName = json.data.buyerName;
          sellerName = json.data.sellerName;
          createTime = json.data.createTime;
        }
      } else {
         // Fallback to standard CCXT implicit integration (Throws -1000 without RSA Whitelist)
         const json = await this.client.request('c2c/orderMatch/getUserOrderDetail', 'sapi', 'POST', {
            adOrderNo: orderNumber
         });
         if (json && json.data) {
             buyerName = json.data.buyerName;
             sellerName = json.data.sellerName;
             createTime = json.data.createTime;
         }
      }
      
      if (buyerName || sellerName || createTime) {
        return {
          buyerName: buyerName || undefined,
          sellerName: sellerName || undefined,
          createTime: createTime || undefined
        };
      }
      return null;
    } catch(err) {
      logger.error(`[BinanceService] fetchTrueLegalName error for ${orderNumber}:`, err);
      return null;
    }
  }

  /**
   * Fetches real Funding wallet balances from Binance
   */
  async fetchFundingBalances() {
    if (!this.enabled) return [];
    
    try {
      // The funding wallet mapping in CCXT
      const response = await this.client.sapiPostAssetGetFundingAsset();
      
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
  async fetchP2PVolume() {
    if (!this.enabled) return [];

    try {
      // Direct raw API hit to c2c endpoint via CCXT implicit API
      // ccxt parses implicit APIs dynamically
      const response = await this.client.sapiGetC2cOrderMatchListUserOrderHistory();
      
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
  async fetchChatMessages(orderId: string): Promise<any[]> {
    try {
      // Removed the strict CCXT .has[] check because CCXT lacks explicit definitions for the V7.4 SAPI chat pagination array.
      // We natively execute the raw request against Binance's Gateway bypassing the implicit wrapper.
      const payload = await this.client.request('c2c/chat/retrieveChatMessagesWithPagination', 'sapi', 'GET', { 
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
