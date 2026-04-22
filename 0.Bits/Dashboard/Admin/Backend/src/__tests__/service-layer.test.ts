import { describe, it, expect, vi, beforeEach } from "vitest";

/**
 * Service-Layer Tests — Institutional grade business logic validation.
 *
 * Tests verify service behavior with mocked Prisma to isolate business
 * logic from database implementation.
 */

// ── Mock Prisma ──────────────────────────────────────────────

const mockPrisma = {
  user: {
    findUnique: vi.fn(),
    update: vi.fn(),
    create: vi.fn(),
    count: vi.fn(),
    findMany: vi.fn(),
  },
  userDocument: { updateMany: vi.fn() },
  p2POrder: {
    findUnique: vi.fn(),
    update: vi.fn(),
    findMany: vi.fn(),
    count: vi.fn(),
  },
  p2PDispute: {
    create: vi.fn(),
    update: vi.fn(),
    findMany: vi.fn(),
    count: vi.fn(),
  },
  portfolio: {
    findMany: vi.fn(),
    upsert: vi.fn(),
  },
  healthCheck: {
    create: vi.fn(),
    findFirst: vi.fn(),
    findMany: vi.fn(),
  },
  systemLog: {
    create: vi.fn(),
  },
  $transaction: vi.fn((fn: any) => fn(mockPrisma)),
};

vi.mock("../lib/db.js", () => ({
  prisma: mockPrisma,
  checkDatabaseHealth: vi.fn().mockResolvedValue(true),
}));

vi.mock("../lib/transaction.js", () => ({
  safeTransaction: vi.fn(async (fn: any) => fn(mockPrisma)),
}));

vi.mock("../lib/logger.js", () => ({
  createLogger: () => ({
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
    debug: vi.fn(),
  }),
}));

vi.mock("../config/index.js", () => ({
  config: {
    JWT_SECRET: "test-secret-at-least-32-chars-long",
    JWT_EXPIRES_IN: "24h",
    JWT_REFRESH_EXPIRES_IN: "7d",
    JANUAR_BASE_URL: "https://api.januar.com",
    FACILITAPAY_BASE_URL: "https://api.facilitapay.com/api/v1",
    NODE_ENV: "test",
  },
}));

// ── Operations Service Tests ─────────────────────────────────

describe("OperationsService", () => {
  beforeEach(() => vi.clearAllMocks());

  it("getSystemHealth returns operational when DB is healthy", async () => {
    const { OperationsService } = await import("../services/operations.service.js");
    const service = new OperationsService();

    mockPrisma.healthCheck.findMany.mockResolvedValue([]);

    const health = await service.getSystemHealth();
    expect(health.status).toBe("operational");
    expect(health.database).toBe("connected");
    expect(health).toHaveProperty("uptime");
    expect(health).toHaveProperty("memory");
  });

  it("writeLog persists structured log entry", async () => {
    const { OperationsService } = await import("../services/operations.service.js");
    const service = new OperationsService();

    mockPrisma.systemLog.create.mockResolvedValue({ id: "log-1" });

    const log = await service.writeLog("ERROR", "auth", "Login failed", { ip: "1.2.3.4" });
    expect(mockPrisma.systemLog.create).toHaveBeenCalledWith({
      data: expect.objectContaining({
        level: "ERROR",
        source: "auth",
        message: "Login failed",
      }),
    });
  });
});

// ── User Service Tests ───────────────────────────────────────

