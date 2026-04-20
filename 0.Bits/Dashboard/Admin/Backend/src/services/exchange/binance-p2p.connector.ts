import * as ccxt from 'ccxt';
import { createLogger } from '../../lib/logger.js';

const log = createLogger('binance-p2p-connector');

/**
 * Dedicated Binance adapter specifically for mapping
 * undocumented or strictly SAPI-based C2C endpoints.
 */
export class BinanceP2PConnector {
  private client: ccxt.Exchange;

  constructor(client: ccxt.Exchange) {
    this.client = client;
  }

  /**
   * Get C2C Trade History (User Data) 
   * Official SAPI: GET /sapi/v1/c2c/orderMatch/listUserOrderHistory
   * Weight: 1
   */
  async getTradeHistory(params: {
    tradeType?: 'BUY' | 'SELL';
    startTimestamp?: number;
    endTimestamp?: number;
    page?: number;
    rows?: number;
  } = {}) {
    log.info('Executing explicit Binance SAPI: c2c/orderMatch/listUserOrderHistory');
    try {
      // ccxt implicit methods resolve 'sapiGetC2cOrderMatchListUserOrderHistory' automatically.
      // But for total type safety and strict execution logic, we use client.request().
      const response = await this.client.request('c2c/orderMatch/listUserOrderHistory', 'sapi', 'GET', params);
      return response;
    } catch (error) {
      log.error('Failed to fetch Binance P2P history', { error });
      throw error;
    }
  }

  /**
   * Internal BAPI mapping for scanning the P2P marketplace (Public).
   * Note: This hits the unofficial web API endpoints to locate active advertisement liquidity.
   * No API key required for public BAPI reading, but CCXT fetch bridges the IP/proxy mechanics.
   */
  async getPublicAds(params: {
    asset: string;       // USDT, BTC
    fiat: string;        // EUR, GBP
    tradeType: 'BUY' | 'SELL';
    page?: number;
    rows?: number;
    payTypes?: string[];
  }) {
    log.info('Scraping internal Binance BAPI: c2c/adv/search');
    try {
      // We leverage CCXT's base fetch implementation to execute arbitrary public queries.
      const payload = {
        page: params.page || 1,
        rows: params.rows || 10,
        asset: params.asset,
        tradeType: params.tradeType,
        fiat: params.fiat,
        payTypes: params.payTypes || [],
      };

      const url = 'https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search';
      const response = await this.client.fetch(url, 'POST', {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
      }, JSON.stringify(payload));
      
      return response;
    } catch (error) {
      log.error('Failed to scrape Binance P2P BAPI market', { error });
      throw error;
    }
  }
}
