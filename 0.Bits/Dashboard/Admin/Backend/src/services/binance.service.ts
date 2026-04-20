import ccxt from 'ccxt';
import { config } from '../config/index.js';
import { logger } from '../lib/logger.js';

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
   * Fetches real Funding wallet balances from Binance
   */
  async fetchFundingBalances() {
    if (!this.enabled) return [];
    
    try {
      // The funding wallet mapping in CCXT
      const response = await this.client.sapiGetFundingAsset();
      
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
        transaction_date: new Date(order.createTime).toISOString(),
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
}

export const binanceService = new BinanceService();
