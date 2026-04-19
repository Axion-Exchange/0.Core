import { z } from 'zod';

export const createAdSchema = z.object({
  accountId: z.string().uuid(),
  asset: z.string().min(1).max(10),
  fiat: z.string().min(1).max(10),
  type: z.enum(['BUY', 'SELL']),
  price: z.coerce.number().positive(),
  marginPercent: z.coerce.number(),
  minLimit: z.coerce.number().positive(),
  maxLimit: z.coerce.number().positive(),
  availableQty: z.coerce.number().min(0).optional(),
  autoReply: z.string().optional(),
  remarks: z.string().optional(),
});

export const updateAdSchema = createAdSchema.partial().extend({
  status: z.enum(['ACTIVE', 'PAUSED', 'DEPLETED', 'ARCHIVED']).optional(),
});

export const toggleAdSchema = z.object({
  enabled: z.boolean(),
});

export const createAccountSchema = z.object({
  exchange: z.enum(['BINANCE', 'BITGET']),
  label: z.string().min(1).max(100),
  apiKey: z.string().min(1),
  apiSecret: z.string().min(1),
  passphrase: z.string().optional(),
  region: z.string().max(10).optional(),
});

export const createOrderSchema = z.object({
  externalOrderId: z.string().optional(),
  advertisementId: z.string().uuid().optional(),
  asset: z.string().min(1).max(10),
  amount: z.coerce.number().positive(),
  fiat: z.string().min(1).max(10),
  fiatAmount: z.coerce.number().positive(),
  price: z.coerce.number().positive(),
  type: z.enum(['BUY', 'SELL']),
  counterparty: z.string().optional(),
  paymentMethod: z.string().optional(),
});

export const createDisputeSchema = z.object({
  orderId: z.string().uuid(),
  reason: z.string().min(1),
  description: z.string().optional(),
  evidenceUrls: z.array(z.string().url()).optional(),
});

export const resolveDisputeSchema = z.object({
  resolution: z.string().min(1),
  resolvedInFavor: z.enum(['buyer', 'seller']),
});

export const createPaymentMethodSchema = z.object({
  label: z.string().min(1),
  type: z.enum(['BANK_TRANSFER', 'PIX', 'PSE', 'SPEI', 'MOBILE_MONEY', 'CARD', 'CRYPTO_WALLET']).default('BANK_TRANSFER'),
  bankName: z.string().optional(),
  accountName: z.string().optional(),
  accountNumber: z.string().optional(),
  routingNumber: z.string().optional(),
  swiftCode: z.string().optional(),
  currency: z.string().length(3),
  country: z.string().length(3).optional(),
  region: z.string().max(10).optional(),
  dailyLimit: z.coerce.number().optional(),
  monthlyLimit: z.coerce.number().optional(),
});
