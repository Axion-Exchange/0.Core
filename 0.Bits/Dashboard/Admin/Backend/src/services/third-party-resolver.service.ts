import { prisma } from '../lib/db.js';
import { createLogger } from '../lib/logger.js';

const log = createLogger('third-party-resolver');

// ── Email & Link Extraction ───────────────────────────────────────────────────

const EMAIL_REGEX = /\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b/g;
const DIDIT_LINK_REGEX = /verify\.didit\.me\/session\/([A-Za-z0-9]+)/g;

interface ChatExtraction {
  orderId: string;
  externalOrderId: string | null;
  counterpartyName: string | null;
  amount: string;
  fiat: string;
  emails: string[];
  diditLinks: string[];
}

interface ThirdPartyCandidate {
  orderId: string;
  externalOrderId: string | null;
  binanceName: string;
  kycName: string;
  kycEmail: string | null;
  kycCountry: string | null;
  kycStatus: string;
  kycSessionId: string;
  kycProvider: string;
  orderAmount: string;
  orderFiat: string;
  matchType: 'SAME_PERSON' | 'THIRD_PARTY';
  januarMatch: boolean;
  januarSenderName: string | null;
  januarAmount: string | null;
  confidence: number;
}

// ── PearV2 Name Matching (reused from orchestrator) ──────────────────────────

const CYRILLIC_TO_LATIN: Record<string, string> = {
  'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'H', 'Ґ': 'G',
  'Д': 'D', 'Е': 'E', 'Є': 'Ye', 'Ж': 'Zh', 'З': 'Z',
  'И': 'Y', 'І': 'I', 'Ї': 'Yi', 'Й': 'Y', 'К': 'K',
  'Л': 'L', 'М': 'M', 'Н': 'N', 'О': 'O', 'П': 'P',
  'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U', 'Ф': 'F',
  'Х': 'Kh', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Shch',
  'Ь': '', 'Ю': 'Yu', 'Я': 'Ya', 'Ё': 'Yo', 'Ы': 'Y', 'Э': 'E', 'Ъ': '',
  'а': 'a', 'б': 'b', 'в': 'v', 'г': 'h', 'ґ': 'g',
  'д': 'd', 'е': 'e', 'є': 'ye', 'ж': 'zh', 'з': 'z',
  'и': 'y', 'і': 'i', 'ї': 'yi', 'й': 'y', 'к': 'k',
  'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p',
  'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f',
  'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
  'ь': '', 'ю': 'yu', 'я': 'ya', 'ё': 'yo', 'ы': 'y', 'э': 'e', 'ъ': '',
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

function normalizeWords(name: string): string[] {
  return stripAccents(transliterateCyrillic(name))
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, '')
    .trim()
    .split(/\s+/)
    .filter(w => w.length > 1);
}

function levenshtein(s1: string, s2: string): number {
  if (s1.length < s2.length) return levenshtein(s2, s1);
  if (s2.length === 0) return s1.length;
  let prev = Array.from({ length: s2.length + 1 }, (_, i) => i);
  for (let i = 0; i < s1.length; i++) {
    const curr = [i + 1];
    for (let j = 0; j < s2.length; j++) {
      curr.push(Math.min(prev[j + 1] + 1, curr[j] + 1, prev[j] + (s1[i] !== s2[j] ? 1 : 0)));
    }
    prev = curr;
  }
  return prev[s2.length];
}

function namesSimilar(nameA: string, nameB: string): boolean {
  const wordsA = normalizeWords(nameA);
  const wordsB = normalizeWords(nameB);
  if (wordsA.length === 0 || wordsB.length === 0) return false;

  let matched = 0;
  for (const wa of wordsA) {
    for (const wb of wordsB) {
      if (wa === wb || levenshtein(wa, wb) <= 1 || (Math.min(wa.length, wb.length) >= 5 && levenshtein(wa, wb) <= 2)) {
        matched++;
        break;
      }
    }
  }

  // Forward: all A words in B
  if (matched === wordsA.length && matched >= 2) return true;

  // Reverse: all B words in A
  let matchedRev = 0;
  for (const wb of wordsB) {
    for (const wa of wordsA) {
      if (wa === wb || levenshtein(wa, wb) <= 1 || (Math.min(wa.length, wb.length) >= 5 && levenshtein(wa, wb) <= 2)) {
        matchedRev++;
        break;
      }
    }
  }
  if (matchedRev === wordsB.length && matchedRev >= 2) return true;

  return false;
}

