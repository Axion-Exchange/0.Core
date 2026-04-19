import { prisma } from '../lib/db.js';
import { NotFoundError } from '../middleware/error.js';
import type { KYCStatus, Prisma } from '@prisma/client';

export class UserService {
  async list(filters: { search?: string; kycStatus?: KYCStatus; isBlocked?: boolean; isFrozen?: boolean; page: number; limit: number; sortBy: string; sortOrder: string }) {
    const where: Prisma.UserWhereInput = {};

    if (filters.search) {
      where.OR = [
        { displayName: { contains: filters.search, mode: 'insensitive' } },
        { email: { contains: filters.search, mode: 'insensitive' } },
        { externalId: { contains: filters.search, mode: 'insensitive' } },
      ];
    }
    if (filters.kycStatus) where.kycStatus = filters.kycStatus;
    if (filters.isBlocked !== undefined) where.isBlocked = filters.isBlocked;
    if (filters.isFrozen !== undefined) where.isFrozen = filters.isFrozen;

    const [data, total] = await Promise.all([
      prisma.user.findMany({
        where,
        include: { _count: { select: { orders: true, transactions: true } } },
        orderBy: { [filters.sortBy]: filters.sortOrder },
        skip: (filters.page - 1) * filters.limit,
        take: filters.limit,
      }),
      prisma.user.count({ where }),
    ]);

    return { data, total, page: filters.page, limit: filters.limit };
  }

  async getById(id: string) {
    const user = await prisma.user.findUnique({
      where: { id },
      include: { documents: true, _count: { select: { orders: true, transactions: true, disputes: true } } },
    });
    if (!user) throw new NotFoundError('User', id);
    return user;
  }

  async create(data: { email?: string; phone?: string; displayName: string; legalName?: string; country?: string; externalId?: string; notes?: string }) {
    return prisma.user.create({ data: data as any });
  }

  async update(id: string, data: Record<string, unknown>) {
    return prisma.user.update({ where: { id }, data: data as any });
  }

  async freeze(id: string, frozen: boolean) {
    return prisma.user.update({ where: { id }, data: { isFrozen: frozen } });
  }

  async block(id: string, blocked: boolean, reason?: string) {
    return prisma.user.update({
      where: { id },
      data: { isBlocked: blocked, blockedReason: blocked ? (reason ?? null) : null },
    });
  }

  async listByKycStatus(status: KYCStatus, page: number = 1, limit: number = 25) {
    const where: Prisma.UserWhereInput = { kycStatus: status };
    const [data, total] = await Promise.all([
      prisma.user.findMany({ where, orderBy: { updatedAt: 'desc' }, skip: (page - 1) * limit, take: limit }),
      prisma.user.count({ where }),
    ]);
    return { data, total, page, limit };
  }

  async approveKyc(userId: string, adminId: string) {
    await prisma.user.update({ where: { id: userId }, data: { kycStatus: 'APPROVED' } });
    await prisma.userDocument.updateMany({
      where: { userId, verificationStatus: 'PENDING' },
      data: { verificationStatus: 'APPROVED', reviewedById: adminId, reviewedAt: new Date() },
    });
  }

  async rejectKyc(userId: string, adminId: string, reason?: string) {
    await prisma.user.update({ where: { id: userId }, data: { kycStatus: 'REJECTED' } });
    await prisma.userDocument.updateMany({
      where: { userId, verificationStatus: 'PENDING' },
      data: { verificationStatus: 'REJECTED', rejectionReason: reason ?? null, reviewedById: adminId, reviewedAt: new Date() },
    });
  }

  async listBlocked(page: number = 1, limit: number = 25) {
    const where: Prisma.UserWhereInput = { isBlocked: true };
    const [data, total] = await Promise.all([
      prisma.user.findMany({ where, orderBy: { updatedAt: 'desc' }, skip: (page - 1) * limit, take: limit }),
      prisma.user.count({ where }),
    ]);
    return { data, total, page, limit };
  }
}

export const userService = new UserService();
