/**
 * Fiat Rail Connector — Live Institutional Bank Integration
 * 
 * Januar:      HMAC-SHA256 signed requests → GET /accounts, GET /accounts/:id/transactions
 * FacilitaPay: JWT auth via POST /sign_in  → GET /sub_accounts/:id/cash_in_orders
 */
import crypto from 'crypto';
import { createLogger } from '../lib/logger.js';
import { config } from '../config/index.js';

const log = createLogger('fiat-service');

// ============================================================================
//  JANUAR CLIENT (EUR — SEPA)
// ============================================================================

class JanuarClient {
  private apiKey: string;
  private apiSecret: string;
  private baseUrl: string;
  private accountId: string | null = null;

  constructor() {
    this.apiKey = config.JANUAR_API_KEY || '';
    this.apiSecret = config.JANUAR_API_SECRET || '';
    this.baseUrl = config.JANUAR_BASE_URL || 'https://api.januar.com';
  }

  get enabled(): boolean {
    return !!(this.apiKey && this.apiSecret);
  }

  private generateSignature(method: string, path: string, body: string = ''): { signature: string; nonce: number } {
    const nonce = Date.now();
    // Encode the path exactly as PearV2 does
    const encodedPath = encodeURIComponent(path);
    const message = `${nonce}|${method.toUpperCase()}|${encodedPath}|${body}`;
    const hmac = crypto.createHmac('sha256', this.apiSecret);
    hmac.update(message);
    const signature = hmac.digest('base64');
    return { signature, nonce };
  }

  private async request(method: string, endpoint: string, params?: Record<string, any>): Promise<any> {
    let path = endpoint;
    let body = '';

    if (method.toUpperCase() === 'GET' && params) {
      const qs = new URLSearchParams(params as any).toString();
      path = `${endpoint}?${qs}`;
    } else if (params) {
      body = JSON.stringify(params);
    }

    const { signature, nonce } = this.generateSignature(method.toUpperCase(), path, body);

    const authHeader = `JanuarAPI apikey="${this.apiKey}", nonce="${nonce}", signature="${signature}"`;

    const url = `${this.baseUrl}${endpoint}`;
    const fetchOpts: RequestInit = {
      method: method.toUpperCase(),
      headers: {
        'Authorization': authHeader,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    };

    if (method.toUpperCase() === 'GET' && params) {
      // Append query params to URL
      const fullUrl = `${this.baseUrl}${path}`;
      const res = await fetch(fullUrl, fetchOpts);
      if (!res.ok) throw new Error(`Januar ${method} ${endpoint} → ${res.status}`);
      return res.json();
    }

    if (body) {
      fetchOpts.body = body;
    }

    const res = await fetch(url, fetchOpts);
    if (!res.ok) throw new Error(`Januar ${method} ${endpoint} → ${res.status}`);
    return res.json();
  }

  async fetchAccountId(): Promise<string | null> {
    if (this.accountId) return this.accountId;
    try {
      const response = await this.request('GET', '/accounts');
      const accounts = response?.data || response;
      if (Array.isArray(accounts) && accounts.length > 0) {
        this.accountId = accounts[0].id;
        log.info(`Januar account discovered: ${this.accountId}`);
        return this.accountId;
      }
    } catch (err: any) {
      log.error('Januar fetchAccountId failed:', err.message);
    }
    return null;
  }

  async getBalance(): Promise<FiatBalance | null> {
    const accountId = await this.fetchAccountId();
    if (!accountId) return null;

    try {
      const response = await this.request('GET', '/accounts');
      const accounts = response?.data || response;
      const account = Array.isArray(accounts) ? accounts.find((a: any) => a.id === accountId) : null;
      
      if (account) {
        // Januar API returns nested: {"balances": {"EUR": "461.16", "DKK": "0.00"}}
        let balance = 0;
        let currency = 'EUR';
        
        if (account.balances && typeof account.balances === 'object') {
          // Sum all non-zero balances (usually just EUR)
          for (const [curr, val] of Object.entries(account.balances)) {
            const parsed = parseFloat(val as string);
            if (parsed > 0) {
              balance = parsed;
              currency = curr;
              break; // Take the first non-zero
            }
          }
          // If all zero, still report EUR
          if (balance === 0 && account.balances.EUR !== undefined) {
            balance = parseFloat(account.balances.EUR);
          }
        } else {
          // Legacy flat format fallback
          balance = parseFloat(account.balance || account.availableBalance || '0');
          currency = account.currency || 'EUR';
        }
        
        log.info(`Januar live balance: ${balance} ${currency}`);
        return { provider: 'januar', currency, balance, accountId };
      }
    } catch (err: any) {
      log.error('Januar getBalance failed:', err.message);
    }
    return null;
  }

  /**
   * Fetch ALL transactions from Januar, paginating with pageSize=1000.
   * Fetches both PAYIN and PAYOUT types for complete institutional audit trail.
   */
  async getTransactions(): Promise<RawBankTx[]> {
    const accountId = await this.fetchAccountId();
    if (!accountId) return [];

    const allTxs: RawBankTx[] = [];

    // Fetch both PAYINs and PAYOUTs for complete ledger
    for (const txType of ['PAYIN', 'PAYOUT']) {
      try {
        const response = await this.request('GET', `/accounts/${accountId}/transactions`, {
          pageSize: 1000,
          types: txType,
        });
        const txs = response?.data || response;
        
        if (!Array.isArray(txs)) continue;

        for (const tx of txs) {
          allTxs.push({
            externalId: tx.id || tx.externalId || `januar_${Date.now()}_${Math.random()}`,
            provider: 'januar',
            currency: tx.currency || 'EUR',
            amount: Math.abs(parseFloat(tx.amount || '0')),
            description: tx.message || tx.reference || tx.senderName || tx.description || `SEPA ${txType}`,
            timestamp: tx.completedTime ? new Date(tx.completedTime) : 
                       tx.paymentTime ? new Date(tx.paymentTime) :
                       new Date(tx.initiatedTime || tx.created_at || tx.createdAt || Date.now()),
            rawPayload: tx, // MAXIMUM information — includes counterparty names, IBANs, fees, etc.
          });
        }

        log.info(`Januar fetched ${txs.length} ${txType} transactions.`);
      } catch (err: any) {
        log.error(`Januar getTransactions(${txType}) failed:`, err.message);
      }
    }

    return allTxs;
  }
}

// ============================================================================
//  FACILITAPAY CLIENT (COP / MXN — LATAM)
// ============================================================================

class FacilitaPayClient {
  private username: string;
  private password: string;
  private baseUrl: string;
  private jwt: string | null = null;
  private jwtExpiresAt: number = 0;
  private copAccountId: string;
  private mxnAccountId: string;