// ── Service ───────────────────────────────────────────────────────────────────

export class ThirdPartyResolverService {

  /**
   * Step 1: Scan ALL chat messages for emails and Didit verification links.
   */
  async extractEmailsFromChats(): Promise<ChatExtraction[]> {
    log.info('[ThirdParty] Scanning chat messages for emails and Didit links...');

    const messages = await prisma.p2PChatMessage.findMany({
      where: {
        OR: [
          { content: { contains: '@' } },
          { content: { contains: 'verify.didit.me' } },
        ],
      },
      include: {
        order: {
          select: {
            id: true,
            externalOrderId: true,
            counterpartyName: true,
            amount: true,
            fiat: true,
          },
        },
      },
    });

    // Group by order
    const orderMap = new Map<string, ChatExtraction>();

    for (const msg of messages) {
      const orderId = msg.order.id;
      if (!orderMap.has(orderId)) {
        orderMap.set(orderId, {
          orderId,
          externalOrderId: msg.order.externalOrderId,
          counterpartyName: msg.order.counterpartyName,
          amount: msg.order.amount.toString(),
          fiat: msg.order.fiat,
          emails: [],
          diditLinks: [],
        });
      }

      const entry = orderMap.get(orderId)!;

      // Extract emails
      const emailMatches = msg.content.match(EMAIL_REGEX);
      if (emailMatches) {
        for (const email of emailMatches) {
          const lower = email.toLowerCase();
          if (!entry.emails.includes(lower)) entry.emails.push(lower);
        }
      }

      // Extract Didit links
      const linkMatches = [...msg.content.matchAll(DIDIT_LINK_REGEX)];
      for (const match of linkMatches) {
        const sessionSlug = match[1];
        if (!entry.diditLinks.includes(sessionSlug)) entry.diditLinks.push(sessionSlug);
      }
    }

    const results = Array.from(orderMap.values()).filter(e => e.emails.length > 0 || e.diditLinks.length > 0);
    log.info(`[ThirdParty] Found ${results.length} orders with emails/links in chat.`);
    return results;
  }

