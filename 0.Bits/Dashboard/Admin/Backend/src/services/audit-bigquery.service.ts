/**
 * Immutable Audit Log — BigQuery Sink
 * 
 * Every admin mutation is written to BigQuery as an append-only,
 * tamper-proof audit trail. BigQuery tables cannot be modified
 * via streaming insert — only appended to. This provides SOC 2
 * compliance evidence that no audit records have been altered.
 */

import { createLogger } from "../lib/logger.js";
const log = createLogger("audit-bq");

const GCP_PROJECT = "project-6f4828a2-2b35-4f50-8b2";
const BQ_DATASET = "0core_analytics";
const BQ_TABLE = "audit_trail";

async function getAccessToken(): Promise<string> {
  const { execSync } = await import("child_process");
  return execSync("/data/gcp/get-token.sh").toString().trim();
}

export interface AuditEntry {
  id: string;
  adminId: string;
  action: string;
  resource: string;
  resourceId?: string | null;
  method: string;
  path: string;
  ipAddress: string;
  userAgent?: string | null;
  requestBody?: Record<string, unknown> | null;
  responseCode?: number | null;
  duration?: number | null;
  correlationId?: string | null;
}

/**
 * Write a single audit entry to BigQuery.
 * Fire-and-forget — failures are logged but never block the request.
 */
export async function sinkAuditToBigQuery(entry: AuditEntry): Promise<void> {
  try {
    const token = await getAccessToken();
    const url = `https://bigquery.googleapis.com/bigquery/v2/projects/${GCP_PROJECT}/datasets/${BQ_DATASET}/tables/${BQ_TABLE}/insertAll`;

    const row = {
      ...entry,
      requestBody: entry.requestBody ? JSON.stringify(entry.requestBody) : null,
      createdAt: new Date().toISOString().replace("T", " ").slice(0, 19),
    };

    const resp = await fetch(url, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ rows: [{ json: row }] }),
    });

    const data = (await resp.json()) as any;
    if (data.insertErrors?.length) {
      log.error("[AuditBQ] Insert error:", JSON.stringify(data.insertErrors));
    }
  } catch (err) {
    log.error("[AuditBQ] Failed to sink audit:", (err as Error).message);
  }
}
