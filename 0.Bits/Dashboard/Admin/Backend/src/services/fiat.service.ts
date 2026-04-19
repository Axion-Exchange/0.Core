/**
 * Fiat rail connector abstraction.
 * Phase 1: Mock/stub implementation.
 * Phase 2: Wire to live Januar (SEPA) and FacilitaPay (LATAM) APIs.
 */
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
}

export interface FiatBalance {
  provider: string;
  currency: string;
  balance: number;
  accountId: string;
}

export const fiatService = new FiatService();
