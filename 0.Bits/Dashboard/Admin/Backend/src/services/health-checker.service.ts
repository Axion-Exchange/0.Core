import { prisma } from "../lib/db.js";
import { checkDatabaseHealth } from "../lib/db.js";
import { createLogger } from "../lib/logger.js";
import { config } from "../config/index.js";

const log = createLogger("health-checker");

/**
 * Service Health Checker — Institutional-grade infrastructure monitoring.
 *
 * Probes all critical subsystems and writes results to the `health_checks` table
 * for historical tracking and dashboard display.
 *
 * Services monitored:
 * 1. PostgreSQL Database
 * 2. Redis Cache
 * 3. Binance Exchange API
 * 4. Januar Fiat Gateway (EUR)
 * 5. FacilitaPay Fiat Gateway (COP/MXN)
 * 6. Didit KYC Provider
 * 7. BullMQ Job Queue
 * 8. WebSocket Bridge
 * 9. API Server (self-check)
 */

interface ProbeResult {
  service: string;
  status: "healthy" | "degraded" | "down";
  latencyMs: number;
  message: string;
  metadata?: Record<string, unknown>;
}

async function probeWithTimeout(
  name: string,
  fn: () => Promise<ProbeResult>,
  timeoutMs = 10000
): Promise<ProbeResult> {
  try {
    const result = await Promise.race([
      fn(),
      new Promise<ProbeResult>((_, reject) =>
        setTimeout(() => reject(new Error("Probe timeout")), timeoutMs)
      ),
    ]);
    return result;
  } catch (err: any) {
    return {
      service: name,
      status: "down",
      latencyMs: timeoutMs,
      message: err.message || "Unknown error",
    };
  }
}

// ── Individual Probes ──────────────────────────────────────────

async function probeDatabase(): Promise<ProbeResult> {
  const start = Date.now();
  try {
    const healthy = await checkDatabaseHealth();
    const latencyMs = Date.now() - start;
    return {
      service: "database",
      status: healthy ? "healthy" : "down",
      latencyMs,
      message: healthy ? "PostgreSQL responding" : "Database unreachable",
    };
  } catch (err: any) {
    return {
      service: "database",
      status: "down",
      latencyMs: Date.now() - start,
      message: err.message,
    };
  }
}

async function probeRedis(): Promise<ProbeResult> {
  const start = Date.now();
  try {
    // Use dynamic import to avoid circular dependencies
    const { default: Redis } = await import("ioredis");
    const redis = new Redis(process.env.REDIS_URL || "redis://localhost:6379", {
      connectTimeout: 5000,
      lazyConnect: true,
    });
    await redis.connect();
    const pong = await redis.ping();
    const info = await redis.info("memory");
    const memMatch = info.match(/used_memory_human:(.+)/);
    const mem = memMatch ? memMatch[1].trim() : "unknown";
    await redis.quit();
    return {
      service: "redis",
      status: pong === "PONG" ? "healthy" : "degraded",
      latencyMs: Date.now() - start,
      message: `Redis responding (${mem} used)`,
      metadata: { memoryUsed: mem },
    };
  } catch (err: any) {
    return {
      service: "redis",
      status: "down",
      latencyMs: Date.now() - start,
      message: err.message,
    };
  }
}

async function probeBinanceAPI(): Promise<ProbeResult> {
  const start = Date.now();
  try {
    const res = await fetch("https://api.binance.com/api/v3/ping", {
      signal: AbortSignal.timeout(5000),
    });
    const latencyMs = Date.now() - start;
    return {
      service: "binance_api",
      status: res.ok ? "healthy" : "degraded",
      latencyMs,
      message: res.ok ? "Binance API reachable" : `HTTP ${res.status}`,
      metadata: { statusCode: res.status },
    };
  } catch (err: any) {
    return {
      service: "binance_api",
      status: "down",
      latencyMs: Date.now() - start,
      message: err.message,
    };
  }
}

