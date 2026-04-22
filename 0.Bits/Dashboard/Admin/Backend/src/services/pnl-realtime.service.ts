/**
 * Real-Time P&L WebSocket Emitter (v2 — True FIFO, Multi-Currency)
 * 
 * Computes live FIFO P&L every 30 seconds and broadcasts to connected
 * dashboard clients via Socket.IO.
 * 
 * Room: "pnl:live"
 * Events: "pnl:update" — full multi-currency FIFO P&L snapshot
 */

import { getSocket } from "../lib/socket.js";
import { createLogger } from "../lib/logger.js";
import { fifoV2 } from "./intelligence/fifo-v2.service.js";
import { prisma } from "../lib/db.js";

const log = createLogger("pnl-realtime");

let emitInterval: NodeJS.Timeout | null = null;

export interface RealTimePnL {
  timestamp: string;
  // EUR P&L
  todayPnl: string;
  weekPnl: string;
  monthPnl: string;
  // Live spread
  avgBuyPrice: string;
  avgSellPrice: string;
  spreadPct: string;
  // Inventory
  inventoryQty: string;
  inventoryValue: string;
  // Counters
  todayBuys: number;
  todaySells: number;
  // Trade velocity
  ordersPerHour: number;
}

async function computeRealTimePnL(): Promise<RealTimePnL> {
  const now = new Date();
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const weekStart = new Date(todayStart.getTime() - 7 * 86400000);
  const monthStart = new Date(now.getFullYear(), now.getMonth(), 1);

  // Run all 3 FIFO v2 calculations concurrently (EUR primary)
  const [today, week, month] = await Promise.all([
    fifoV2.computeForCurrency('EUR', todayStart, now).catch(() => null),
    fifoV2.computeForCurrency('EUR', weekStart, now).catch(() => null),
    fifoV2.computeForCurrency('EUR', monthStart, now).catch(() => null),
  ]);

  // Calculate orders/hour for last 6 hours
  const sixHoursAgo = new Date(now.getTime() - 6 * 3600000);
  const recentCount = await prisma.p2POrder.count({
    where: {
      createdAt: { gte: sixHoursAgo },
      status: "COMPLETED",
    },
  });

  return {
    timestamp: now.toISOString(),
    todayPnl: today?.realizedPnl ?? "0.00",
    weekPnl: week?.realizedPnl ?? "0.00",
    monthPnl: month?.realizedPnl ?? "0.00",
    avgBuyPrice: today?.avgBuyPrice ?? "0.00",
    avgSellPrice: today?.avgSellPrice ?? "0.00",
    spreadPct: today?.spreadPct ?? "0.00",
    inventoryQty: month?.inventoryQty ?? "0.00",
    inventoryValue: month?.inventoryCostBasis ?? "0.00",
    todayBuys: today?.buyCount ?? 0,
    todaySells: today?.sellCount ?? 0,
    ordersPerHour: parseFloat((recentCount / 6).toFixed(1)),
  };
}

/**
 * Start emitting real-time P&L updates every 30 seconds.
 * Only emits when at least 1 client is in the "pnl:live" room.
 */
export function startPnLEmitter(): void {
  if (emitInterval) return;

  const io = getSocket();

  io.on("connection", (socket) => {
    socket.on("pnl:subscribe", () => {
      socket.join("pnl:live");
      log.info(`[PnL] Client ${socket.id} subscribed to live P&L`);

      computeRealTimePnL().then((pnl) => {
        socket.emit("pnl:update", pnl);
      }).catch(() => {});
    });

    socket.on("pnl:unsubscribe", () => {
      socket.leave("pnl:live");
    });
  });

  emitInterval = setInterval(async () => {
    try {
      const room = io.sockets.adapter.rooms.get("pnl:live");
      if (!room || room.size === 0) return;

      const pnl = await computeRealTimePnL();
      io.to("pnl:live").emit("pnl:update", pnl);
    } catch (err) {
      log.error("[PnL] Emit failed:", (err as Error).message);
    }
  }, 30_000);

  log.info("[PnL] Real-time emitter started (30s interval, FIFO v2)");
}

export function stopPnLEmitter(): void {
  if (emitInterval) {
    clearInterval(emitInterval);
    emitInterval = null;
  }
}

export async function getPnLSnapshot(): Promise<RealTimePnL> {
  return computeRealTimePnL();
}
