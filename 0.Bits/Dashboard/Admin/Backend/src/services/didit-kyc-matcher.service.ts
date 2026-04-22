import { prisma } from '../lib/db.js';
import { config } from '../config/index.js';
import { createLogger } from '../lib/logger.js';
import { KYCStatus } from '@prisma/client';

const log = createLogger('didit-kyc-matcher');

/**
 * Normalize a name for fuzzy matching:
 * - Uppercase
 * - Strip accents/diacritics
 * - Sort tokens alphabetically (handles name order variations)
 */
function normalizeName(name: string): string {
  return name
    .toUpperCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '') // strip diacritics
    .replace(/[^A-Z\s]/g, '')        // keep only letters and spaces
    .trim()
    .split(/\s+/)
    .sort()
    .join(' ');
}

/**
 * Calculate token-set similarity between two names.
 * Returns a score from 0 to 1.
 */
function tokenSetSimilarity(a: string, b: string): number {
  const tokensA = new Set(a.split(/\s+/).filter(t => t.length > 1));
  const tokensB = new Set(b.split(/\s+/).filter(t => t.length > 1));
  
  if (tokensA.size === 0 || tokensB.size === 0) return 0;
  
  let matches = 0;
  for (const token of tokensA) {
    if (tokensB.has(token)) matches++;
  }
  
  // Jaccard-like similarity: intersection / union
  const union = new Set([...tokensA, ...tokensB]).size;
  return matches / union;
}

interface DiditSession {
  session_id: string;
  full_name: string;
  status: string;
  country?: string;
  document_type?: string;
  portrait_image?: string;
  created_at: string;
  features?: Array<{ feature: string; status: string }>;
  vendor_data?: string;
  phone_number?: { number: string; is_verified: boolean } | string;
  email_address?: { email: string; is_verified: boolean } | string;
}

interface MatchResult {
  userId: string;
  userName: string;
  diditName: string;
  sessionId: string;
  status: KYCStatus;
  similarity: number;
  country?: string;
}

export class DiditKycMatcherService {
  private baseUrl = 'https://verification.didit.me/v3';
  
  private get headers() {
    return {
      'x-api-key': config.DIDIT_API_KEY || '',
      'Accept': 'application/json',
    };
  }

  /**
   * Fetch all Didit verification sessions with pagination.
   */
  async fetchAllSessions(): Promise<DiditSession[]> {
    const allSessions: DiditSession[] = [];
    let offset = 0;
    const pageSize = 100;
    
    while (true) {
      const url = `${this.baseUrl}/sessions?page_size=${pageSize}&offset=${offset}&session_kind=user`;
      log.info(`[DiditMatcher] Fetching sessions offset=${offset}...`);
      
      const res = await fetch(url, { headers: this.headers });
      
      if (!res.ok) {
        const text = await res.text();
        log.error(`[DiditMatcher] API error ${res.status}: ${text}`);
        throw new Error(`Didit API error: ${res.status} - ${text}`);
      }
      
      const data: any = await res.json();
      const results = data.results || [];
      allSessions.push(...results);
      
      log.info(`[DiditMatcher] Fetched ${results.length} sessions (total: ${allSessions.length}/${data.count})`);
      
      if (!data.next || results.length === 0) break;
      offset += pageSize;
    }
    
    return allSessions;
  }

