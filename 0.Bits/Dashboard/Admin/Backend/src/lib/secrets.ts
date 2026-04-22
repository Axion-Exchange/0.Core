import { createLogger } from './logger.js';

const log = createLogger('secrets');

/**
 * SecretsManager interface — abstraction layer for secret access.
 * 
 * Doc ref: §Secret Management and Zero-Leakage Patterns (citations 43, 45)
 * "Institutional grade systems mandate the use of a centralized secret control plane
 *  like HashiCorp Vault."
 * 
 * Phase 2: EnvSecretsManager (reads from process.env, same as today)
 * Phase 3: VaultSecretsManager (reads from HashiCorp Vault)
 * 
 * By abstracting secret access now, swapping to Vault later is a config change,
 * not a code change.
 */
export interface ISecretsManager {
  /** Get a secret value by key. Returns undefined if not set. */
  get(key: string): Promise<string | undefined>;
  
  /** Get a secret value, throwing if not set (required secrets). */
  getRequired(key: string): Promise<string>;

  /** Check if a secret exists. */
  has(key: string): Promise<boolean>;
}

/**
 * Default implementation: reads secrets from environment variables.
 * Zero behavioral change from the current system.
 */
class EnvSecretsManager implements ISecretsManager {
  async get(key: string): Promise<string | undefined> {
    return process.env[key];
  }

  async getRequired(key: string): Promise<string> {
    const value = process.env[key];
    if (!value) {
      throw new Error(`[Secrets] Required secret "${key}" is not set in environment`);
    }
    return value;
  }

  async has(key: string): Promise<boolean> {
    return process.env[key] !== undefined;
  }
}

/**
 * Placeholder for Phase 3: HashiCorp Vault integration.
 * 
 * Will implement:
 * - Dynamic secrets (temporary DB users, auto-rotating API keys)
 * - Encryption as a Service (crypto ops within Vault)
 * - Audit logging (every secret access tracked)
 */
// class VaultSecretsManager implements ISecretsManager {
//   constructor(private vaultAddr: string, private vaultToken: string) {}
//   async get(key: string): Promise<string | undefined> { ... }
//   async getRequired(key: string): Promise<string> { ... }
//   async has(key: string): Promise<boolean> { ... }
// }

/**
 * Factory: create the appropriate secrets manager based on config.
 * When VAULT_ADDR is set, use VaultSecretsManager; otherwise, use EnvSecretsManager.
 */
function createSecretsManager(): ISecretsManager {
  // Phase 3: uncomment when Vault is deployed
  // if (process.env.VAULT_ADDR && process.env.VAULT_TOKEN) {
  //   log.info('[Secrets] Using HashiCorp Vault');
  //   return new VaultSecretsManager(process.env.VAULT_ADDR, process.env.VAULT_TOKEN);
  // }

  log.info('[Secrets] Using environment variables');
  return new EnvSecretsManager();
}

export const secrets = createSecretsManager();
