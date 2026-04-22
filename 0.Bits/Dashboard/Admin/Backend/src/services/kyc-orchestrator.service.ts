import { prisma } from '../lib/db.js';
import { createLogger } from '../lib/logger.js';
import { KYCStatus } from '@prisma/client';

const log = createLogger('kyc-orchestrator');

// ── Name Normalization ────────────────────────────────────────────────────────

function normalizeName(name: string): string {
  return name
    .toUpperCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^A-Z\s]/g, '')
    .trim()
    .split(/\s+/)
    .filter(t => t.length > 1)
    .sort()
    .join(' ');
}

function tokenSetSimilarity(a: string, b: string): number {
  const tokensA = new Set(a.split(/\s+/).filter(t => t.length > 1));
  const tokensB = new Set(b.split(/\s+/).filter(t => t.length > 1));
  if (tokensA.size === 0 || tokensB.size === 0) return 0;
  let matches = 0;
  for (const token of tokensA) {
    if (tokensB.has(token)) matches++;
  }
  return matches / new Set([...tokensA, ...tokensB]).size;
}

// ── Provider Adapters ─────────────────────────────────────────────────────────

interface ProviderSession {
  externalId: string;
  fullName: string | null;
  status: string;
  country?: string;
  documentType?: string;
  portraitUrl?: string;
  rawPayload: Record<string, any>;
}

/**
 * Fetch sessions from a Didit app using its API key.
 */
async function fetchDiditSessions(baseUrl: string, apiKey: string): Promise<ProviderSession[]> {
  const all: ProviderSession[] = [];
  let offset = 0;
  const pageSize = 100;

  while (true) {
    const url = `${baseUrl}/sessions?page_size=${pageSize}&offset=${offset}&session_kind=user`;
    const res = await fetch(url, {
      headers: { 'x-api-key': apiKey, 'Accept': 'application/json' },
    });

    if (!res.ok) {
      const text = await res.text();
      log.error(`Didit API ${res.status}: ${text}`);
      break;
    }

    const data: any = await res.json();
    const results = data.results || [];

    for (const s of results) {
      all.push({
        externalId: s.session_id,
        fullName: s.full_name || null,
        status: (s.status || 'UNKNOWN').toUpperCase(),
        country: s.country || undefined,
        documentType: s.document_type || undefined,
        portraitUrl: s.portrait_image || undefined,
        rawPayload: s,
      });
    }

    if (!data.next || results.length === 0) break;
    offset += pageSize;
  }

  return all;
}

// ── Orchestrator ──────────────────────────────────────────────────────────────

export class KycOrchestratorService {

  /**
   * Register a new KYC provider/app.
   */
  async addProvider(input: {
    name: string;
    provider: string;
    appId: string;
    apiKey: string;
    baseUrl?: string;
  }) {
    const existing = await prisma.kycProvider.findUnique({
      where: { provider_appId: { provider: input.provider.toUpperCase(), appId: input.appId } },
    });
    if (existing) {
      return prisma.kycProvider.update({
        where: { id: existing.id },
        data: {
          name: input.name,
          apiKey: input.apiKey,
          baseUrl: input.baseUrl || existing.baseUrl,
          isActive: true,
        },
      });
    }
    return prisma.kycProvider.create({
      data: {
        name: input.name,
        provider: input.provider.toUpperCase(),
        appId: input.appId,
        apiKey: input.apiKey,
        baseUrl: input.baseUrl || 'https://verification.didit.me/v3',
      },
    });
  }

  /**
   * List all registered providers with session counts.
   */
  async listProviders() {
    const providers = await prisma.kycProvider.findMany({
      include: { _count: { select: { sessions: true } } },
      orderBy: { createdAt: 'asc' },
    });
    return providers.map(p => ({
      id: p.id,
      name: p.name,
      provider: p.provider,
      appId: p.appId,
      baseUrl: p.baseUrl,
      isActive: p.isActive,
      sessionCount: p._count.sessions,
      createdAt: p.createdAt.toISOString(),
    }));
  }

