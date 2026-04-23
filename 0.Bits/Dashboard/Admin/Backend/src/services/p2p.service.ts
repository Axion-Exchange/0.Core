import { prisma } from '../lib/db.js';
import { safeTransaction } from '../lib/transaction.js';
import { encrypt, decrypt } from '../lib/crypto.js';
import { NotFoundError } from '../middleware/error.js';
import type { AdStatus, OrderStatus, DisputeStatus, Prisma } from '@prisma/client';
import { binanceService } from './binance.service.js';
import { getSocket } from '../lib/socket.js';

export class P2PService {
  // ── Accounts ───────────────────────────────────────────

  async listAccounts() {
    return prisma.p2PAccount.findMany({
      include: { _count: { select: { advertisements: true, wallets: true } } },
      orderBy: { createdAt: 'desc' },
    });
  }

  async createAccount(data: { exchange: string; label: string; apiKey: string; apiSecret: string; passphrase?: string; region?: string }) {
    return prisma.p2PAccount.create({
      data: {
        exchange: data.exchange as any,
        label: data.label,
        apiKeyEnc: encrypt(data.apiKey),
        apiSecretEnc: encrypt(data.apiSecret),
        passphraseEnc: data.passphrase ? encrypt(data.passphrase) : null,
        region: data.region ?? null,
      },
    });
  }

  async updateAccount(id: string, data: Partial<{ label: string; region: string; isActive: boolean }>) {
    return prisma.p2PAccount.update({ where: { id }, data });
  }

  async deleteAccount(id: string) {
    return prisma.p2PAccount.delete({ where: { id } });
  }

  // ── Advertisements ─────────────────────────────────────

  async listAds(filters?: { accountId?: string; status?: AdStatus; asset?: string; fiat?: string; type?: string; page?: number; limit?: number }) {
    const page = filters?.page ?? 1;
    const limit = filters?.limit ?? 25;
    const where: Prisma.P2PAdvertisementWhereInput = {};

    if (filters?.accountId) where.accountId = filters.accountId;
    if (filters?.status) where.status = filters.status;
    if (filters?.asset) where.asset = filters.asset;
    if (filters?.fiat) where.fiat = filters.fiat;
    if (filters?.type) where.type = filters.type as any;

    const [data, total] = await Promise.all([
      prisma.p2PAdvertisement.findMany({
        where,
        include: { account: { select: { exchange: true, label: true } } },
        orderBy: { createdAt: 'desc' },
        skip: (page - 1) * limit,
        take: limit,
      }),
      prisma.p2PAdvertisement.count({ where }),
    ]);

    return { data, total, page, limit };
  }

  async createAd(data: { accountId: string; asset: string; fiat: string; type: string; price: number; marginPercent: number; minLimit: number; maxLimit: number; availableQty?: number; autoReply?: string; remarks?: string }) {
    return prisma.p2PAdvertisement.create({
      data: {
        accountId: data.accountId,
        asset: data.asset,
        fiat: data.fiat,
        type: data.type as any,
        price: data.price,
        marginPercent: data.marginPercent,
        minLimit: data.minLimit,
        maxLimit: data.maxLimit,
        availableQty: data.availableQty ?? 0,
        autoReply: data.autoReply ?? null,
        remarks: data.remarks ?? null,
      },
    });
  }

  async updateAd(id: string, data: Record<string, unknown>) {
    return prisma.p2PAdvertisement.update({ where: { id }, data: data as any });
  }

  async toggleAd(id: string, enabled: boolean) {
    const ad = await prisma.p2PAdvertisement.findUnique({
      where: { id },
      include: { account: true }
    });

    if (!ad) throw new NotFoundError('Advertisement', id);

    if (ad.externalAdId && ad.account.exchange === 'BINANCE') {
       const success = await binanceService.toggleAdStatus(ad.externalAdId, enabled ? 'Active' : 'Paused', ad.account);
       if (!success) {
         throw new Error(`Failed to toggle ad ${ad.externalAdId} on Binance`);
       }
    }

    const updated = await prisma.p2PAdvertisement.update({
      where: { id },
      data: { status: enabled ? 'ACTIVE' : 'PAUSED' },
    });

    try {
      const io = getSocket();
      io.emit('ad:update', { id: updated.id, status: updated.status, externalAdId: updated.externalAdId });
    } catch(err) {
      // Ignore socket errors if no clients connected
    }

    return updated;
  }

  // ── Orders ─────────────────────────────────────────────