async function probeJanuarAPI(): Promise<ProbeResult> {
  const start = Date.now();
  const baseUrl = config.JANUAR_BASE_URL || "https://api.januar.com";
  try {
    const res = await fetch(`${baseUrl}/health`, {
      signal: AbortSignal.timeout(5000),
    });
    const latencyMs = Date.now() - start;
    return {
      service: "januar_fiat",
      status: res.ok || res.status === 401 ? "healthy" : "degraded",
      latencyMs,
      message:
        res.ok || res.status === 401
          ? "Januar API reachable"
          : `HTTP ${res.status}`,
      metadata: { statusCode: res.status },
    };
  } catch (err: any) {
    return {
      service: "januar_fiat",
      status: "down",
      latencyMs: Date.now() - start,
      message: err.message,
    };
  }
}

async function probeFacilitaPay(): Promise<ProbeResult> {
  const start = Date.now();
  const baseUrl =
    config.FACILITAPAY_BASE_URL || "https://api.facilitapay.com/api/v1";
  try {
    const res = await fetch(`${baseUrl}/health`, {
      signal: AbortSignal.timeout(5000),
    });
    const latencyMs = Date.now() - start;
    return {
      service: "facilitapay_fiat",
      status: res.ok || res.status === 401 ? "healthy" : "degraded",
      latencyMs,
      message:
        res.ok || res.status === 401
          ? "FacilitaPay API reachable"
          : `HTTP ${res.status}`,
      metadata: { statusCode: res.status },
    };
  } catch (err: any) {
    return {
      service: "facilitapay_fiat",
      status: "down",
      latencyMs: Date.now() - start,
      message: err.message,
    };
  }
}

async function probeDiditKYC(): Promise<ProbeResult> {
  const start = Date.now();
  try {
    const res = await fetch("https://apx.didit.me/health", {
      signal: AbortSignal.timeout(5000),
    });
    const latencyMs = Date.now() - start;
    return {
      service: "didit_kyc",
      status: res.ok || res.status === 401 || res.status === 404 ? "healthy" : "degraded",
      latencyMs,
      message: "Didit KYC API reachable",
      metadata: { statusCode: res.status },
    };
  } catch (err: any) {
    return {
      service: "didit_kyc",
      status: "down",
      latencyMs: Date.now() - start,
      message: err.message,
    };
  }
}

async function probeBullMQ(): Promise<ProbeResult> {
  const start = Date.now();
  try {
    // Check if the BullMQ queues exist by querying Redis for bull:* keys
    const { default: Redis } = await import("ioredis");
    const redis = new Redis(process.env.REDIS_URL || "redis://localhost:6379", {
      connectTimeout: 5000,
      lazyConnect: true,
    });
    await redis.connect();
    const keys = await redis.keys("bull:*:id");
    await redis.quit();
    return {
      service: "bullmq_workers",
      status: keys.length > 0 ? "healthy" : "degraded",
      latencyMs: Date.now() - start,
      message: `${keys.length} queues active`,
      metadata: { queueCount: keys.length },
    };
  } catch (err: any) {
    return {
      service: "bullmq_workers",
      status: "down",
      latencyMs: Date.now() - start,
      message: err.message,
    };
  }
}

async function probeAPISelf(): Promise<ProbeResult> {
  const start = Date.now();
  try {
    const res = await fetch("http://localhost:4000/api/v1/health", {
      signal: AbortSignal.timeout(5000),
    });
    const body = (await res.json()) as any;
    const latencyMs = Date.now() - start;
    return {
      service: "api_server",
      status: body.data?.status === "operational" ? "healthy" : "degraded",
      latencyMs,
      message: `API v${body.data?.version || "?"} (uptime ${body.data?.uptime || 0}s)`,
      metadata: {
        uptime: body.data?.uptime,
        version: body.data?.version,
        memory: body.data?.memory,
      },
    };
  } catch (err: any) {
    return {
      service: "api_server",
      status: "down",
      latencyMs: Date.now() - start,
      message: err.message,
    };
  }
}

async function probeWebSocket(): Promise<ProbeResult> {
  const start = Date.now();
  try {
    // Simple HTTP check to the socket.io polling endpoint
    const res = await fetch(
      "http://localhost:4000/socket.io/?EIO=4&transport=polling",
      { signal: AbortSignal.timeout(5000) }
    );
    const latencyMs = Date.now() - start;
    return {
      service: "websocket_bridge",
      status: res.ok ? "healthy" : "degraded",
      latencyMs,
      message: res.ok ? "WebSocket bridge responding" : `HTTP ${res.status}`,
      metadata: { statusCode: res.status },
    };
  } catch (err: any) {
    return {
      service: "websocket_bridge",
      status: "down",
      latencyMs: Date.now() - start,
      message: err.message,
    };
  }
}