  /**
   * Match Didit sessions against DB users by name.
   * Returns all matches found.
   */
  async matchSessions(sessions: DiditSession[]): Promise<MatchResult[]> {
    // Load all users with legal names
    const users = await prisma.user.findMany({
      where: { legalName: { not: null } },
      select: { id: true, legalName: true, displayName: true, kycStatus: true },
    });
    
    log.info(`[DiditMatcher] Matching ${sessions.length} Didit sessions against ${users.length} DB users...`);
    
    // Build normalized name → user map
    const userMap = new Map<string, typeof users[0]>();
    const userNormNames = new Map<string, string>();
    
    for (const user of users) {
      if (!user.legalName) continue;
      const norm = normalizeName(user.legalName);
      userMap.set(norm, user);
      userNormNames.set(user.id, norm);
    }
    
    const matches: MatchResult[] = [];
    const matchedUserIds = new Set<string>();
    
    for (const session of sessions) {
      if (!session.full_name) continue;
      
      const sessionNorm = normalizeName(session.full_name);
      const mapStatus = this.mapStatus(session.status);
      
      // 1. Exact normalized match (fastest path)
      const exactMatch = userMap.get(sessionNorm);
      if (exactMatch && !matchedUserIds.has(exactMatch.id)) {
        matches.push({
          userId: exactMatch.id,
          userName: exactMatch.legalName!,
          diditName: session.full_name,
          sessionId: session.session_id,
          status: mapStatus,
          similarity: 1.0,
          country: session.country,
        });
        matchedUserIds.add(exactMatch.id);
        continue;
      }
      
      // 2. Token-set fuzzy match (handles partial name differences)
      let bestMatch: typeof users[0] | null = null;
      let bestSim = 0;
      
      for (const user of users) {
        if (matchedUserIds.has(user.id)) continue;
        const userNorm = userNormNames.get(user.id);
        if (!userNorm) continue;
        
        const sim = tokenSetSimilarity(sessionNorm, userNorm);
        if (sim > bestSim && sim >= 0.85) {
          bestSim = sim;
          bestMatch = user;
        }
      }
      
      if (bestMatch) {
        matches.push({
          userId: bestMatch.id,
          userName: bestMatch.legalName!,
          diditName: session.full_name,
          sessionId: session.session_id,
          status: mapStatus,
          similarity: bestSim,
          country: session.country,
        });
        matchedUserIds.add(bestMatch.id);
      }
    }
    
    return matches;
  }

  /**
   * Apply matches to the database — update kycStatus and country.
   */
  async applyMatches(matches: MatchResult[]): Promise<number> {
    let updated = 0;
    
    for (const match of matches) {
      await prisma.user.update({
        where: { id: match.userId },
        data: {
          kycStatus: match.status,
          country: match.country || undefined,
          metadata: {
            diditSessionId: match.sessionId,
            diditFullName: match.diditName,
            diditMatchSimilarity: match.similarity,
            diditMatchedAt: new Date().toISOString(),
          },
        },
      });
      updated++;
    }
    
    return updated;
  }

  /**
   * Run the full matching pipeline: fetch → match → apply.
   */
  async runFullMatch(): Promise<{
    totalSessions: number;
    totalUsers: number;
    matched: number;
    approved: number;
    declined: number;
    results: MatchResult[];
  }> {
    log.info('[DiditMatcher] Starting full KYC matching pipeline...');
    
    // Step 1: Fetch all Didit sessions
    const sessions = await this.fetchAllSessions();
    log.info(`[DiditMatcher] Fetched ${sessions.length} total Didit sessions.`);
    
    // Step 2: Match against DB users
    const matches = await this.matchSessions(sessions);
    log.info(`[DiditMatcher] Found ${matches.length} matches.`);
    
    // Step 3: Apply to DB
    const updated = await this.applyMatches(matches);
    
    const approved = matches.filter(m => m.status === KYCStatus.APPROVED).length;
    const declined = matches.filter(m => m.status === KYCStatus.REJECTED).length;
    
    const totalUsers = await prisma.user.count({ where: { legalName: { not: null } } });
    
    log.info(`[DiditMatcher] DONE: ${updated} users updated (${approved} approved, ${declined} declined)`);
    
    return {
      totalSessions: sessions.length,
      totalUsers,
      matched: matches.length,
      approved,
      declined,
      results: matches,
    };
  }

  private mapStatus(diditStatus: string): KYCStatus {
    const s = diditStatus.toUpperCase();
    if (s === 'APPROVED') return KYCStatus.APPROVED;
    if (s === 'DECLINED' || s === 'REJECTED') return KYCStatus.REJECTED;
    if (s === 'IN_REVIEW' || s === 'IN REVIEW') return KYCStatus.IN_REVIEW;
    if (s === 'PENDING' || s === 'IN_PROGRESS' || s === 'IN PROGRESS') return KYCStatus.PENDING;
    if (s === 'EXPIRED') return KYCStatus.EXPIRED;
    return KYCStatus.PENDING;
  }
}

export const diditKycMatcher = new DiditKycMatcherService();