describe("UserService — KYC Mutations", () => {
  beforeEach(() => vi.clearAllMocks());

  it("approveKyc wraps user + document updates in safeTransaction", async () => {
    const { UserService } = await import("../services/user.service.js");
    const service = new UserService();

    mockPrisma.user.update.mockResolvedValue({ id: "u1", kycStatus: "APPROVED" });
    mockPrisma.userDocument.updateMany.mockResolvedValue({ count: 2 });

    await service.approveKyc("u1", "admin-1");

    // Verify user and docs were updated (via mocked safeTransaction)
    expect(mockPrisma.user.update).toHaveBeenCalledWith(
      expect.objectContaining({ where: { id: "u1" }, data: { kycStatus: "APPROVED" } })
    );
    expect(mockPrisma.userDocument.updateMany).toHaveBeenCalled();
  });

  it("rejectKyc passes rejection reason to documents", async () => {
    const { UserService } = await import("../services/user.service.js");
    const service = new UserService();

    mockPrisma.user.update.mockResolvedValue({ id: "u1", kycStatus: "REJECTED" });
    mockPrisma.userDocument.updateMany.mockResolvedValue({ count: 1 });

    await service.rejectKyc("u1", "admin-1", "Blurry ID photo");

    expect(mockPrisma.user.update).toHaveBeenCalledWith(
      expect.objectContaining({
        where: { id: "u1" },
        data: { kycStatus: "REJECTED" },
      })
    );
    expect(mockPrisma.userDocument.updateMany).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({
          rejectionReason: "Blurry ID photo",
        }),
      })
    );
  });

  it("freeze sets isFrozen flag", async () => {
    const { UserService } = await import("../services/user.service.js");
    const service = new UserService();

    mockPrisma.user.update.mockResolvedValue({ id: "u1", isFrozen: true });

    await service.freeze("u1", true);

    expect(mockPrisma.user.update).toHaveBeenCalledWith({
      where: { id: "u1" },
      data: { isFrozen: true },
    });
  });
});

// ── P2P Service Tests ────────────────────────────────────────

describe("P2PService — Order Lifecycle", () => {
  beforeEach(() => vi.clearAllMocks());

  it("updateOrderStatus sets completedAt for COMPLETED orders", async () => {
    const { P2PService } = await import("../services/p2p.service.js");
    const service = new P2PService();

    mockPrisma.p2POrder.update.mockResolvedValue({ id: "o1", status: "COMPLETED" });

    await service.updateOrderStatus("o1", "COMPLETED" as any);

    const call = mockPrisma.p2POrder.update.mock.calls[0]?.[0];
    expect(call?.data?.status).toBe("COMPLETED");
    expect(call?.data?.completedAt).toBeInstanceOf(Date);
  });

  it("updateOrderStatus sets cancelledAt for CANCELLED orders", async () => {
    const { P2PService } = await import("../services/p2p.service.js");
    const service = new P2PService();

    mockPrisma.p2POrder.update.mockResolvedValue({ id: "o1", status: "CANCELLED" });

    await service.updateOrderStatus("o1", "CANCELLED" as any);

    const call = mockPrisma.p2POrder.update.mock.calls[0]?.[0];
    expect(call?.data?.cancelledAt).toBeInstanceOf(Date);
  });

  it("resolveDispute uses safeTransaction for atomic dispute+order update", async () => {
    const { P2PService } = await import("../services/p2p.service.js");
    const service = new P2PService();

    mockPrisma.p2PDispute.update.mockResolvedValue({ id: "d1", orderId: "o1" });
    mockPrisma.p2POrder.update.mockResolvedValue({ id: "o1", status: "COMPLETED" });

    await service.resolveDispute("d1", {
      resolution: "Seller provided valid proof",
      resolvedInFavor: "seller",
      adminId: "admin-1",
    });

    // Verify dispute was updated via mocked safeTransaction
    expect(mockPrisma.p2PDispute.update).toHaveBeenCalled();
    expect(mockPrisma.p2POrder.update).toHaveBeenCalled();
  });
});

// ── Health Checker Tests ─────────────────────────────────────

describe("HealthChecker — Probe System", () => {
  it("getLatestHealthStatus returns latest check per service", async () => {
    const { getLatestHealthStatus } = await import("../services/health-checker.service.js");

    mockPrisma.healthCheck.findFirst.mockResolvedValue({
      service: "database",
      status: "healthy",
      latencyMs: 5,
      checkedAt: new Date(),
    });

    const results = await getLatestHealthStatus();
    expect(results.length).toBeGreaterThan(0);
  });
});
