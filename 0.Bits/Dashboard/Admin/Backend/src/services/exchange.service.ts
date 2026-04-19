/**
 * Exchange connector abstraction.
 * Phase 1: Mock/stub implementation.
 * Phase 2: Wire to live Binance/Bitget/Bybit APIs.
 */
export class ExchangeService {
  /**
   * Fetch balances from all connected exchange accounts.
   * TODO: Wire to live APIs using encrypted credentials from P2PAccount.
   */
  async fetchAllBalances(): Promise<ExchangeBalance[]> {
    // Stub: Return mock data until exchange APIs are wired
    return [
      { exchange: 'binance', asset: 'USDT', spotBalance: 3250.42, fundingBalance: 1500.00, totalUsd: 4750.42 },
      { exchange: 'binance', asset: 'BTC', spotBalance: 0.045, fundingBalance: 0, totalUsd: 2890.00 },
      { exchange: 'bitget', asset: 'USDT', spotBalance: 800.00, fundingBalance: 200.00, totalUsd: 1000.00 },
    ];
  }

  /**
   * Fetch P2P order history from an exchange.
   */
  async fetchP2POrders(_exchange: string, _apiKey: string, _apiSecret: string): Promise<unknown[]> {
    // Stub
    return [];
  }

  /**
   * Fetch active P2P advertisements from an exchange.
   */
  async fetchP2PAds(_exchange: string, _apiKey: string, _apiSecret: string): Promise<unknown[]> {
    // Stub
    return [];
  }
}

export interface ExchangeBalance {
  exchange: string;
  asset: string;
  spotBalance: number;
  fundingBalance: number;
  totalUsd: number;
}

export const exchangeService = new ExchangeService();
