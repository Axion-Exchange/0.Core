/**
 * Uptime Monitor — Lightweight external health check.
 * 
 * Doc ref: §Observability and Incident Response (citations 10, 38)
 * "Without APM, failures like out-of-memory exceptions can cause
 *  silent restarts that go undetected for days."
 * 
 * Runs as a cron job (PM2 or system cron):
 *   pm2 start dist/scripts/health-monitor.js --name 0core-monitor (every 5 minutes via cron)
 * 
 * Checks:
 * 1. API health endpoint responds 200
 * 2. Response time < 5s threshold
 * 3. Database reports "operational"
 * 4. Logs alerts to structured logger + optional webhook
 */

import { createLogger } from '../lib/logger.js';

const log = createLogger('health-monitor');

interface HealthCheckResult {
  endpoint: string;
  status: 'UP' | 'DOWN' | 'DEGRADED';
  responseTimeMs: number;
  statusCode: number;
  details?: Record<string, unknown>;
}

const ENDPOINTS = [
  { name: 'API Health', url: 'http://localhost:4000/api/v1/health' },
];

const RESPONSE_TIME_THRESHOLD_MS = 5000;
const WEBHOOK_URL = process.env.ALERT_WEBHOOK_URL; // Optional Discord/Slack webhook

async function checkEndpoint(name: string, url: string): Promise<HealthCheckResult> {
  const start = Date.now();
  try {
    const res = await fetch(url, { signal: AbortSignal.timeout(10000) });
    const responseTimeMs = Date.now() - start;
    const body = await res.json() as any;

    const status: 'UP' | 'DOWN' | 'DEGRADED' =
      res.status !== 200 ? 'DOWN' :
      body.data?.status === 'degraded' ? 'DEGRADED' :
      responseTimeMs > RESPONSE_TIME_THRESHOLD_MS ? 'DEGRADED' :
      'UP';

    return {
      endpoint: name,
      status,
      responseTimeMs,
      statusCode: res.status,
      details: {
        dbStatus: body.data?.status,
        uptime: body.data?.uptime,
        version: body.data?.version,
      },
    };
  } catch (err: any) {
    return {
      endpoint: name,
      status: 'DOWN',
      responseTimeMs: Date.now() - start,
      statusCode: 0,
      details: { error: err.message },
    };
  }
}

async function sendAlert(results: HealthCheckResult[]) {
  const failures = results.filter(r => r.status !== 'UP');
  if (failures.length === 0) return;

  const message = failures.map(f =>
    `⚠️ ${f.endpoint}: ${f.status} (${f.responseTimeMs}ms, HTTP ${f.statusCode})`
  ).join('\n');

  log.error(`[Alert] Health check failures:\n${message}`);

  if (WEBHOOK_URL) {
    try {
      await fetch(WEBHOOK_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: `🚨 **0core Health Alert**\n${message}\n\`${new Date().toISOString()}\``,
        }),
      });
    } catch (err: any) {
      log.error(`[Alert] Failed to send webhook: ${err.message}`);
    }
  }
}

async function main() {
  const results: HealthCheckResult[] = [];

  for (const ep of ENDPOINTS) {
    const result = await checkEndpoint(ep.name, ep.url);
    results.push(result);

    const icon = result.status === 'UP' ? '✅' : result.status === 'DEGRADED' ? '⚠️' : '❌';
    log.info(`${icon} ${result.endpoint}: ${result.status} (${result.responseTimeMs}ms)`);
  }

  await sendAlert(results);

  // Exit with code 1 if any check failed (for cron alerting)
  const hasFailure = results.some(r => r.status === 'DOWN');
  process.exit(hasFailure ? 1 : 0);
}

main().catch(err => {
  log.error(`[Monitor] Fatal: ${err.message}`);
  process.exit(1);
});
