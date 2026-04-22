/**
 * Feature Flags Service — Redis-backed kill switches
 * 
 * Provides instant enable/disable toggles for critical subsystems.
 * All flags are stored in Redis for sub-millisecond reads.
 * 
 * Usage in workers:
 *   if (await featureFlags.isEnabled("EUR_P2P")) { ... }
 *   
 * Changes take effect immediately — no deployment required.
 */

import { createLogger } from "../lib/logger.js";
import { redis } from "../lib/redis.js";

const log = createLogger("feature-flags");

const FLAG_PREFIX = "ff:";

export interface FeatureFlag {
  name: string;
  enabled: boolean;
  description: string;
  lastModified: string;
  modifiedBy: string;
}

// Default flags — created on first boot if not present
const DEFAULT_FLAGS: Record<string, { enabled: boolean; description: string }> = {
  EUR_P2P:          { enabled: true,  description: "EUR P2P order processing" },
  MXN_P2P:          { enabled: true,  description: "MXN P2P order processing" },
  COP_P2P:          { enabled: true,  description: "COP P2P order processing" },
  GBP_P2P:          { enabled: true,  description: "GBP P2P order processing" },
  AUTO_RELEASE:     { enabled: true,  description: "Automatic order release on payment match" },
  PRICING_ENGINE:   { enabled: true,  description: "Dynamic pricing engine for sell ads" },
  BINANCE_SYNC:     { enabled: true,  description: "Binance trade/balance sync worker" },
  FIAT_SYNC:        { enabled: true,  description: "Januar/FacilitaPay fiat sync worker" },
  KYC_VERIFICATION: { enabled: true,  description: "KYC verification flow" },
  FRAUD_SCAN:       { enabled: true,  description: "Automated fraud pattern scanning" },
  BQ_SYNC:          { enabled: true,  description: "BigQuery data sync worker" },
  HEALTH_WORKER:    { enabled: true,  description: "Health check worker" },
};

class FeatureFlagsService {
  async initialize(): Promise<void> {
    // using imported redis singleton
    const flagNames = Object.keys(DEFAULT_FLAGS);
    for (const name of flagNames) {
      const exists = await redis.exists(`${FLAG_PREFIX}${name}`);
      if (!exists) {
        
        await redis.hset(`${FLAG_PREFIX}${name}`, {
          enabled: DEFAULT_FLAGS[name]!.enabled ? "1" : "0",
          description: DEFAULT_FLAGS[name]!.description,
          lastModified: new Date().toISOString(),
          modifiedBy: "system",
        });
      }
    }
    log.info(`[FeatureFlags] ${flagNames.length} flags initialized`);
  }

  async isEnabled(flagName: string): Promise<boolean> {
    try {
      // using imported redis singleton
      const val = await redis.hget(`${FLAG_PREFIX}${flagName}`, "enabled");
      return val !== "0";
    } catch {
      return true;
    }
  }

  async setFlag(flagName: string, enabled: boolean, modifiedBy: string = "admin"): Promise<void> {
    // using imported redis singleton
    await redis.hset(`${FLAG_PREFIX}${flagName}`, {
      enabled: enabled ? "1" : "0",
      lastModified: new Date().toISOString(),
      modifiedBy,
    });
    log.warn(`[FeatureFlags] ${flagName} => ${enabled ? "ENABLED" : "DISABLED"} by ${modifiedBy}`);
  }

  async getAllFlags(): Promise<FeatureFlag[]> {
    // using imported redis singleton
    const flags: FeatureFlag[] = [];
    const flagNames = Object.keys(DEFAULT_FLAGS);

    for (const name of flagNames) {
      const data = await redis.hgetall(`${FLAG_PREFIX}${name}`);
      flags.push({
        name,
        enabled: data.enabled !== "0",
        description: data.description || (DEFAULT_FLAGS[name] ? DEFAULT_FLAGS[name].description : ""),
        lastModified: data.lastModified || "",
        modifiedBy: data.modifiedBy || "system",
      });
    }

    return flags;
  }
}

export const featureFlags = new FeatureFlagsService();