  /**
   * Sync sessions from ALL active providers into the kyc_sessions table.
   */
  async syncAllProviders(): Promise<{ providersSynced: number; sessionsIngested: number }> {
    const providers = await prisma.kycProvider.findMany({ where: { isActive: true } });
    log.info(`[Orchestrator] Syncing ${providers.length} active providers...`);

    let totalIngested = 0;

    // Fetch from all providers concurrently
    const results = await Promise.allSettled(
      providers.map(async (prov) => {
        let sessions: ProviderSession[] = [];

        if (prov.provider === 'DIDIT') {
          sessions = await fetchDiditSessions(prov.baseUrl, prov.apiKey);
        }
        // Future: else if (prov.provider === 'SUMSUB') { ... }

        log.info(`[Orchestrator] ${prov.name}: ${sessions.length} sessions`);

        // Upsert into kyc_sessions
        let ingested = 0;
        for (const sess of sessions) {
          await prisma.kycSession.upsert({
            where: {
              providerId_externalId: { providerId: prov.id, externalId: sess.externalId },
            },
            create: {
              providerId: prov.id,
              externalId: sess.externalId,
              fullName: sess.fullName,
              normalizedName: sess.fullName ? normalizeName(sess.fullName) : null,
              country: sess.country,
              documentType: sess.documentType,
              status: sess.status,
              portraitUrl: sess.portraitUrl,
              rawPayload: sess.rawPayload,
            },
            update: {
              fullName: sess.fullName,
              normalizedName: sess.fullName ? normalizeName(sess.fullName) : null,
              country: sess.country,
              status: sess.status,
              portraitUrl: sess.portraitUrl,
              rawPayload: sess.rawPayload,
            },
          });
          ingested++;
        }

        return { provider: prov.name, count: ingested };
      })
    );

    for (const r of results) {
      if (r.status === 'fulfilled') totalIngested += r.value.count;
      else log.error(`[Orchestrator] Provider sync failed:`, r.reason);
    }

    log.info(`[Orchestrator] Sync complete: ${totalIngested} sessions from ${providers.length} providers`);
    return { providersSynced: providers.length, sessionsIngested: totalIngested };
  }

  /**
   * Match all unmatched sessions against DB users using fuzzy name matching.
   */
  async matchAllSessions(): Promise<{ matched: number; approved: number; declined: number; details: any[] }> {
    // Get all unmatched sessions with names
    const sessions = await prisma.kycSession.findMany({
      where: { matchedUserId: null, fullName: { not: null } },
      include: { provider: { select: { name: true, provider: true } } },
    });

    // Get all users with legal names
    const users = await prisma.user.findMany({
      where: { legalName: { not: null } },
      select: { id: true, legalName: true, displayName: true },
    });

    log.info(`[Orchestrator] Matching ${sessions.length} unmatched sessions against ${users.length} users...`);

    // Build normalized name map
    const userNorms = new Map<string, { id: string; legalName: string; norm: string }>();
    const normToUser = new Map<string, string>();
    for (const u of users) {
      if (!u.legalName) continue;
      const n = normalizeName(u.legalName);
      userNorms.set(u.id, { id: u.id, legalName: u.legalName, norm: n });
      normToUser.set(n, u.id);
    }

    const details: any[] = [];
    const matchedUserIds = new Set<string>();
    let matched = 0;
    let approved = 0;
    let declined = 0;

    for (const sess of sessions) {
      if (!sess.normalizedName) continue;

      // 1. Exact token-sorted match
      let userId = normToUser.get(sess.normalizedName);
      let similarity = userId ? 1.0 : 0;

      // 2. Fuzzy fallback
      if (!userId) {
        let bestSim = 0;
        for (const [uid, data] of userNorms) {
          if (matchedUserIds.has(uid)) continue;
          const sim = tokenSetSimilarity(sess.normalizedName, data.norm);
          if (sim > bestSim && sim >= 0.85) {
            bestSim = sim;
            userId = uid;
            similarity = sim;
          }
        }
      }

      if (userId && !matchedUserIds.has(userId)) {
        matchedUserIds.add(userId);
        const kycStatus = this.mapStatus(sess.status);

        // Update session with match
        await prisma.kycSession.update({
          where: { id: sess.id },
          data: { matchedUserId: userId, matchSimilarity: similarity },
        });

        // Update user kycStatus
        await prisma.user.update({
          where: { id: userId },
          data: {
            kycStatus,
            country: sess.country || undefined,
            metadata: {
              kycProvider: sess.provider.provider,
              kycAppName: sess.provider.name,
              kycSessionId: sess.externalId,
              kycMatchSimilarity: similarity,
              kycMatchedAt: new Date().toISOString(),
            },
          },
        });

        matched++;
        if (kycStatus === KYCStatus.APPROVED) approved++;
        if (kycStatus === KYCStatus.REJECTED) declined++;

        const userData = userNorms.get(userId);
        details.push({
          userName: userData?.legalName || '?',
          diditName: sess.fullName,
          provider: sess.provider.name,
          status: kycStatus,
          similarity: Math.round(similarity * 100),
          country: sess.country,
        });
      }
    }

    log.info(`[Orchestrator] Matched ${matched} users (${approved} approved, ${declined} declined)`);
    return { matched, approved, declined, details };
  }

