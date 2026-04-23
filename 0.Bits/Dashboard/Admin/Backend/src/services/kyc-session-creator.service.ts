import { prisma } from '../lib/db.js';
import { createLogger } from '../lib/logger.js';
import { diditService } from './didit.service.js';

const log = createLogger('kyc-session-creator');

export interface CreateSessionResult {
  sessionId: string;
  sessionUrl: string;
  status: string;
}

export class KycSessionCreatorService {

  /**
   * Create a session specifically for a P2P order counterparty.
   * Embeds the order ID as vendor_data for automatic linking.
   */
  async createSessionForOrder(orderId: string, email?: string): Promise<CreateSessionResult> {
    const order = await prisma.p2POrder.findUnique({
      where: { id: orderId },
      select: { counterpartyName: true, externalOrderId: true },
    });
    if (!order) throw new Error(`Order ${orderId} not found`);

    // Split counterparty name
    const nameParts = (order.counterpartyName || '').split(' ');
    const firstName = nameParts[0];
    const lastName = nameParts.slice(1).join(' ');

    return diditService.createSession({
      vendorData: `order:${order.externalOrderId || orderId}`,
      email,
      firstName,
      lastName,
      metadata: {
        binance_order_id: order.externalOrderId || orderId,
        counterparty_name: order.counterpartyName || '',
      },
    });
  }

  /**
   * Create a session specifically for a user (without an order context).
   */
  async createSessionForUser(userId: string, email?: string): Promise<CreateSessionResult> {
    const user = await prisma.user.findUnique({
      where: { id: userId },
      select: { displayName: true, legalName: true, externalId: true },
    });
    if (!user) throw new Error(`User ${userId} not found`);

    const nameParts = (user.legalName || user.displayName || '').split(' ');
    const firstName = nameParts[0];
    const lastName = nameParts.slice(1).join(' ');

    return diditService.createSession({
      vendorData: `user:${user.externalId || userId}`,
      email: email || undefined,
      firstName,
      lastName,
      metadata: {
        user_id: userId,
        binance_uid: user.externalId || '',
      },
    });
  }
}

export const kycSessionCreator = new KycSessionCreatorService();
