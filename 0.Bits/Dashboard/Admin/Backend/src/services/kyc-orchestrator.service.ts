import { prisma } from '../lib/db.js';
import { createLogger } from '../lib/logger.js';
import { KYCStatus } from '@prisma/client';
import { diditService } from './didit.service.js';

const log = createLogger('kyc-orchestrator');

// ══════════════════════════════════════════════════════════════════════════════
// PearV2 Name Matching Engine (ported from Python)
// - Cyrillic → Latin transliteration
// - Diacritical accent stripping
// - Levenshtein distance per word (tiered tolerance)
// - Reverse subset matching (shorter name in longer)
// - Supermajority rule (3+ words: all-but-one match = same person)
// ══════════════════════════════════════════════════════════════════════════════

const CYRILLIC_TO_LATIN: Record<string, string> = {
  'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'H', 'Ґ': 'G',
  'Д': 'D', 'Е': 'E', 'Є': 'Ye', 'Ж': 'Zh', 'З': 'Z',
  'И': 'Y', 'І': 'I', 'Ї': 'Yi', 'Й': 'Y', 'К': 'K',
  'Л': 'L', 'М': 'M', 'Н': 'N', 'О': 'O', 'П': 'P',
  'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U', 'Ф': 'F',
  'Х': 'Kh', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Shch',
  'Ь': '', 'Ю': 'Yu', 'Я': 'Ya',
  'Ё': 'Yo', 'Ы': 'Y', 'Э': 'E', 'Ъ': '',
  'а': 'a', 'б': 'b', 'в': 'v', 'г': 'h', 'ґ': 'g',
  'д': 'd', 'е': 'e', 'є': 'ye', 'ж': 'zh', 'з': 'z',
  'и': 'y', 'і': 'i', 'ї': 'yi', 'й': 'y', 'к': 'k',
  'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p',
  'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f',
  'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
  'ь': '', 'ю': 'yu', 'я': 'ya',
  'ё': 'yo', 'ы': 'y', 'э': 'e', 'ъ': '',
};

function transliterateCyrillic(text: string): string {
  let result = '';
  for (const char of text) {
    const mapped = CYRILLIC_TO_LATIN[char];
    if (mapped !== undefined) {
      result += char === char.toUpperCase() && mapped.length > 1 ? mapped.toUpperCase() : mapped;
    } else {
      result += char;
    }
  }
  return result;
}

function stripAccents(text: string): string {
  return text.normalize('NFKD').replace(/[\u0300-\u036f]/g, '');
}

/**
 * PearV2 normalize-and-split pipeline:
 * 1. Transliterate Cyrillic → Latin
 * 2. Strip diacritical accents
 * 3. Lowercase
 * 4. Strip non-alphanumeric (keep periods for initials)
 * 5. Split on whitespace
 * 6. Expand dotted initials (F.A. → [f, a])
 */
function normalizeAndSplit(name: string): string[] {
  let normalized = transliterateCyrillic(name);
  normalized = stripAccents(normalized);
  normalized = normalized.toLowerCase().trim();
  normalized = normalized.replace(/[^a-z0-9\s.]/g, '');

  const rawWords = normalized.split(/\s+/).filter(w => w.length > 0);

  const expanded: string[] = [];
  for (const w of rawWords) {
    const initials = w.match(/([a-z])\./g);
    if (initials && w.length <= initials.length * 2 + 1) {
      for (const init of initials) expanded.push(init[0]!);
    } else {
      const clean = w.replace(/\.+$/, '');
      if (clean) expanded.push(clean);
    }
  }
  return expanded;
}

/** Levenshtein distance between two strings. */
function levenshtein(s1: string, s2: string): number {
  if (s1.length < s2.length) return levenshtein(s2, s1);
  if (s2.length === 0) return s1.length;
  let prev = Array.from({ length: s2.length + 1 }, (_, i) => i);
  for (let i = 0; i < s1.length; i++) {
    const curr = [i + 1];
    for (let j = 0; j < s2.length; j++) {
      curr.push(Math.min(
        prev[j + 1]! + 1,
        curr[j]! + 1,
        prev[j]! + (s1[i] !== s2[j] ? 1 : 0),
      ));
    }
    prev = curr;
  }
  return prev[s2.length]!;
}

/**
 * PearV2 word matching with tiered Levenshtein tolerance:
 * - 1-4 chars: max 1 edit
 * - 5+ chars: max 2 edits (handles maria/mariana, jorge/george, alexander/aleksander)
 * - Single-letter initials match first letter of words
 */
function wordsMatch(w1: string, w2: string): boolean {
  if (w1 === w2) return true;
  const dist = levenshtein(w1, w2);
  if (dist <= 1) return true;
  // Initial abbreviation — disabled for KYC matching (too many false positives)
  // Only match if BOTH are single letters
  // if (w1.length === 1 && w2.length > 1 && w1[0] === w2[0]) return true;
  // if (w2.length === 1 && w1.length > 1 && w2[0] === w1[0]) return true;
  // Length-proportional: words ≥5 chars allow distance 2
  if (Math.min(w1.length, w2.length) >= 5 && dist <= 2) return true;
  return false;
}