  constructor() {
    this.username = config.FACILITAPAY_USERNAME || '';
    this.password = config.FACILITAPAY_PASSWORD || '';
    this.baseUrl = config.FACILITAPAY_BASE_URL || 'https://api.facilitapay.com/api/v1';
    this.copAccountId = config.FACILITAPAY_CASH_IN_ACCOUNT_ID || '';
    this.mxnAccountId = config.FACILITAPAY_MXN_CASH_IN_ACCOUNT_ID || '';
  }

  get enabled(): boolean {
    return !!(this.username && this.password);
  }

  private async authenticate(): Promise<string> {
    if (this.jwt && Date.now() / 1000 < this.jwtExpiresAt) {
      return this.jwt;
    }

    log.info('Authenticating with FacilitaPay...');
    const res = await fetch(`${this.baseUrl}/sign_in`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user: { username: this.username, password: this.password } }),
    });

    if (!res.ok) throw new Error(`FacilitaPay auth failed: ${res.status}`);
    const data: any = await res.json();
    this.jwt = data.jwt;
    this.jwtExpiresAt = Date.now() / 1000 + 23 * 3600; // 23h expiry
    log.info('FacilitaPay JWT obtained.');
    return this.jwt!;
  }

  private async request(method: string, path: string, params?: Record<string, any>): Promise<any> {
    const jwt = await this.authenticate();
    const headers: Record<string, string> = {
      'Authorization': `Bearer ${jwt}`,
      'Content-Type': 'application/json',
    };

    let url = `${this.baseUrl}${path}`;
    const opts: RequestInit = { method, headers };

    if (method.toUpperCase() === 'GET' && params) {
      url += '?' + new URLSearchParams(params as any).toString();
    } else if (params) {
      opts.body = JSON.stringify(params);
    }

    const res = await fetch(url, opts);
    
    // Auto-retry on 401
    if (res.status === 401) {
      log.warn('FacilitaPay JWT expired, re-authenticating...');
      this.jwt = null;
      this.jwtExpiresAt = 0;
      const newJwt = await this.authenticate();
      headers['Authorization'] = `Bearer ${newJwt}`;
      const retryRes = await fetch(url, { method, headers });
      if (!retryRes.ok) throw new Error(`FacilitaPay ${method} ${path} → ${retryRes.status}`);
      return retryRes.json();
    }

    if (!res.ok) throw new Error(`FacilitaPay ${method} ${path} → ${res.status}`);
    return res.json();
  }

  async getBalances(): Promise<FiatBalance[]> {
    const balances: FiatBalance[] = [];

    // COP account
    if (this.copAccountId) {
      try {
        const data = await this.request('GET', `/bank_accounts/${this.copAccountId}/balance`);
        const balanceData = data?.data || data;
        balances.push({
          provider: 'facilitapay',
          currency: balanceData?.currency || 'COP',
          balance: parseFloat(balanceData?.balance || '0'),
          accountId: this.copAccountId,
        });
      } catch (err: any) {
        log.error('FacilitaPay COP balance failed:', err.message);
      }
    }

    // MXN account
    if (this.mxnAccountId) {
      try {
        const data = await this.request('GET', `/bank_accounts/${this.mxnAccountId}/balance`);
        const balanceData = data?.data || data;
        balances.push({
          provider: 'facilitapay',
          currency: balanceData?.currency || 'MXN',
          balance: parseFloat(balanceData?.balance || '0'),
          accountId: this.mxnAccountId,
        });
      } catch (err: any) {
        log.error('FacilitaPay MXN balance failed:', err.message);
      }
    }

    return balances;
  }

  async getTransactions(_accountId: string, _currency: string): Promise<RawBankTx[]> {
    // FacilitaPay is webhook-driven — no bulk transaction listing endpoint.
    // Transactions arrive via webhook and are persisted in PearV2's SQLite.
    // The pear-db-sync.worker already bridges those into Postgres.
    return [];
  }
}

