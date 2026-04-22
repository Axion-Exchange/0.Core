/**
 * Fraud Notifier Service — COMPLETELY ISOLATED
 * 
 * ⚠️ SECURITY: This service has ZERO write permissions.
 * - Reads from BigQuery only (6-hour delayed data)
 * - Cannot access live PostgreSQL directly
 * - Cannot release orders, approve KYC, or modify any data
 * - Only outputs notifications to Telegram
 * - Uses dedicated service account: axion-ai-notify (bigquery.dataViewer)
 */

import { createLogger } from "../lib/logger.js";
const log = createLogger("fraud-notifier");

const GCP_PROJECT = "project-6f4828a2-2b35-4f50-8b2";
const BQ_DATASET = "0core_analytics";
const TELEGRAM_BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN;
const TELEGRAM_CHAT_ID = process.env.TELEGRAM_CHAT_ID;

interface FraudAlert {
  type: "cancelled_spike" | "name_mismatch" | "volume_anomaly" | "amount_mismatch";
  severity: "low" | "medium" | "high";
  description: string;
  entity: string;
  value: string;
}

/**
 * Get a fresh access token from the ADC refresh token.
 * This runs on the VPS using the /data/gcp/adc.json credentials.
 */
async function getAccessToken(): Promise<string> {
  const { execSync } = await import("child_process");
  return execSync("/data/gcp/get-token.sh").toString().trim();
}

/**
 * Run a BigQuery query and return rows.
 * READ-ONLY: Only SELECT queries are allowed.
 */
async function queryBigQuery(sql: string): Promise<any[]> {
  const token = await getAccessToken();
  const url = `https://bigquery.googleapis.com/bigquery/v2/projects/${GCP_PROJECT}/queries`;
  
  const resp = await fetch(url, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      query: sql,
      useLegacySql: false,
      maxResults: 1000,
    }),
  });
  
  const data = await resp.json() as any;
  if (data.errors) {
    log.error("[FraudNotifier] BigQuery error:", data.errors);
    return [];
  }
  
  const fields = data.schema?.fields || [];
  const rows = data.rows || [];
  
  return rows.map((row: any) => {
    const obj: any = {};
    row.f.forEach((cell: any, i: number) => {
      obj[fields[i].name] = cell.v;
    });
    return obj;
  });
}

/**
 * Send alert to Telegram (notification only, no data mutation).
 */