  /**
   * Step 2: Cross-reference chat emails with Didit KYC sessions.
   */
  async crossReferenceWithDidit(extractions: ChatExtraction[]): Promise<ThirdPartyCandidate[]> {
    log.info('[ThirdParty] Cross-referencing with Didit KYC sessions...');

    // Load all KYC sessions with emails
    const allSessions = await prisma.kycSession.findMany({
      where: { fullName: { not: null } },
      include: { provider: { select: { name: true } } },
    });

    // Build email → session map from Didit rawPayload
    const emailToSession = new Map<string, typeof allSessions[0]>();
    const sessionUrlToSession = new Map<string, typeof allSessions[0]>();

    for (const sess of allSessions) {
      const raw = sess.rawPayload as any;
      if (raw?.email_address?.email) {
        emailToSession.set(raw.email_address.email.toLowerCase(), sess);
      }
      if (raw?.session_url) {
        // Extract slug from URL
        const match = raw.session_url.match(/\/session\/([A-Za-z0-9]+)/);
        if (match) sessionUrlToSession.set(match[1], sess);
      }
    }

    log.info(`[ThirdParty] ${emailToSession.size} Didit sessions have emails, ${sessionUrlToSession.size} have URLs.`);

    // Load Januar transactions for payment verification
    const januarTxns = await prisma.transaction.findMany({
      where: { source: 'januar', type: 'TRANSFER_IN' },
      select: { description: true, amount: true, metadata: true, completedAt: true },
    });

    const candidates: ThirdPartyCandidate[] = [];

    for (const extraction of extractions) {
      if (!extraction.counterpartyName) continue;

      let matchedSession: typeof allSessions[0] | null = null;

      // Try email match first
      for (const email of extraction.emails) {
        const sess = emailToSession.get(email);
        if (sess) { matchedSession = sess; break; }
      }

      // Try Didit link match
      if (!matchedSession) {
        for (const slug of extraction.diditLinks) {
          const sess = sessionUrlToSession.get(slug);
          if (sess) { matchedSession = sess; break; }
        }
      }

      if (!matchedSession || !matchedSession.fullName) continue;

      const kycName = matchedSession.fullName;
      const binanceName = extraction.counterpartyName;

      // Compare names
      const isSamePerson = namesSimilar(binanceName, kycName);

      // Check Januar for payment verification (name match + IBAN cross-ref)
      let januarMatch = false;
      let januarSenderName: string | null = null;
      let januarAmount: string | null = null;

      if (!isSamePerson) {
        // Strategy 1: Name match on Januar sender
        for (const txn of januarTxns) {
          const meta = txn.metadata as any;
          const senderName = meta?.senderName || meta?.counterparty?.name || txn.description || '';
          if (!senderName) continue;

          if (namesSimilar(kycName, senderName)) {
            // Check amount tolerance (±10%)
            const txnAmount = parseFloat(txn.amount.toString());
            const orderAmount = parseFloat(extraction.amount);
            const tolerance = orderAmount * 0.10;
            if (Math.abs(txnAmount - orderAmount) <= tolerance) {
              januarMatch = true;
              januarSenderName = senderName;
              januarAmount = txn.amount.toString();
              break;
            }
          }
        }

        // Strategy 2: IBAN cross-referencing
        // If the same IBAN sent multiple payments, map repeat payers
        if (!januarMatch) {
          // Build IBAN → payment history map
          const ibanPayments = new Map<string, { senderName: string; amounts: number[]; count: number }>();
          for (const txn of januarTxns) {
            const meta = txn.metadata as any;
            const iban = meta?.senderIban || meta?.counterparty?.accountNumber || '';
            const senderName = meta?.senderName || meta?.counterparty?.name || txn.description || '';
            if (!iban || !senderName) continue;

            if (!ibanPayments.has(iban)) {
              ibanPayments.set(iban, { senderName, amounts: [], count: 0 });
            }
            const entry = ibanPayments.get(iban)!;
            entry.amounts.push(parseFloat(txn.amount.toString()));
            entry.count++;
          }

          // Check if the KYC name matches any IBAN sender
          for (const [iban, data] of ibanPayments) {
            if (namesSimilar(kycName, data.senderName)) {
              // Found IBAN whose sender matches KYC name
              // Check if any payment amount matches this order
              const orderAmount = parseFloat(extraction.amount);
              const matchingAmount = data.amounts.find(a => Math.abs(a - orderAmount) <= orderAmount * 0.15);
              if (matchingAmount) {
                januarMatch = true;
                januarSenderName = `${data.senderName} (IBAN: ${iban.substring(0, 8)}...)`;
                januarAmount = matchingAmount.toString();
                break;
              }
            }
          }
        }
      }

      const raw = matchedSession.rawPayload as any;
      candidates.push({
        orderId: extraction.orderId,
        externalOrderId: extraction.externalOrderId,
        binanceName,
        kycName,
        kycEmail: raw?.email_address?.email || null,
        kycCountry: matchedSession.country,
        kycStatus: matchedSession.status,
        kycSessionId: matchedSession.externalId,
        kycProvider: matchedSession.provider.name,
        orderAmount: extraction.amount,
        orderFiat: extraction.fiat,
        matchType: isSamePerson ? 'SAME_PERSON' : 'THIRD_PARTY',
        januarMatch,
        januarSenderName,
        januarAmount,
        confidence: isSamePerson ? 1.0 : (januarMatch ? 0.95 : 0.50),
      });
    }

    log.info(`[ThirdParty] Found ${candidates.length} candidates: ${candidates.filter(c => c.matchType === 'SAME_PERSON').length} same-person, ${candidates.filter(c => c.matchType === 'THIRD_PARTY').length} third-party`);
    return candidates;
  }