  async listOrders(filters?: { accountId?: string; status?: OrderStatus; asset?: string; type?: string; from?: Date; to?: Date; page?: number; limit?: number }) {
    const page = filters?.page ?? 1;
    const limit = filters?.limit ?? 25;
    const where: Prisma.P2POrderWhereInput = {};

    if (filters?.accountId) where.accountId = filters.accountId;
    if (filters?.status) where.status = filters.status;
    if (filters?.asset) where.asset = filters.asset;
    if (filters?.type) where.type = filters.type as any;
    if (filters?.from || filters?.to) {
      where.createdAt = {};
      if (filters?.from) where.createdAt.gte = filters.from;
      if (filters?.to) where.createdAt.lte = filters.to;
    }

    const [data, total] = await Promise.all([
      prisma.p2POrder.findMany({
        where,
        include: {
          advertisement: { select: { asset: true, fiat: true, type: true } },
          user: { select: { displayName: true } },
        },
        orderBy: { createdAt: 'desc' },
        skip: (page - 1) * limit,
        take: limit,
      }),
      prisma.p2POrder.count({ where }),
    ]);

    return { data, total, page, limit };
  }

  async getOrder(id: string) {
    const order = await prisma.p2POrder.findUnique({
      where: { id },
      include: {
        advertisement: true,
        user: true,
        disputes: true,
      },
    });
    if (!order) throw new NotFoundError('Order', id);
    return order;
  }

  async updateOrderStatus(id: string, status: OrderStatus) {
    const now = new Date();
    const data: Record<string, unknown> = { status };

    if (status === 'COMPLETED') data['completedAt'] = now;
    if (status === 'CANCELLED') data['cancelledAt'] = now;

    return prisma.p2POrder.update({ where: { id }, data: data as any });
  }

  // ── Disputes ───────────────────────────────────────────

  async listDisputes(filters?: { status?: DisputeStatus; page?: number; limit?: number }) {
    const page = filters?.page ?? 1;
    const limit = filters?.limit ?? 25;
    const where: Prisma.P2PDisputeWhereInput = {};

    if (filters?.status) where.status = filters.status;

    const [data, total] = await Promise.all([
      prisma.p2PDispute.findMany({
        where,
        include: {
          order: { select: { externalOrderId: true, asset: true, fiatAmount: true } },
          assignedTo: { select: { displayName: true } },
        },
        orderBy: { createdAt: 'desc' },
        skip: (page - 1) * limit,
        take: limit,
      }),
      prisma.p2PDispute.count({ where }),
    ]);

    return { data, total, page, limit };
  }

  async createDispute(data: { orderId: string; reason: string; description?: string; evidenceUrls?: string[]; filedBy: string }) {
    return prisma.p2PDispute.create({
      data: {
        orderId: data.orderId,
        reason: data.reason,
        description: data.description ?? null,
        evidenceUrls: data.evidenceUrls ?? [],
        filedBy: data.filedBy,
      },
    });
  }

  async resolveDispute(id: string, data: { resolution: string; resolvedInFavor: string; adminId: string }) {
    // Atomic: resolve dispute + update linked order status in one transaction
    return safeTransaction(async (tx) => {
      const dispute = await tx.p2PDispute.update({
        where: { id },
        data: {
          status: data.resolvedInFavor === 'buyer' ? 'RESOLVED_BUYER' : 'RESOLVED_SELLER',
          resolution: data.resolution,
          resolvedInFavor: data.resolvedInFavor,
          resolvedAt: new Date(),
          assignedToId: data.adminId,
        },
      });
      // Also close the linked order atomically
      await tx.p2POrder.update({
        where: { id: dispute.orderId },
        data: { status: data.resolvedInFavor === 'buyer' ? 'CANCELLED' : 'COMPLETED', completedAt: new Date() },
      });
      return dispute;
    }, { label: 'resolve-dispute' });
  }

  // ── Payment Methods ────────────────────────────────────

  async listPaymentMethods() {
    return prisma.paymentMethod.findMany({
      orderBy: [{ isPrimary: 'desc' }, { createdAt: 'desc' }],
    });
  }

  async createPaymentMethod(data: Record<string, unknown>) {
    return prisma.paymentMethod.create({ data: data as any });
  }

  async updatePaymentMethod(id: string, data: Record<string, unknown>) {
    return prisma.paymentMethod.update({ where: { id }, data: data as any });
  }

  async deletePaymentMethod(id: string) {
    return prisma.paymentMethod.delete({ where: { id } });
  }
}

export const p2pService = new P2PService();
