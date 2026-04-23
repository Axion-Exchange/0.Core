import { prisma } from '../lib/db.js';
import { createLogger } from '../lib/logger.js';
import { decrypt } from '../lib/crypto.js';

const log = createLogger('didit-service');

export interface CreateSessionResult {
  sessionId: string;
  sessionUrl: string;
  status: string;
}

export class DiditService {
  /**
   * Retrieves the active DIDIT provider credentials from the database.
   */
  async getProvider() {
    const provider = await prisma.kycProvider.findFirst({
      where: { isActive: true, provider: 'DIDIT' },
      orderBy: { createdAt: 'desc' },
    });
    return provider;
  }

  /**
   * Creates a new KYC session for a user or order.
   */
  async createSession(params: {
    vendorData: string;
    email?: string;
    firstName?: string;
    lastName?: string;
    metadata?: Record<string, string>;
  }): Promise<CreateSessionResult> {
    const provider = await this.getProvider();

    if (!provider) {
      log.warn(`[DiditService] No active DIDIT provider found. Falling back to mock session.`);
      const mockId = `mock-${Date.now()}`;
      return {
        sessionId: mockId,
        sessionUrl: `https://verify.didit.me/mock-session/${mockId}`,
        status: 'NOT_STARTED',
      };
    }

    try {
      const apiKey = decrypt(provider.apiKey);
      const url = `${provider.baseUrl.replace(/\/$/, '')}/session/`;

      const payload = {
        vendor_data: params.vendorData,
        callback: "https://api.0bit.app/v1/webhooks/didit", // Standardize callback if needed
        features: {
          session_timeout: 3600,
        }
      };

      const res = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': apiKey,
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errText = await res.text();
        throw new Error(`Didit API error: ${res.status} ${errText}`);
      }

      const data: any = await res.json();
      return {
        sessionId: data.session_id,
        sessionUrl: data.url,
        status: data.status || 'NOT_STARTED',
      };
    } catch (err: any) {
      log.error(`[DiditService] Failed to create session: ${err.message}`);
      throw err;
    }
  }

  /**
   * Retrieves the full decision details of a specific session.
   */
  async getSessionDecision(sessionId: string): Promise<any> {
    const provider = await this.getProvider();
    if (!provider) {
      return { status: "MOCK", mock: true, note: "No active provider. Returning mock decision." };
    }

    try {
      const apiKey = decrypt(provider.apiKey);
      const url = `${provider.baseUrl.replace(/\/$/, '')}/session/${sessionId}/decision/`;

      const res = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': apiKey,
        },
      });

      if (!res.ok) {
        if (res.status === 404) return null;
        const errText = await res.text();
        throw new Error(`Didit API error: ${res.status} ${errText}`);
      }

      return await res.json();
    } catch (err: any) {
      log.error(`[DiditService] Failed to get session decision for ${sessionId}: ${err.message}`);
      throw err;
    }
  }

  /**
   * Attempts to download the PDF report for a session.
   * If the endpoint fails (e.g. not supported by tier), returns the raw JSON decision as a string.
   */
  async downloadSessionReport(sessionId: string): Promise<{ type: 'pdf' | 'json', data: Buffer | string }> {
    const provider = await this.getProvider();
    if (!provider) {
      return { type: 'json', data: JSON.stringify({ mock: true, sessionId, status: "APPROVED" }, null, 2) };
    }

    try {
      const apiKey = decrypt(provider.apiKey);
      // Attempting PDF endpoint as per standard API structures
      const pdfUrl = `${provider.baseUrl.replace(/\/$/, '')}/session/${sessionId}/pdf/`;
      
      const res = await fetch(pdfUrl, {
        method: 'GET',
        headers: {
          'x-api-key': apiKey,
        },
      });

      if (res.ok) {
        const arrayBuffer = await res.arrayBuffer();
        return { type: 'pdf', data: Buffer.from(arrayBuffer) };
      }

      // Fallback to JSON Decision if PDF endpoint fails or returns 404
      const decision = await this.getSessionDecision(sessionId);
      return { type: 'json', data: JSON.stringify(decision, null, 2) };
    } catch (err: any) {
      log.error(`[DiditService] Failed to download report for ${sessionId}, falling back to decision JSON: ${err.message}`);
      const decision = await this.getSessionDecision(sessionId);
      return { type: 'json', data: JSON.stringify(decision, null, 2) };
    }
  }
}

export const diditService = new DiditService();
