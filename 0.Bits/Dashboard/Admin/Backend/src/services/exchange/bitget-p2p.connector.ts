import * as ccxt from 'ccxt';
import { createLogger } from '../../lib/logger.js';

const log = createLogger('bitget-p2p-connector');

/**
 * Dedicated Bitget adapter specifically mapped to explicitly
 * handle P2P commands natively in V2 without ccxt overriding issues.
 */
export class BitgetP2PConnector {
  private client: ccxt.Exchange;

  constructor(client: ccxt.Exchange) {
    this.client = client;
  }

  /**
   * VIP Merchant: Get Trade History
   * Equivalent to /api/v2/p2p/orderList
   */
  async getTradeHistory(params: {
    startTime?: string;
    endTime?: string;
    coin?: string;
  } = {}) {
    log.info('Executing explicit Bitget V2 SAPI: p2p/orderList');
    try {
      const response = await (this.client as any).privateGetApiV2P2pOrderlist(params);
      return response;
    } catch (error) {
      log.error('Failed to fetch Bitget P2P history', { error });
      throw error;
    }
  }

  /**
   * VIP Merchant: Get Advertisements
   * Equivalent to /api/v2/p2p/advList
   */
  async getMerchantAds(params: {
    advNo?: string;
    coin?: string;
  } = {}) {
    log.info('Executing Bitget V2 SAPI: p2p/advList');
    try {
      const response = await (this.client as any).privateGetApiV2P2pAdvlist(params);
      return response;
    } catch (error) {
       log.error('Failed to fetch Bitget P2P Merchant Ads', { error });
       throw error;
    }
  }

  /**
   * Retrieves merchant specific identity stats.
   */
  async getMerchantInfo() {
    log.info('Executing Bitget V2 SAPI: p2p/merchantInfo');
    try {
      return await (this.client as any).privateGetApiV2P2pMerchantinfo();
    } catch (error) {
      log.error('Failed to fetch Bitget P2P Merchant Info', { error });
      throw error;
    }
  }
}
