import * as ccxt from 'ccxt';
import { prisma } from '../lib/db.js';
import { decrypt } from '../lib/crypto.js';
import { createLogger } from '../lib/logger.js';
import type { P2PAccount } from '@prisma/client';

const log = createLogger('exchange-service');

export class ExchangeService {
  private clients = new Map<string, ccxt.Exchange>();

  /**
   * Initialize or refresh CCXT clients for all active P2P accounts.
   */
  async loadClients() {
    const accounts = await prisma.p2PAccount.findMany({ where: { isActive: true } });
    
    for (const account of accounts) {
      if (!this.clients.has(account.id)) {
        try {
          const ccxtLib = ccxt as any;
          const exchangeClass = ccxtLib[account.exchange.toLowerCase()];
          
          if (!exchangeClass) {
            log.error(`Unsupported exchange: ${account.exchange}`, { accountId: account.id });
            continue;
          }

          const client = new exchangeClass({
            apiKey: decrypt(account.apiKeyEnc),
            secret: decrypt(account.apiSecretEnc),
            ...(account.passphraseEnc ? { password: decrypt(account.passphraseEnc) } : {}),
            enableRateLimit: true,
          });

          this.clients.set(account.id, client);
          log.info(`CCXT client loaded`, { exchange: account.exchange, accountId: account.id });
        } catch (error) {
          log.error('Failed to load CCXT client', { accountId: account.id, error });
        }
      }
    }
  }

  /**
   * Example: Concurrent execution of an action across all active accounts.
   * This is the institutional skeleton for handling multiple parallel operations.
   */
  private async executeConcurrently<T>(action: (client: ccxt.Exchange, account: P2PAccount) => Promise<T>) {
    await this.loadClients();
    const accounts = await prisma.p2PAccount.findMany({ where: { isActive: true } });

    const promises = accounts.map(async (account) => {
      const client = this.clients.get(account.id);
      if (!client) throw new Error(`Missing client for account ${account.id}`);
      return action(client, account);
    });

    return Promise.allSettled(promises);
  }

  /**
   * Fetch balances concurrently from all configured CCXT instances.
   */
  async fetchAllBalances(): Promise<ExchangeBalance[]> {
    const results = await this.executeConcurrently(async (client, account) => {
      // Stub implementation: a real implementation would use client.fetchBalance()
      // Because this is a skeleton, we simulate the network delay.
      await new Promise(res => setTimeout(res, 100)); 
      
      return [
        { exchange: account.exchange, accountId: account.id, asset: 'USDT', spotBalance: 1000, fundingBalance: 500, totalUsd: 1500 },
      ];
    });

    const balances: ExchangeBalance[] = [];
    for (const res of results) {
      if (res.status === 'fulfilled') balances.push(...res.value);
      else log.error('Balance fetch failed for an account', { error: res.reason });
    }
    
    return balances;
  }

  /**
   * Fetch P2P orders concurrently across all accounts.
   * CCXT does not have a unified P2P API, so this skeleton prepares
   * the routing to exchange-specific private API endpoints (e.g., sapiGet).
   */
  async fetchConcurrentP2POrders() {
    return this.executeConcurrently(async (client, account) => {
      // if (account.exchange === 'BINANCE') -> client.sapiGetC2cOrderMatchListUserOrderHistory()
      // if (account.exchange === 'BITGET') -> client.privateGetP2pOrders()
      await new Promise(res => setTimeout(res, 50));
      return [];
    });
  }

  /**
   * Fetch active P2P advertisements concurrently across all accounts.
   */
  async fetchConcurrentP2PAds() {
    return this.executeConcurrently(async (client, account) => {
      await new Promise(res => setTimeout(res, 50));
      return [];
    });
  }
}

export interface ExchangeBalance {
  exchange: string;
  accountId?: string;
  asset: string;
  spotBalance: number;
  fundingBalance: number;
  totalUsd: number;
}

export const exchangeService = new ExchangeService();