// ── Main Runner ──────────────────────────────────────────────

const ALL_PROBES = [
  { name: "database", fn: probeDatabase },
  { name: "redis", fn: probeRedis },
  { name: "binance_api", fn: probeBinanceAPI },
  { name: "januar_fiat", fn: probeJanuarAPI },
  { name: "facilitapay_fiat", fn: probeFacilitaPay },
  { name: "didit_kyc", fn: probeDiditKYC },
  { name: "bullmq_workers", fn: probeBullMQ },
  { name: "api_server", fn: probeAPISelf },
  { name: "websocket_bridge", fn: probeWebSocket },
];

/**
 * Run all health probes and persist results to the database.
 */
export async function runAllHealthChecks(): Promise<ProbeResult[]> {
  const results: ProbeResult[] = [];

  for (const probe of ALL_PROBES) {
    const result = await probeWithTimeout(probe.name, probe.fn);
    results.push(result);

    // Persist to database
    try {
      await prisma.healthCheck.create({
        data: {
          service: result.service,
          status: result.status,
          latencyMs: result.latencyMs,
          message: result.message,
          metadata: (result.metadata ?? undefined) as any,
        },
      });
    } catch (err: any) {
      log.error(`Failed to persist health check for ${probe.name}: ${err.message}`);
    }
  }

  return results;
}

/**
 * Get the latest health status for each service.
 */
export async function getLatestHealthStatus() {
  const services = ALL_PROBES.map((p) => p.name);

  const latest = await Promise.all(
    services.map(async (service) => {
      const check = await prisma.healthCheck.findFirst({
        where: { service },
        orderBy: { checkedAt: "desc" },
      });
      return check;
    })
  );

  return latest.filter(Boolean);
}

/**
 * Get 30-day health history for a specific service (for the tracker component).
 */
export async function getServiceHistory(service: string, days = 30) {
  const since = new Date(Date.now() - days * 24 * 60 * 60 * 1000);

  const checks = await prisma.healthCheck.findMany({
    where: { service, checkedAt: { gte: since } },
    orderBy: { checkedAt: "asc" },
    select: { status: true, latencyMs: true, checkedAt: true, message: true },
  });

  return checks;
}

/**
 * Get full dashboard data: latest status + history for all services.
 */
export async function getHealthDashboard() {
  const latest = await getLatestHealthStatus();
  const services = ALL_PROBES.map((p) => p.name);

  const historyMap: Record<string, any[]> = {};
  for (const service of services) {
    historyMap[service] = await getServiceHistory(service);
  }

  return {
    services: ALL_PROBES.map((p) => {
      const check = latest.find((c) => c?.service === p.name);
      return {
        id: p.name,
        name: SERVICE_DISPLAY_NAMES[p.name] || p.name,
        region: SERVICE_REGIONS[p.name] || "Cloud",
        status: check?.status || "unknown",
        latencyMs: check?.latencyMs || null,
        message: check?.message || "No data yet",
        lastChecked: check?.checkedAt || null,
        history: historyMap[p.name] || [],
      };
    }),
    timestamp: new Date().toISOString(),
  };
}

// Display names mapping
const SERVICE_DISPLAY_NAMES: Record<string, string> = {
  database: "PostgreSQL Database",
  redis: "Redis Cache & Sessions",
  binance_api: "Binance Exchange API",
  januar_fiat: "Januar Fiat Gateway",
  facilitapay_fiat: "FacilitaPay Gateway",
  didit_kyc: "Didit KYC Provider",
  bullmq_workers: "BullMQ Job Workers",
  api_server: "0core API Server",
  websocket_bridge: "WebSocket Bridge",
};

const SERVICE_REGIONS: Record<string, string> = {
  database: "Tokyo VPS",
  redis: "Tokyo VPS",
  binance_api: "Binance Cloud",
  januar_fiat: "Januar EU",
  facilitapay_fiat: "FacilitaPay LATAM",
  didit_kyc: "Didit Cloud",
  bullmq_workers: "Tokyo VPS",
  api_server: "Tokyo VPS",
  websocket_bridge: "Tokyo VPS",
};
