/**
 * BigQuery Sync Service
 * Exports P2P orders and health checks to BigQuery every 6 hours.
 */

import { prisma } from "../lib/db.js";
import { createLogger } from "../lib/logger.js";
const log = createLogger("bigquery-sync");

const GCP_PROJECT = "project-6f4828a2-2b35-4f50-8b2";
const BQ_DATASET = "0core_analytics";

async function getAccessToken(): Promise<string> {
  const { execSync } = await import("child_process");
  return execSync("/data/gcp/get-token.sh").toString().trim();
}

async function insertRows(table: string, rows: any[]): Promise<number> {
  if (rows.length === 0) return 0;
  
  const token = await getAccessToken();
  const url = `https://bigquery.googleapis.com/bigquery/v2/projects/${GCP_PROJECT}/datasets/${BQ_DATASET}/tables/${table}/insertAll`;
  
  let total = 0;
  const batchSize = 500;
  
  for (let i = 0; i < rows.length; i += batchSize) {
    const batch = rows.slice(i, i + batchSize).map(r => ({ json: r }));
    
    const resp = await fetch(url, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ rows: batch }),
    });
    
    const data = await resp.json() as any;
    const errors = data.insertErrors?.length || 0;
    total += batch.length - errors;
    
    if (errors > 0) {
      log.warn(`[BQ-Sync] ${table} batch ${i / batchSize + 1}: ${errors} errors`);
    }
  }
  
  return total;
}

export async function syncToBigQuery(): Promise<{ orders: number; health: number }> {
  log.info("[BQ-Sync] Starting BigQuery sync...");
  
  // Sync recent P2P orders (last 7 days to catch updates)
  const recentOrders = await prisma.p2POrder.findMany({
    where: { updatedAt: { gte: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000) } },
    orderBy: { createdAt: "desc" },
  });
  
  const orderRows = recentOrders.map((o: any) => ({
    id: o.id,
    orderNumber: o.externalOrderId || "",
    type: o.type,
    asset: o.asset,
    fiat: o.fiat,
    price: parseFloat(o.price) || 0,
    amount: parseFloat(o.amount) || 0,
    total: parseFloat(o.fiatAmount) || 0,
    status: o.status,
    counterpartyNickname: o.counterparty || "",
    counterpartyName: o.counterpartyName || "",
    paymentMethod: o.paymentMethod || "",
    createdAt: o.createdAt?.toISOString()?.replace("T", " ")?.slice(0, 19) || "",
    completedAt: (o.completedAt || o.createdAt)?.toISOString()?.replace("T", " ")?.slice(0, 19) || "",
  }));
  
  const ordersInserted = await insertRows("p2p_orders", orderRows);
  
  // Sync health checks (last 24 hours)
  const recentHealth = await prisma.healthCheck.findMany({
    where: { checkedAt: { gte: new Date(Date.now() - 24 * 60 * 60 * 1000) } },
    orderBy: { checkedAt: "desc" },
  });
  
  const healthRows = recentHealth.map((h: any) => ({
    id: h.id,
    service: h.service,
    status: h.status,
    latencyMs: h.latencyMs,
    message: h.message || "",
    checkedAt: h.checkedAt?.toISOString()?.replace("T", " ")?.slice(0, 19) || "",
  }));
  
  const healthInserted = await insertRows("health_checks", healthRows);
  
  log.info(`[BQ-Sync] Synced ${ordersInserted} orders + ${healthInserted} health checks`);
  return { orders: ordersInserted, health: healthInserted };
}