interface NameMatchResult {
  matched: boolean;
  confidence: number;
  method: string;
  details: string;
}

/**
 * PearV2 hardcoded fuzzy name matching engine.
 * Handles name order, spelling variations, truncation, and Cyrillic.
 */
function pearV2Match(nameA: string, nameB: string): NameMatchResult {
  const wordsA = normalizeAndSplit(nameA);
  const wordsB = normalizeAndSplit(nameB);

  if (wordsA.length === 0 || wordsB.length === 0) {
    return { matched: false, confidence: 0, method: 'empty', details: 'Empty name(s)' };
  }

  // ── FORWARD CHECK: All words from A must appear in B ──
  let matchedForward = 0;
  const unmatchedA: string[] = [];
  for (const wa of wordsA) {
    let found = false;
    for (const wb of wordsB) {
      if (wordsMatch(wa, wb)) { found = true; break; }
    }
    if (found) matchedForward++;
    else unmatchedA.push(wa);
  }

  if (matchedForward === wordsA.length && matchedForward >= 2) {
    return { matched: true, confidence: 1.0, method: 'forward', details: `All ${matchedForward} words matched` };
  }

  // ── REVERSE CHECK: All B words found in A (for shortened names) ──
  let matchedReverse = 0;
  for (const wb of wordsB) {
    for (const wa of wordsA) {
      if (wordsMatch(wa, wb)) { matchedReverse++; break; }
    }
  }

  if (wordsB.length >= 2 && matchedReverse === wordsB.length) {
    return { matched: true, confidence: 0.95, method: 'reverse_subset', details: `All ${wordsB.length} shorter-name words found in longer name` };
  }

  // ── SUPERMAJORITY: 4+ words, all-but-one match, at least 3 words matched ──
  // (Requires minimum 3 genuinely matched words to avoid false positives on short names)
  if (wordsA.length >= 5 && matchedForward >= wordsA.length - 1 && matchedForward >= 4) {
    return { matched: true, confidence: 0.90, method: 'supermajority', details: `${matchedForward}/${wordsA.length} words matched (missing: ${unmatchedA.join(', ')})` };
  }

  // Also check supermajority in reverse direction
  if (wordsB.length >= 5 && matchedReverse >= wordsB.length - 1 && matchedReverse >= 4) {
    return { matched: true, confidence: 0.90, method: 'supermajority_reverse', details: `${matchedReverse}/${wordsB.length} reverse words matched` };
  }

  return { matched: false, confidence: matchedForward / wordsA.length, method: 'no_match', details: `Missing: ${unmatchedA.join(', ')}` };
}

