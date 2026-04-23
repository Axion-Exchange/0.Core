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

  /**
   * VIP Merchant: Get Advertisement Details
   * SAPI: GET /sapi/v1/c2c/ads/getDetailByNo
   */
  async getMerchantAdDetail(adsNo: string) {
    log.info(`Executing VIP SAPI: c2c/ads/getDetailByNo for [${adsNo}]`);
    try {
      const response = await this.client.request('c2c/ads/getDetailByNo', 'sapi', 'GET', { adsNo });
      return response;
    } catch (error) {
      log.error(`Failed to fetch VIP Ad Details for [${adsNo}]`, { error });
      throw error;
    }
  }

  /**
   * VIP Merchant: Create Advertisement
   * SAPI: POST /sapi/v1/c2c/ads/post
   * Requires strict 'classify' and 'onlineNow' to bypass 'illegal parameter' rejection.
   */
  async createMerchantAd(params: Record<string, any>) {
    log.info('Executing VIP SAPI: c2c/ads/post');
    try {
      // Ensure specific VIP parameters are set if not provided.
      const payload = {
        classify: 'mass', // default merchant requirement
        onlineNow: true, 
        ...params
      };
      const response = await this.client.request('c2c/ads/post', 'sapi', 'POST', payload);
      return response;
    } catch (error) {
      log.error('Failed to POST new VIP Ad', { error });
      throw error;
    }
  }

  /**
   * VIP Merchant: Update Advertisement Surplus Amount
   * Uses precise algebraic mapping as calculated against Binance Support parameters.
   */
  async updateMerchantAdSurplus(adsNo: string, newSurplusAmount: number) {
    log.info(`Executing VIP Surplus Math for [${adsNo}] -> target: ${newSurplusAmount}`);
    
    try {
      // Step 1: Fetch current state via private Detail endpoint
      const detailRes = await this.getMerchantAdDetail(adsNo);
      
      // We assume detailRes strictly maps to binomial payload struct (e.g. { data: { initAmount:... } })
      // Some API structures return it flat. We will extract values dynamically.
      const data = detailRes.data || detailRes;
      const initAmountBefore = parseFloat(data.initAmount);
      const surplusAmountBefore = parseFloat(data.surplusAmount || data.dynamicMaxAmount || data.remainingAmount);

      if (isNaN(initAmountBefore) || isNaN(surplusAmountBefore)) {
         throw new Error(`Failed to parse init/surplus values for ad ${adsNo}`);
      }

      // Step 2: Accurate Algebraic Map (Correcting Support's typo)
      // Eq: init_after = init_before - surplus_before + surplus_after
      const initAmountAfter = initAmountBefore - surplusAmountBefore + newSurplusAmount;

      log.info(`Math executed: ${initAmountBefore} - ${surplusAmountBefore} + ${newSurplusAmount} = ${initAmountAfter}`);

      // Step 3: Dispatch Update to SAPI
      const updateRes = await this.client.request('c2c/ads/update', 'sapi', 'POST', {
        adsNo: adsNo,
        initAmount: initAmountAfter.toString()
      });

      return updateRes;
    } catch (error) {
       log.error(`Failed to update surplus for [${adsNo}]`, { error });
       throw error;
    }
  }

  /**
   * Send Chat Message to P2P Order
   * Connects to undocumented SAPI chat endpoint to automate KYC requests
   */
  async sendChatMessage(orderNo: string, content: string) {
    log.info(`Sending chat message for order [${orderNo}]`);
    try {
      // Trying standard SAPI endpoint mapping
      const response = await this.client.request('c2c/chat/sendMsg', 'sapi', 'POST', {
        orderNo,
        content
      });
      return response;
    } catch (error) {
      log.error(`Failed to send chat message for order [${orderNo}]`, { error });
      throw error;
    }
  }
}