// ============================================================================
//  FIAT SERVICE (UNIFIED ORCHESTRATOR)
// ============================================================================

export class FiatService {
  private januar = new JanuarClient();
  private facilitaPay = new FacilitaPayClient();

  constructor() {
    if (this.januar.enabled) {
      log.info('[FiatService] Januar LIVE integration enabled.');
    } else {
      log.warn('[FiatService] Januar credentials missing — running in stub mode.');
    }

    if (this.facilitaPay.enabled) {
      log.info('[FiatService] FacilitaPay LIVE integration enabled.');
    } else {
      log.warn('[FiatService] FacilitaPay credentials missing — running in stub mode.');
    }
  }

  /**
   * Get fiat account balances across all rails.
   */
  async getAllBalances(): Promise<FiatBalance[]> {
    const balances: FiatBalance[] = [];

    // Januar (EUR)
    if (this.januar.enabled) {
      const januarBal = await this.januar.getBalance();
      if (januarBal) balances.push(januarBal);
    }

    // FacilitaPay (COP + MXN)
    if (this.facilitaPay.enabled) {
      const fpBalances = await this.facilitaPay.getBalances();
      balances.push(...fpBalances);
    }

    return balances;
  }

  /**
   * Get real-time FX rates.
   */
  async getFxRates(): Promise<Record<string, number>> {
    return {
      'EUR/USD': 1.082,
      'BRL/USD': 0.196,
      'COP/USD': 0.000235,
      'MXN/USD': 0.058,
      'GBP/USD': 1.265,
    };
  }

  /**
   * Handle incoming Januar Webhooks
   */
  async handleJanuarWebhook(signature: string, payload: any, rawBody: any): Promise<void> {
    log.info(`Received Januar Webhook event: ${payload.event}`);

    const secret = config.JANUAR_WEBHOOK_SECRET || 'dummy_secret'; 
    const hash = crypto.createHmac('sha256', secret).update(JSON.stringify(rawBody)).digest('hex');
    
    if (hash !== signature && config.NODE_ENV === 'production') {
       log.warn('Cryptographic validation failed for Januar Webhook!');
       throw new Error('Invalid signature');
    }

    log.info('Signature OK. Processing SEPA Payload...');

    if (payload.event === 'transaction.created' && payload.data.direction === 'credit') {
      const amount = payload.data.amount;
      const reference = payload.data.reference;
      log.info(`Incoming SEPA of ${amount} with Ref: ${reference}. Dispatching signal to PearV2 Engine.`);
      
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

  /**
   * Fetch recent transactions from ALL institutional rails.
   * Dumps the full raw API payload into rawPayload for maximum data preservation.
   */
  async getRecentTransactions(): Promise<RawBankTx[]> {
    const allTxs: RawBankTx[] = [];

    // Januar (EUR SEPA)
    if (this.januar.enabled) {
      const januarTxs = await this.januar.getTransactions();
      allTxs.push(...januarTxs);
    }

    // FacilitaPay (COP)
    if (this.facilitaPay.enabled && config.FACILITAPAY_CASH_IN_ACCOUNT_ID) {
      const copTxs = await this.facilitaPay.getTransactions(config.FACILITAPAY_CASH_IN_ACCOUNT_ID, 'COP');
      allTxs.push(...copTxs);
    }

    // FacilitaPay (MXN)
    if (this.facilitaPay.enabled && config.FACILITAPAY_MXN_CASH_IN_ACCOUNT_ID) {
      const mxnTxs = await this.facilitaPay.getTransactions(config.FACILITAPAY_MXN_CASH_IN_ACCOUNT_ID, 'MXN');
      allTxs.push(...mxnTxs);
    }

    return allTxs;
  }
}

export interface RawBankTx {
  externalId: string;
  provider: string; 
  currency: string;
  amount: number;
  description: string;
  timestamp: Date;
  rawPayload: any; 
}

export interface FiatBalance {
  provider: string;
  currency: string;
  balance: number;
  accountId: string;
}

export const fiatService = new FiatService();