/** Normalize name for DB storage (sorted tokens for exact index lookups) */
function normalizeName(name: string): string {
  return normalizeAndSplit(name).sort().join(' ');
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
    return providers.map((p: any) => ({
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
      providers.map(async (prov: any) => {
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
      if (!sess.fullName) continue;

      // 1. Exact token-sorted match (fast path)
      let userId = sess.normalizedName ? normToUser.get(sess.normalizedName) : undefined;
      let similarity = userId ? 1.0 : 0;
      let matchMethod = userId ? 'exact_norm' : '';

      // 2. pg_trgm database-tier fuzzy search (sub-millisecond via GIN index)
      // Doc ref: §Offloading Fuzzy Search to the Data Tier (citations 21, 23, 24)
      // "Postgres extensions like pg_trgm allow for typo-tolerant fuzzy matching at sub-millisecond speeds"
      if (!userId) {
        try {
          const trgmResults: any[] = await prisma.$queryRawUnsafe(`
            SELECT id, "legalName", similarity("legalName", $1) AS sim
            FROM users
            WHERE "legalName" IS NOT NULL AND "legalName" % $1
            ORDER BY sim DESC
            LIMIT 3
          `, sess.fullName);

          if (trgmResults.length > 0) {
            const best = trgmResults[0];
            const sim = Number(best.sim);
            // Only accept if similarity > 0.3 and user not already matched
            if (sim > 0.3 && !matchedUserIds.has(best.id)) {
              userId = best.id;
              similarity = sim;
              matchMethod = 'pg_trgm';
            }
          }
        } catch (trgmErr: any) {
          // pg_trgm not available or query failed — fall through to TypeScript matcher
          log.warn(`[Orchestrator] pg_trgm query failed, falling back to Levenshtein: ${trgmErr.message}`);
        }
      }

      // 3. PearV2 fuzzy match FALLBACK (handles Cyrillic transliteration edge cases)
      // This catches cases where pg_trgm misses due to script differences
      if (!userId) {
        let bestConf = 0;
        for (const [uid, data] of userNorms) {
          if (matchedUserIds.has(uid)) continue;
          const result = pearV2Match(sess.fullName, data.legalName);
          if (result.matched && result.confidence > bestConf) {
            bestConf = result.confidence;
            userId = uid;
            similarity = result.confidence;
            matchMethod = result.method;
          }
        }
      }

      if (userId && !matchedUserIds.has(userId)) {
        matchedUserIds.add(userId);

        let finalStatus = sess.status;
        let email: string | undefined;
        try {
          const fullDecision = await diditService.getSessionDecision(sess.externalId);
          if (fullDecision && fullDecision.status) {
            finalStatus = fullDecision.status;
          }
          const raw = fullDecision.raw || fullDecision;
          if (raw.email_address) {
            email = typeof raw.email_address === 'string' ? raw.email_address : raw.email_address.email;
          }
          if (!email) {
             const str = JSON.stringify(raw);
             const match = str.match(/"email"\s*:\s*"([^"]+)"/);
             if (match) email = match[1];
          }
        } catch (e) {
          console.warn('[Orchestrator] Failed to fetch full decision for email:', e);
        }

        const kycStatus = this.mapStatus(finalStatus);

        // Update session with match and corrected status
        await prisma.kycSession.update({
          where: { id: sess.id },
          data: { matchedUserId: userId, matchSimilarity: similarity, status: finalStatus },
        });

        // Update user kycStatus and email
        const updateData: any = {
          kycStatus,
          country: sess.country || undefined,
          metadata: {
            kycProvider: sess.provider.provider,
            kycAppName: sess.provider.name,
            kycSessionId: sess.externalId,
            kycMatchSimilarity: similarity,
            kycMatchedAt: new Date().toISOString(),
          },
        };
        if (email) updateData.email = email;

        await prisma.user.update({
          where: { id: userId },
          data: updateData,
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
          matchMethod,
          country: sess.country,
        });
      }
    }

    log.info(`[Orchestrator] Matched ${matched} users (${approved} approved, ${declined} declined)`);
    return { matched, approved, declined, details };
  }

  /**
   * Propagate Didit status changes to already-matched users.
   * Catches: manual approvals, expirations, declines done on Didit console.
   */
  async propagateStatusChanges(): Promise<{ updated: number; changes: { user: string; from: string; to: string }[] }> {
    const matched = await prisma.kycSession.findMany({
      where: { matchedUserId: { not: null } },
      include: { matchedUser: { select: { id: true, legalName: true, kycStatus: true } } },
    });

    let updated = 0;
    const changes: { user: string; from: string; to: string }[] = [];

    for (const sess of matched) {
      if (!sess.matchedUser) continue;
      let sessionStatus = sess.status;
      if (sess.rawPayload && typeof sess.rawPayload === 'object' && (sess.rawPayload as any).status) {
        sessionStatus = (sess.rawPayload as any).status;
      }
      
      const newStatus = this.mapStatus(sessionStatus);
      const currentStatus = sess.matchedUser.kycStatus;

      // Only propagate if status actually changed
      if (newStatus !== currentStatus) {
        // Double check using the decision endpoint if going from APPROVED back to PENDING/IN_REVIEW
        let finalStatus = newStatus;
        if (currentStatus === 'APPROVED' && (newStatus === 'PENDING' || newStatus === 'IN_REVIEW')) {
            try {
              const decision = await diditService.getSessionDecision(sess.externalId);
              if (decision && decision.status) {
                 finalStatus = this.mapStatus(decision.status);
              }
            } catch (e) {
              log.warn(`[Orchestrator] Failed to fetch decision for status check:`, e);
            }
        }
        
        if (finalStatus !== currentStatus) {
          await prisma.user.update({
            where: { id: sess.matchedUser.id },
            data: { kycStatus: finalStatus },
          });
          updated++;
          changes.push({
            user: sess.matchedUser.legalName || sess.matchedUser.id,
            from: currentStatus,
            to: finalStatus,
          });
          log.info(`[Orchestrator] Status change: ${sess.matchedUser.legalName} ${currentStatus} → ${finalStatus}`);
        }
      }
    }

    if (updated > 0) {
      log.info(`[Orchestrator] Propagated ${updated} status changes`);
    }
    return { updated, changes };
  }

  /**
   * Run full pipeline: sync all providers → match all sessions → propagate status changes.
   */
  async runFullPipeline() {
    log.info('[Orchestrator] ═══ Starting Full KYC Pipeline ═══');

    const syncResult = await this.syncAllProviders();
    const matchResult = await this.matchAllSessions();
    const statusResult = await this.propagateStatusChanges();

    // Count totals
    const totalSessions = await prisma.kycSession.count();
    const totalMatched = await prisma.kycSession.count({ where: { matchedUserId: { not: null } } });
    const totalUsers = await prisma.user.count({ where: { legalName: { not: null } } });
    const approvedUsers = await prisma.user.count({ where: { kycStatus: KYCStatus.APPROVED } });

    log.info('[Orchestrator] ═══ Pipeline Complete ═══');

    return {
      sync: syncResult,
      matching: matchResult,
      statusPropagation: statusResult,
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
      sessions: sessions.map((s: any) => ({
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

  mapStatus(s: string): KYCStatus {
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
