import * as ccxt from 'ccxt';
import { createLogger } from '../../lib/logger.js';
import * as crypto from 'crypto';

const log = createLogger('binance-p2p-connector');

/**
 * Dedicated Binance adapter mapping SAPI C2C endpoints v7.4.
 * Integrates comprehensive merchant & user operations.
 */
export class BinanceP2PConnector {
  private client: ccxt.Exchange;

  constructor(client: ccxt.Exchange) {
    this.client = client;
  }

  // ============================================================================
  // ADS CONTROLLER
  // ============================================================================

  async getAvailableAdsCategory(params: Record<string, any> = {}) {
    return this.client.request('c2c/ads/getAvailableAdsCategory', 'sapi', 'GET', params);
  }

  async getAdDetailByNo(adsNo: string) {
    return this.client.request('c2c/ads/getDetailByNo', 'sapi', 'POST', { adsNo });
  }

  async getReferencePrice(params: Record<string, any>) {
    return this.client.request('c2c/ads/getReferencePrice', 'sapi', 'POST', params);
  }

  async listAdsWithPagination(params: Record<string, any> = {}) {
    const timestamp = Date.now();
    const queryPayload = `timestamp=${timestamp}`;
    let signature: string;
    
    // Binance requires SAPI listWithPagination to be a JSON body, but the signature must ONLY cover the query string.
    // CCXT natively tries to form-encode the body and sign it, which returns -1000. We bypass it here.
    if (this.client.secret && (this.client.secret.includes('BEGIN PRIVATE KEY') || this.client.secret.includes('BEGIN RSA PRIVATE KEY'))) {
      const signer = crypto.createSign('RSA-SHA256');
      signer.update(queryPayload);
      signer.end();
      signature = encodeURIComponent(signer.sign(this.client.secret, 'base64'));
    } else {
      signature = crypto.createHmac('sha256', this.client.secret).update(queryPayload).digest('hex');
    }

    const rawRes = await fetch(`https://api.binance.com/sapi/v1/c2c/ads/listWithPagination?${queryPayload}&signature=${signature}`, {
        method: 'POST',
        headers: {
          'X-MBX-APIKEY': this.client.apiKey,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(params)
    });
    
    return rawRes.json();
  }

  async postAd(params: Record<string, any>) {
    const payload = { classify: 'mass', onlineNow: true, ...params };
    return this.client.request('c2c/ads/post', 'sapi', 'POST', payload);
  }

  async searchAds(params: Record<string, any> = {}) {
    return this.client.request('c2c/ads/search', 'sapi', 'POST', params);
  }

  async updateAd(params: Record<string, any>) {
    return this.client.request('c2c/ads/update', 'sapi', 'POST', params);
  }

  async updateAdStatus(advNos: string[], advStatus: number) {
    return this.client.request('c2c/ads/updateStatus', 'sapi', 'POST', { advNos, advStatus });
  }

  /**
   * Internal BAPI mapping for scanning the P2P marketplace (Public).
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

  async updateMerchantAdSurplus(adsNo: string, newSurplusAmount: number) {
    log.info(`Executing VIP Surplus Math for [${adsNo}] -> target: ${newSurplusAmount}`);
    try {
      const detailRes = await this.getMerchantAdDetail(adsNo);
      const data = detailRes.data || detailRes;
      const initAmountBefore = parseFloat(data.initAmount);
      const surplusAmountBefore = parseFloat(data.surplusAmount || data.dynamicMaxAmount || data.remainingAmount);

      if (isNaN(initAmountBefore) || isNaN(surplusAmountBefore)) {
         throw new Error(`Failed to parse init/surplus values for ad ${adsNo}`);
      }

      const initAmountAfter = initAmountBefore - surplusAmountBefore + newSurplusAmount;
      log.info(`Math executed: ${initAmountBefore} - ${surplusAmountBefore} + ${newSurplusAmount} = ${initAmountAfter}`);

      const updateRes = await this.client.request('c2c/ads/update', 'sapi', 'POST', {
        adsNo: adsNo,
        initAmount: initAmountAfter.toString()
      });

      return updateRes;
    } catch (error) {
      log.error(`Failed to execute VIP Surplus Math on [${adsNo}]`, { error });
      throw error;
    }
  }

  // ============================================================================
  // MERCHANT CONTROLLER
  // ============================================================================

  async closeBusiness(params: Record<string, any> = {}) {
    return this.client.request('c2c/merchant/closeBusiness', 'sapi', 'POST', params);
  }

  async endRest(params: Record<string, any> = {}) {
    return this.client.request('c2c/merchant/endRest', 'sapi', 'POST', params);
  }

  async getMerchantAdDetail(merchantNo?: string) {
    // Retained signature compatibility; officially SAPI GET c2c/merchant/getAdDetails
    return this.client.request('c2c/merchant/getAdDetails', 'sapi', 'GET', merchantNo ? { merchantNo } : {});
  }

  async getOffline(params: Record<string, any> = {}) {
    return this.client.request('c2c/merchant/getOffline', 'sapi', 'POST', params);
  }

  async getOnline(params: Record<string, any> = {}) {
    return this.client.request('c2c/merchant/getOnline', 'sapi', 'POST', params);
  }

  async startBusiness(params: Record<string, any> = {}) {
    return this.client.request('c2c/merchant/startBusiness', 'sapi', 'POST', params);
  }

  async startRest(params: Record<string, any> = {}) {
    return this.client.request('c2c/merchant/startRest', 'sapi', 'POST', params);
  }

  // ============================================================================
  // ORDER MATCH CONTROLLER
  // ============================================================================

  async cancelOrder(params: { orderNumber: string; orderCancelReasonCode: number; orderCancelAdditionalInfo?: string }) {
    return this.client.request('c2c/orderMatch/cancelOrder', 'sapi', 'POST', params);
  }

  async checkIfAllowedCancelOrder(orderNumber: string) {
    return this.client.request('c2c/orderMatch/checkIfAllowedCancelOrder', 'sapi', 'POST', { orderNumber });
  }

  async checkIfCanPlaceOrder(adOrderNo: string) {
    return this.client.request('c2c/orderMatch/checkIfCanPlaceOrder', 'sapi', 'POST', { adOrderNo });
  }

  async checkIfCanReleaseCoin(params: Record<string, any>) {
    return this.client.request('c2c/orderMatch/checkIfCanReleaseCoin', 'sapi', 'POST', params);
  }

  async getUserOrderDetail(adOrderNo: string) {
    return this.client.request('c2c/orderMatch/getUserOrderDetail', 'sapi', 'POST', { adOrderNo });
  }

  async getUserOrderSummary(params: Record<string, any> = {}) {
    return this.client.request('c2c/orderMatch/getUserOrderSummary', 'sapi', 'GET', params);
  }

  async listOrders(params: Record<string, any> = {}) {
    return this.client.request('c2c/orderMatch/listOrders', 'sapi', 'POST', params);
  }

  async getTradeHistory(params: { tradeType?: 'BUY' | 'SELL'; startTimestamp?: number; endTimestamp?: number; page?: number; rows?: number; } = {}) {
    log.info('Executing explicit Binance SAPI: c2c/orderMatch/listUserOrderHistory');
    try {
      return await this.client.request('c2c/orderMatch/listUserOrderHistory', 'sapi', 'GET', params);
    } catch (error) {
      log.error('Failed to fetch Binance P2P history', { error });
      throw error;
    }
  }

  async markOrderAsPaid(params: Record<string, any>) {
    return this.client.request('c2c/orderMatch/markOrderAsPaid', 'sapi', 'POST', params);
  }

  async placeOrder(params: Record<string, any>) {
    return this.client.request('c2c/orderMatch/placeOrder', 'sapi', 'POST', params);
  }

  async queryCounterPartyOrderStatistic(params: Record<string, any>) {
    return this.client.request('c2c/orderMatch/queryCounterPartyOrderStatistic', 'sapi', 'POST', params);
  }

  async releaseDigitalAsset(params: Record<string, any>) {
    return this.client.request('c2c/orderMatch/releaseCoin', 'sapi', 'POST', params);
  }

  // ============================================================================
  // KYC, PAYMENT, AND DIGITAL/FIAT CURRENCY CONTROLLERS
  // ============================================================================

  async verifiedAdditionalKyc(params: Record<string, any> = {}) {
    return this.client.request('c2c/orderMatch/verifiedAdditionalKyc', 'sapi', 'POST', params);
  }

  async getPaymentMethodById(params: Record<string, any>) {
    return this.client.request('c2c/paymentMethod/getById', 'sapi', 'GET', params);
  }

  async getPaymentMethodByUserId(params: Record<string, any>) {
    return this.client.request('c2c/paymentMethod/getByUserId', 'sapi', 'GET', params);
  }

  async listAllOfValidPaymentMethods(params: Record<string, any> = {}) {
    return this.client.request('c2c/paymentMethod/list', 'sapi', 'GET', params);
  }

  async getUserDetail(params: Record<string, any> = {}) {
    return this.client.request('c2c/user/getUserDetail', 'sapi', 'GET', params);
  }

  async getRiskWarningTips(params: Record<string, any> = {}) {
    return this.client.request('c2c/user/getRiskWarningTips', 'sapi', 'GET', params);
  }

  async queryDigitalCurrencyList(params: Record<string, any> = {}) {
    return this.client.request('c2c/digitalCurrency/list', 'sapi', 'POST', params);
  }

  async queryFiatCurrencyList(params: Record<string, any> = {}) {
    return this.client.request('c2c/fiatCurrency/list', 'sapi', 'POST', params);
  }

  // ============================================================================
  // CHAT CONTROLLER
  // ============================================================================

  async getChatImagePresignedUrl(params: Record<string, any>) {
    return this.client.request('c2c/chat/getChatImagePresignedUrl', 'sapi', 'GET', params);
  }

  async markMessagesAsReadByUserAndOrder(params: Record<string, any>) {
    return this.client.request('c2c/chat/markMessagesAsReadByUserAndOrder', 'sapi', 'POST', params);
  }

  async markMessagesAsReadByUser(params: Record<string, any>) {
    return this.client.request('c2c/chat/markMessagesAsReadByUser', 'sapi', 'POST', params);
  }

  async retrieveChatWSS(params: Record<string, any> = {}) {
    return this.client.request('c2c/chat/retrieveChatWSS', 'sapi', 'GET', params);
  }

  async retrieveChatMessages(params: Record<string, any>) {
    return this.client.request('c2c/chat/retrieveChatMessagesWithPagination', 'sapi', 'GET', params);
  }

  async sendChatMessage(orderNo: string, content: string) {
    log.info(`Sending SAPI Chat message to [${orderNo}]`);
    return this.client.request('c2c/chat/sendMsg', 'sapi', 'POST', { orderNo, content });
  }

  // ============================================================================
  // COMMISSION CONTROLLER
  // ============================================================================

  async getCommissionOverview(params: Record<string, any> = {}) {
    return this.client.request('c2c/commission/overview', 'sapi', 'GET', params);
  }

  async getTakerCommissionRate(params: Record<string, any> = {}) {
    return this.client.request('c2c/commission/takerRate', 'sapi', 'GET', params);
  }

}