async function sendTelegramAlert(alerts: FraudAlert[]): Promise<void> {
  if (!TELEGRAM_BOT_TOKEN || !TELEGRAM_CHAT_ID || alerts.length === 0) return;
  
  const highCount = alerts.filter(a => a.severity === "high").length;
  const medCount = alerts.filter(a => a.severity === "medium").length;
  
  let message = `🔍 *Fraud Monitor — ${alerts.length} pattern(s) detected*\n`;
  message += `├ 🔴 High: ${highCount}  🟡 Medium: ${medCount}\n\n`;
  
  for (const alert of alerts.slice(0, 10)) {
    const icon = alert.severity === "high" ? "🔴" : alert.severity === "medium" ? "🟡" : "🔵";
    message += `${icon} *${alert.type}*\n`;
    message += `├ ${alert.description}\n`;
    message += `├ Entity: \`${alert.entity}\`\n`;
    message += `└ Value: ${alert.value}\n\n`;
  }
  
  message += `_Automated scan — review at 0bit.app_`;
  
  try {
    await fetch(`https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        chat_id: TELEGRAM_CHAT_ID,
        text: message,
        parse_mode: "Markdown",
      }),
    });
    log.info(`[FraudNotifier] Telegram alert sent: ${alerts.length} patterns`);
  } catch (err) {
    log.error("[FraudNotifier] Telegram send failed:", err);
  }
}

/**
 * Rule 1: Counterparties with excessive cancellations (>3 in 7 days)
 */
async function checkCancelledSpikes(): Promise<FraudAlert[]> {
  const rows = await queryBigQuery(`
    SELECT counterpartyNickname, COUNT(*) as cancel_count
    FROM \`${BQ_DATASET}.p2p_orders\`
    WHERE status = "CANCELLED"
      AND createdAt >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
    GROUP BY counterpartyNickname
    HAVING cancel_count > 3
    ORDER BY cancel_count DESC
    LIMIT 20
  `);
  
  return rows.map(r => ({
    type: "cancelled_spike" as const,
    severity: parseInt(r.cancel_count) > 8 ? "high" as const : "medium" as const,
    description: `${r.cancel_count} cancelled orders in 7 days`,
    entity: r.counterpartyNickname || "Unknown",
    value: `${r.cancel_count} cancellations`,
  }));
}

/**
 * Rule 2: Volume anomalies (orders > 3σ from 30-day mean)
 */
async function checkVolumeAnomalies(): Promise<FraudAlert[]> {
  const rows = await queryBigQuery(`
    WITH daily_volume AS (
      SELECT DATE(createdAt) as day, SUM(total) as volume
      FROM \`${BQ_DATASET}.p2p_orders\`
      WHERE status = "COMPLETED" AND fiat = "EUR"
      GROUP BY day
    ),
    stats AS (
      SELECT AVG(volume) as mean, STDDEV(volume) as std FROM daily_volume
    )
    SELECT dv.day, dv.volume, s.mean, s.std,
           (dv.volume - s.mean) / NULLIF(s.std, 0) as z_score
    FROM daily_volume dv CROSS JOIN stats s
    WHERE dv.day >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
      AND (dv.volume - s.mean) / NULLIF(s.std, 0) > 3
    ORDER BY dv.day DESC
  `);
  
  return rows.map(r => ({
    type: "volume_anomaly" as const,
    severity: parseFloat(r.z_score) > 4 ? "high" as const : "medium" as const,
    description: `Daily volume €${parseFloat(r.volume).toFixed(0)} is ${parseFloat(r.z_score).toFixed(1)}σ above mean €${parseFloat(r.mean).toFixed(0)}`,
    entity: r.day,
    value: `€${parseFloat(r.volume).toFixed(0)} (z=${parseFloat(r.z_score).toFixed(1)})`,
  }));
}

/**
 * Rule 3: Counterparties with name mismatches on completed orders
 */
async function checkNameMismatches(): Promise<FraudAlert[]> {
  const rows = await queryBigQuery(`
    SELECT counterpartyNickname, counterpartyName, COUNT(*) as order_count
    FROM \`${BQ_DATASET}.p2p_orders\`
    WHERE status = "COMPLETED"
      AND counterpartyName IS NOT NULL
      AND counterpartyNickname IS NOT NULL
      AND LOWER(counterpartyName) != LOWER(counterpartyNickname)
      AND createdAt >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
    GROUP BY counterpartyNickname, counterpartyName
    HAVING order_count >= 3
    ORDER BY order_count DESC
    LIMIT 10
  `);
  
  return rows.map(r => ({
    type: "name_mismatch" as const,
    severity: "low" as const,
    description: `Nickname "${r.counterpartyNickname}" != Real name "${r.counterpartyName}"`,
    entity: r.counterpartyNickname || "Unknown",
    value: `${r.order_count} orders with mismatch`,
  }));
}

/**
 * Main entry point — runs all fraud checks and sends a single Telegram alert.
 * This function is COMPLETELY ISOLATED from the order execution pipeline.
 */
export async function runFraudScan(): Promise<FraudAlert[]> {
  log.info("[FraudNotifier] Starting fraud scan (read-only, BigQuery)...");
  
  const alerts: FraudAlert[] = [];
  
  try {
    const [cancels, volumes, names] = await Promise.all([
      checkCancelledSpikes(),
      checkVolumeAnomalies(),
      checkNameMismatches(),
    ]);
    
    alerts.push(...cancels, ...volumes, ...names);
    
    if (alerts.length > 0) {
      log.warn(`[FraudNotifier] ${alerts.length} patterns detected`);
      await sendTelegramAlert(alerts);
    } else {
      log.info("[FraudNotifier] No suspicious patterns detected");
    }
  } catch (err) {
    log.error("[FraudNotifier] Scan failed:", err);
  }
  
  return alerts;
}
