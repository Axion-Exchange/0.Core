/**
 * Operations Router Extension — Feature Flags, Risk Scores, Real-time P&L
 * 
 * These routes extend the operations module with institutional-grade
 * observability and control plane capabilities.
 */

import { Router, Request, Response } from "express";
import { featureFlags } from "../services/feature-flags.service.js";
import { scoreAllCounterparties, getCounterpartyRisk } from "../services/counterparty-risk.service.js";
import { getPnLSnapshot } from "../services/pnl-realtime.service.js";
import { createLogger } from "../lib/logger.js";

const log = createLogger("ops-ext-router");

export const opsExtRouter = Router();

// ── Feature Flags ────────────────────────────────────────────────────────────

/** GET /operations/flags — List all feature flags */
opsExtRouter.get("/flags", async (_req: Request, res: Response) => {
  try {
    const flags = await featureFlags.getAllFlags();
    res.json({ success: true, data: flags });
  } catch (err) {
    res.status(500).json({ success: false, error: (err as Error).message });
  }
});

/** PUT /operations/flags/:name — Toggle a feature flag */
opsExtRouter.put("/flags/:name", async (req: Request, res: Response) => {
  try {
    const name = req.params.name as string;
    const { enabled } = req.body;
    if (typeof enabled !== "boolean") {
      res.status(400).json({ success: false, error: "enabled must be boolean" });
      return;
    }
    const admin = (req as any).admin?.sub || "unknown";
    await featureFlags.setFlag(name, enabled, admin);
    log.warn(`[Flags] ${name} => ${enabled} by ${admin}`);
    res.json({ success: true, data: { name, enabled } });
  } catch (err) {
    res.status(500).json({ success: false, error: (err as Error).message });
  }
});

// ── Counterparty Risk ────────────────────────────────────────────────────────

/** GET /operations/risk/counterparties — Score all counterparties */
opsExtRouter.get("/risk/counterparties", async (_req: Request, res: Response) => {
  try {
    const risks = await scoreAllCounterparties();
    res.json({
      success: true,
      data: {
        total: risks.length,
        critical: risks.filter(r => r.riskLevel === "critical").length,
        high: risks.filter(r => r.riskLevel === "high").length,
        medium: risks.filter(r => r.riskLevel === "medium").length,
        low: risks.filter(r => r.riskLevel === "low").length,
        counterparties: risks.sort((a, b) => b.riskScore - a.riskScore),
      },
    });
  } catch (err) {
    res.status(500).json({ success: false, error: (err as Error).message });
  }
});

/** GET /operations/risk/counterparties/:nickname — Single counterparty risk */
opsExtRouter.get("/risk/counterparties/:nickname", async (req: Request, res: Response) => {
  try {
    const risk = await getCounterpartyRisk(req.params.nickname as string);
    if (!risk) {
      res.status(404).json({ success: false, error: "Counterparty not found" });
      return;
    }
    res.json({ success: true, data: risk });
  } catch (err) {
    res.status(500).json({ success: false, error: (err as Error).message });
  }
});

// ── Real-Time P&L ────────────────────────────────────────────────────────────

/** GET /operations/pnl/live — REST fallback for real-time P&L */
opsExtRouter.get("/pnl/live", async (_req: Request, res: Response) => {
  try {
    const pnl = await getPnLSnapshot();
    res.json({ success: true, data: pnl });
  } catch (err) {
    res.status(500).json({ success: false, error: (err as Error).message });
  }
});