  /**
   * Step 3: Apply resolutions — create users, link KYC, reassign volume.
   */
  async resolveThirdParties(candidates: ThirdPartyCandidate[]): Promise<{
    linkedKyc: number;
    thirdPartiesResolved: number;
    usersCreated: number;
    volumeReassigned: string;
  }> {
    let linkedKyc = 0;
    let thirdPartiesResolved = 0;
    let usersCreated = 0;
    let volumeReassigned = 0;

    for (const c of candidates) {
      if (c.matchType === 'SAME_PERSON') {
        // Link KYC data to the existing Binance user
        const order = await prisma.p2POrder.findUnique({
          where: { id: c.orderId },
          select: { userId: true },
        });
        if (order?.userId) {
          // Store full Didit KYC data on the user
          await prisma.user.update({
            where: { id: order.userId },
            data: {
              email: c.kycEmail || undefined,
              country: c.kycCountry || undefined,
              metadata: {
                kycEmail: c.kycEmail,
                kycSessionId: c.kycSessionId,
                kycProvider: c.kycProvider,
                kycVerifiedName: c.kycName,
                kycCountry: c.kycCountry,
                kycStatus: c.kycStatus,
                linkedAt: new Date().toISOString(),
              },
            },
          });
          linkedKyc++;
        }
      } else if (c.matchType === 'THIRD_PARTY' && c.confidence >= 0.90) {
        // Find or create user for the actual payer
        let payerUser = await prisma.user.findFirst({
          where: {
            OR: [
              { legalName: c.kycName },
              { email: c.kycEmail || undefined },
            ],
          },
        });

        if (!payerUser) {
          payerUser = await prisma.user.create({
            data: {
              displayName: c.kycName,
              legalName: c.kycName,
              email: c.kycEmail,
              country: c.kycCountry,
              kycStatus: c.kycStatus === 'APPROVED' ? 'APPROVED' : 'PENDING',
              metadata: {
                source: 'third_party_resolution',
                kycSessionId: c.kycSessionId,
                kycProvider: c.kycProvider,
                kycVerifiedName: c.kycName,
                kycCountry: c.kycCountry,
                kycStatus: c.kycStatus,
                resolvedAt: new Date().toISOString(),
              },
            },
          });
          usersCreated++;
          log.info(`[ThirdParty] Created user: ${c.kycName} (${payerUser.id})`);
        }

        // Mark order as third-party and assign actual payer
        await prisma.p2POrder.update({
          where: { id: c.orderId },
          data: {
            actualPayerId: payerUser.id,
            isThirdParty: true,
          },
        });

        volumeReassigned += parseFloat(c.orderAmount);
        thirdPartiesResolved++;
      }
    }

    // Recompute volumes for all affected users
    await this.recomputeVolumes();

    log.info(`[ThirdParty] Resolution complete: ${linkedKyc} KYC linked, ${thirdPartiesResolved} third-parties resolved, ${usersCreated} users created`);

    return {
      linkedKyc,
      thirdPartiesResolved,
      usersCreated,
      volumeReassigned: volumeReassigned.toFixed(2),
    };
  }

  /**
   * Recompute totalVolume for all users based on actual payment attribution.
   * User volume = orders they placed (not third-party) + orders they paid as third party
   */
  async recomputeVolumes(): Promise<void> {
    log.info('[ThirdParty] Recomputing user volumes...');

    // Get all users with orders
    const users = await prisma.user.findMany({
      where: { OR: [{ orders: { some: {} } }, { ordersAsPayer: { some: {} } }] },
      select: { id: true },
    });

    for (const user of users) {
      // Own volume: orders placed by this user that are NOT third-party
      const ownOrders = await prisma.p2POrder.aggregate({
        where: { userId: user.id, isThirdParty: false, status: 'COMPLETED' },
        _sum: { amount: true },
        _count: true,
      });

      // Payer volume: orders where this user was the actual payer (third-party)
      const payerOrders = await prisma.p2POrder.aggregate({
        where: { actualPayerId: user.id, status: 'COMPLETED' },
        _sum: { amount: true },
        _count: true,
      });

      const ownVol = ownOrders._sum.amount ? parseFloat(ownOrders._sum.amount.toString()) : 0;
      const payerVol = payerOrders._sum.amount ? parseFloat(payerOrders._sum.amount.toString()) : 0;
      const totalTrades = (ownOrders._count || 0) + (payerOrders._count || 0);

      await prisma.user.update({
        where: { id: user.id },
        data: {
          totalVolume: ownVol + payerVol,
          totalTrades,
        },
      });
    }

    log.info('[ThirdParty] Volume recomputation complete.');
  }

  /**
   * Run full pipeline: extract → cross-reference → return candidates for review.
   */
  async scanForCandidates(): Promise<ThirdPartyCandidate[]> {
    const extractions = await this.extractEmailsFromChats();
    const candidates = await this.crossReferenceWithDidit(extractions);
    return candidates;
  }

  /**
   * Run full pipeline and auto-resolve.
   */
  async runFullResolution(): Promise<{
    extractions: number;
    candidates: ThirdPartyCandidate[];
    resolution: {
      linkedKyc: number;
      thirdPartiesResolved: number;
      usersCreated: number;
      volumeReassigned: string;
    };
  }> {
    const extractions = await this.extractEmailsFromChats();
    const candidates = await this.crossReferenceWithDidit(extractions);
    const resolution = await this.resolveThirdParties(candidates);

    return {
      extractions: extractions.length,
      candidates,
      resolution,
    };
  }
}

export const thirdPartyResolver = new ThirdPartyResolverService();
