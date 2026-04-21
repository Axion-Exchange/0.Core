import { z } from 'zod';
import 'dotenv/config';

/**
 * Zod-validated environment configuration.
 * Fails fast at startup if required variables are missing.
 */
const envSchema = z.object({
  // Server
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
  PORT: z.coerce.number().default(4000),

  // Database
  DATABASE_URL: z.string().min(1, 'DATABASE_URL is required'),

  // Auth
  JWT_SECRET: z.string().min(32, 'JWT_SECRET must be at least 32 characters'),
  JWT_EXPIRES_IN: z.string().default('24h'),
  JWT_REFRESH_EXPIRES_IN: z.string().default('7d'),

  // CORS (Defaults gracefully to explicit prod and dev environments)
  CORS_ORIGINS: z.string().default('http://localhost:5173,https://0bit.app,https://www.0bit.app'),

  // Encryption
  ENCRYPTION_KEY: z.string().optional(),

  // Exchange connectors
  BINANCE_API_KEY: z.string().optional(),
  BINANCE_API_SECRET: z.string().optional(),
  BINANCE_API_PRIVATE_KEY_PATH: z.string().optional(),
  BITGET_API_KEY: z.string().optional(),
  BITGET_API_SECRET: z.string().optional(),
  BITGET_PASSPHRASE: z.string().optional(),

  // Fiat rails
  JANUAR_API_KEY: z.string().optional(),
  JANUAR_API_SECRET: z.string().optional(),
  JANUAR_WEBHOOK_SECRET: z.string().optional(),
  FACILITAPAY_USERNAME: z.string().optional(),
  FACILITAPAY_PASSWORD: z.string().optional(),

  // Logging
  LOG_LEVEL: z.enum(['debug', 'info', 'warn', 'error']).default('info'),
});

function loadConfig() {
  const parsed = envSchema.safeParse(process.env);

  if (!parsed.success) {
    const formatted = parsed.error.issues
      .map((i) => `  ✗ ${i.path.join('.')}: ${i.message}`)
      .join('\n');
    console.error(`\n[CONFIG] Environment validation failed:\n${formatted}\n`);
    process.exit(1);
  }

  return parsed.data;
}

export const config = loadConfig();

export const isProduction = config.NODE_ENV === 'production';
export const isDevelopment = config.NODE_ENV === 'development';
