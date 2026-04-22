/**
 * Counterparty Risk Scoring Engine
 * 
 * Computes a 0-100 risk score for each P2P counterparty based on:
 * - Cancellation rate (higher = riskier)
 * - Order frequency (too many too fast = suspicious)
 * - Amount consistency (high variance = suspicious)
 * - Account age (newer = riskier)
 * - Third-party payment history
 * 
 * Scores are persisted to BigQuery for trend analysis.
 * This is READ-ONLY analytics — it does NOT block or release orders.
 */

import { prisma } from "../lib/db.js";
import { createLogger } from "../lib/logger.js";

const log = createLogger("risk-score");

const GCP_PROJECT = "project-6f4828a2-2b35-4f50-8b2";
const BQ_DATASET = "0core_analytics";

async function getAccessToken(): Promise<string> {
  const { execSync } = await import("child_process");
  return execSync("/data/gcp/get-token.sh").toString().trim();
}

export interface CounterpartyRisk {
  nickname: string;
  totalOrders: number;
  completedOrders: number;
  cancelledOrders: number;
  completionRate: number;
  avgAmount: number;
  totalVolume: number;
  firstSeen: Date;
  lastSeen: Date;
  riskScore: number;        // 0 = safest, 100 = riskiest
  riskLevel: "low" | "medium" | "high" | "critical";
  factors: string[];
}

function computeRiskScore(stats: {
  totalOrders: number;
  completedOrders: number;
  cancelledOrders: number;
  thirdPartyCount: number;
  daysSinceFirst: number;
  amountStdDev: number;
  avgAmount: number;
}): { score: number; factors: string[] } {
  let score = 0;
  const factors: string[] = [];

  // Factor 1: Cancellation rate (0-30 points)
  const cancelRate = stats.totalOrders > 0 ? stats.cancelledOrders / stats.totalOrders : 0;
  if (cancelRate > 0.3) { score += 30; factors.push(`High cancel rate: ${(cancelRate * 100).toFixed(0)}%`); }
  else if (cancelRate > 0.15) { score += 15; factors.push(`Moderate cancel rate: ${(cancelRate * 100).toFixed(0)}%`); }
  else if (cancelRate > 0.05) { score += 5; factors.push(`Low cancel rate: ${(cancelRate * 100).toFixed(0)}%`); }

  // Factor 2: Account age (0-20 points)
  if (stats.daysSinceFirst < 3) { score += 20; factors.push("Account < 3 days old"); }
  else if (stats.daysSinceFirst < 14) { score += 10; factors.push("Account < 2 weeks old"); }

  // Factor 3: Third-party payments (0-25 points)
  const thirdPartyRate = stats.totalOrders > 0 ? stats.thirdPartyCount / stats.totalOrders : 0;
  if (thirdPartyRate > 0.3) { score += 25; factors.push(`Third-party payments: ${(thirdPartyRate * 100).toFixed(0)}%`); }
  else if (thirdPartyRate > 0.1) { score += 10; factors.push(`Some third-party: ${(thirdPartyRate * 100).toFixed(0)}%`); }

  // Factor 4: Amount variance (0-15 points)
  const cv = stats.avgAmount > 0 ? stats.amountStdDev / stats.avgAmount : 0;
  if (cv > 1.5) { score += 15; factors.push(`High amount variance: CV=${cv.toFixed(1)}`); }
  else if (cv > 0.8) { score += 5; factors.push(`Moderate variance: CV=${cv.toFixed(1)}`); }

  // Factor 5: Velocity (0-10 points)
  const ordersPerDay = stats.daysSinceFirst > 0 ? stats.totalOrders / stats.daysSinceFirst : stats.totalOrders;
  if (ordersPerDay > 5) { score += 10; factors.push(`High velocity: ${ordersPerDay.toFixed(1)} orders/day`); }

  // Clamp
  score = Math.min(100, Math.max(0, score));

  if (factors.length === 0) factors.push("No risk factors detected");

  return { score, factors };
}

function getRiskLevel(score: number): "low" | "medium" | "high" | "critical" {
  if (score >= 70) return "critical";
  if (score >= 45) return "high";
  if (score >= 20) return "medium";
  return "low";
}

export async function scoreAllCounterparties(): Promise<CounterpartyRisk[]> {
  log.info("[RiskScore] Scoring all counterparties...");

  const stats = await prisma.$queryRawUnsafe(`
    SELECT 
      counterparty as nickname,
      COUNT(*)::int as "totalOrders",
      SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END)::int as "completedOrders",
      SUM(CASE WHEN status = 'CANCELLED' THEN 1 ELSE 0 END)::int as "cancelledOrders",
      COUNT(*) FILTER (WHERE "isThirdParty" = true)::int as "thirdPartyCount",
      AVG("fiatAmount"::float) as "avgAmount",
      STDDEV("fiatAmount"::float) as "amountStdDev",
      SUM("fiatAmount"::float) as "totalVolume",
      MIN("createdAt") as "firstSeen",
      MAX("createdAt") as "lastSeen",
      EXTRACT(EPOCH FROM (NOW() - MIN("createdAt"))) / 86400 as "daysSinceFirst"
    FROM p2p_orders
    WHERE counterparty IS NOT NULL
    GROUP BY counterparty
    HAVING COUNT(*) >= 2
    ORDER BY COUNT(*) DESC
  `);

  const results: CounterpartyRisk[] = stats.map((s: any) => {
    const { score, factors } = computeRiskScore({
      totalOrders: s.totalOrders,
      completedOrders: s.completedOrders,
      cancelledOrders: s.cancelledOrders,
      thirdPartyCount: s.thirdPartyCount || 0,
      daysSinceFirst: s.daysSinceFirst || 1,
      amountStdDev: s.amountStdDev || 0,
      avgAmount: s.avgAmount || 0,
    });

    return {
      nickname: s.nickname,
      totalOrders: s.totalOrders,
      completedOrders: s.completedOrders,
      cancelledOrders: s.cancelledOrders,
      completionRate: s.totalOrders > 0 ? s.completedOrders / s.totalOrders : 0,
      avgAmount: s.avgAmount || 0,
      totalVolume: s.totalVolume || 0,
      firstSeen: s.firstSeen,
      lastSeen: s.lastSeen,
      riskScore: score,
      riskLevel: getRiskLevel(score),
      factors,
    };
  });

  // Sink to BigQuery
  try {
    const token = await getAccessToken();
    const url = `https://bigquery.googleapis.com/bigquery/v2/projects/${GCP_PROJECT}/datasets/${BQ_DATASET}/tables/counterparty_risk/insertAll`;
    const bqRows = results.map(r => ({
      json: {
        ...r,
        firstSeen: r.firstSeen?.toISOString?.()?.replace("T", " ")?.slice(0, 19) || "",
        lastSeen: r.lastSeen?.toISOString?.()?.replace("T", " ")?.slice(0, 19) || "",
        factors: JSON.stringify(r.factors),
        scoredAt: new Date().toISOString().replace("T", " ").slice(0, 19),
      },
    }));

    for (let i = 0; i < bqRows.length; i += 500) {
      const batch = bqRows.slice(i, i + 500);
      await fetch(url, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({ rows: batch }),
      });
    }
    log.info(`[RiskScore] ${results.length} counterparties scored and synced to BigQuery`);
  } catch (err) {
    log.error("[RiskScore] BigQuery sync failed:", (err as Error).message);
  }

  return results;
}

export async function getCounterpartyRisk(nickname: string): Promise<CounterpartyRisk | null> {
  const all = await scoreAllCounterparties();
  return all.find(r => r.nickname === nickname) || null;
}
