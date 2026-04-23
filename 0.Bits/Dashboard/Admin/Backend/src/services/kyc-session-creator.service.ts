import { prisma } from '../lib/db.js';
import { createLogger } from '../lib/logger.js';

const log = createLogger('kyc-session-creator');

/**
 * KYC Session Creator — Generates Didit verification sessions with vendor_data.
 * 
 * This is for FUTURE USE: when we generate KYC links from our backend
 * (instead of Didit console), we embed the Binance order ID or user ID
 * as vendor_data. This eliminates the need for chat email extraction.
 * 
 * Usage:
 *   const { sessionUrl } = await kycSessionCreator.createSession({
 *     providerId: 'uuid-of-0bit-provider',
 *     vendorData: 'order:22871255724370505728',
 *     email: 'user@example.com',
 *     callbackUrl: 'https://api.0bit.app/api/v1/kyc/webhook',
 *   });
 *   // Send sessionUrl to the counterparty in Binance chat
 */

interface CreateSessionInput {
  providerId: string;
  vendorData?: string;       // Our internal reference (order ID, user ID, etc.)
  email?: string;            // Pre-fill email for the verifier
  firstName?: string;        // Pre-fill expected first name
  lastName?: string;         // Pre-fill expected last name
  callbackUrl?: string;      // Webhook callback URL
  metadata?: Record<string, string>; // Extra metadata passed to Didit
}

interface CreateSessionResult {
  sessionId: string;
  sessionUrl: string;
  status: string;
}

export class KycSessionCreatorService {

  /**
   * Create a new Didit verification session via API.
   * The vendor_data field links this session back to our internal records.
   */
  async createSession(input: CreateSessionInput): Promise<CreateSessionResult> {
    const provider = await prisma.kycProvider.findUnique({
      where: { id: input.providerId },
    });
    if (!provider) throw new Error(`KYC Provider ${input.providerId} not found`);
    if (provider.provider !== 'DIDIT') throw new Error('Session creation only supported for DIDIT providers');

    const url = `${provider.baseUrl}/sessions/`;

    const body: Record<string, any> = {
      callback: input.callbackUrl || 'https://api.0bit.app/api/v1/kyc/webhook',
    };

    if (input.vendorData) body.vendor_data = input.vendorData;
    if (input.metadata) body.metadata = input.metadata;

    // Pre-fill expected details if provided
    if (input.firstName || input.lastName) {
      body.expected_details = {};
      if (input.firstName) body.expected_details.first_name = input.firstName;
      if (input.lastName) body.expected_details.last_name = input.lastName;
    }

    // Contact details for email notification
    if (input.email) {
      body.contact_details = {
        email: input.email,
        send_notification_emails: true,
      };
    }

    log.info(`[SessionCreator] Creating session on ${provider.name} with vendor_data=${input.vendorData || 'none'}`);

    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'x-api-key': provider.apiKey,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Didit session creation failed (${res.status}): ${text}`);
    }

    const data: any = await res.json();
    const sessionId = data.session_id;
    const sessionUrl = data.session_url || `https://verify.didit.me/session/${sessionId}`;

    // Store in our DB immediately
    await prisma.kycSession.create({
      data: {
        providerId: provider.id,
        externalId: sessionId,
        status: 'NOT_STARTED',
        rawPayload: data,
      },
    });

    log.info(`[SessionCreator] Created session ${sessionId} → ${sessionUrl}`);

    return {
      sessionId,
      sessionUrl,
      status: 'NOT_STARTED',
    };
  }

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

    // Use the first active provider
    const provider = await prisma.kycProvider.findFirst({
      where: { isActive: true, provider: 'DIDIT' },
      orderBy: { createdAt: 'desc' },
    });
    if (!provider) throw new Error('No active Didit provider found');

    // Split counterparty name
    const nameParts = (order.counterpartyName || '').split(' ');
    const firstName = nameParts[0];
    const lastName = nameParts.slice(1).join(' ');

    return this.createSession({
      providerId: provider.id,
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

    const provider = await prisma.kycProvider.findFirst({
      where: { isActive: true, provider: 'DIDIT' },
      orderBy: { createdAt: 'desc' },
    });
    if (!provider) throw new Error('No active Didit provider found');

    const nameParts = (user.legalName || user.displayName || '').split(' ');
    const firstName = nameParts[0];
    const lastName = nameParts.slice(1).join(' ');

    return this.createSession({
      providerId: provider.id,
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
