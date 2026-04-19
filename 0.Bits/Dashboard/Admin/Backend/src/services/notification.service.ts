import { prisma } from '../lib/db.js';

export class NotificationService {
  async listForAdmin(adminId: string, page: number = 1, limit: number = 25) {
    const [data, total] = await Promise.all([
      prisma.notification.findMany({
        where: { adminId },
        orderBy: { createdAt: 'desc' },
        skip: (page - 1) * limit,
        take: limit,
      }),
      prisma.notification.count({ where: { adminId } }),
    ]);

    return { data, total, page, limit };
  }

  async getUnreadCount(adminId: string): Promise<number> {
    return prisma.notification.count({
      where: { adminId, isRead: false },
    });
  }

  async markAsRead(id: string, adminId: string) {
    return prisma.notification.update({
      where: { id, adminId },
      data: { isRead: true, readAt: new Date() },
    });
  }

  async markAllAsRead(adminId: string) {
    return prisma.notification.updateMany({
      where: { adminId, isRead: false },
      data: { isRead: true, readAt: new Date() },
    });
  }

  async create(data: { adminId: string; type: string; title: string; body: string; actionUrl?: string }) {
    return prisma.notification.create({ data: data as any });
  }

  /**
   * Send a notification to all admins.
   */
  async broadcast(data: { type: string; title: string; body: string; actionUrl?: string }) {
    const admins = await prisma.admin.findMany({ where: { isActive: true }, select: { id: true } });

    return prisma.notification.createMany({
      data: admins.map((admin) => ({
        adminId: admin.id,
        type: data.type as any,
        title: data.title,
        body: data.body,
        actionUrl: data.actionUrl ?? null,
      })),
    });
  }
}

export const notificationService = new NotificationService();