  /**
   * Run full pipeline: sync all providers → match all sessions → return unified results.
   */
  async runFullPipeline() {
    log.info('[Orchestrator] ═══ Starting Full KYC Pipeline ═══');

    const syncResult = await this.syncAllProviders();
    const matchResult = await this.matchAllSessions();

    // Count totals
    const totalSessions = await prisma.kycSession.count();
    const totalMatched = await prisma.kycSession.count({ where: { matchedUserId: { not: null } } });
    const totalUsers = await prisma.user.count({ where: { legalName: { not: null } } });
    const approvedUsers = await prisma.user.count({ where: { kycStatus: KYCStatus.APPROVED } });

    log.info('[Orchestrator] ═══ Pipeline Complete ═══');

    return {
      sync: syncResult,
      matching: matchResult,
      totals: {
        sessions: totalSessions,
        matchedSessions: totalMatched,
        users: totalUsers,
        approvedUsers,
      },
    };
  }

  /**
   * Get unified KYC status for a user across all providers.
   * Priority: APPROVED > IN_REVIEW > REJECTED > EXPIRED > NOT_STARTED
   */
  async getUnifiedStatus(userId: string) {
    const sessions = await prisma.kycSession.findMany({
      where: { matchedUserId: userId },
      include: { provider: { select: { name: true, provider: true } } },
      orderBy: { createdAt: 'desc' },
    });

    if (sessions.length === 0) return { status: 'NOT_STARTED', sessions: [] };

    // Priority-based status resolution
    const statusPriority: Record<string, number> = {
      APPROVED: 5,
      IN_REVIEW: 4,
      'IN REVIEW': 4,
      PENDING: 3,
      DECLINED: 2,
      REJECTED: 2,
      EXPIRED: 1,
      ABANDONED: 0,
    };

    let bestStatus = 'NOT_STARTED';
    let bestPriority = -1;

    for (const s of sessions) {
      const p = statusPriority[s.status] ?? 0;
      if (p > bestPriority) {
        bestPriority = p;
        bestStatus = s.status;
      }
    }

    return {
      status: bestStatus,
      sessions: sessions.map(s => ({
        provider: s.provider.name,
        providerType: s.provider.provider,
        sessionId: s.externalId,
        fullName: s.fullName,
        country: s.country,
        status: s.status,
        documentType: s.documentType,
        similarity: s.matchSimilarity,
        createdAt: s.createdAt.toISOString(),
      })),
    };
  }

  /**
   * List all KYC sessions across all providers.
   */
  async listSessions(filters?: { status?: string; matched?: boolean }) {
    const where: any = {};
    if (filters?.status) where.status = filters.status;
    if (filters?.matched === true) where.matchedUserId = { not: null };
    if (filters?.matched === false) where.matchedUserId = null;

    return prisma.kycSession.findMany({
      where,
      include: {
        provider: { select: { name: true, provider: true } },
        matchedUser: { select: { id: true, displayName: true, legalName: true } },
      },
      orderBy: { createdAt: 'desc' },
    });
  }

  private mapStatus(s: string): KYCStatus {
    const upper = s.toUpperCase();
    if (upper === 'APPROVED') return KYCStatus.APPROVED;
    if (upper === 'DECLINED' || upper === 'REJECTED') return KYCStatus.REJECTED;
    if (upper === 'IN_REVIEW' || upper === 'IN REVIEW') return KYCStatus.IN_REVIEW;
    if (upper === 'PENDING' || upper === 'IN_PROGRESS' || upper === 'IN PROGRESS') return KYCStatus.PENDING;
    if (upper === 'EXPIRED') return KYCStatus.EXPIRED;
    return KYCStatus.PENDING;
  }
}

export const kycOrchestrator = new KycOrchestratorService();
