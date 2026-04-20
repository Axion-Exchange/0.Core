import { prisma } from '../lib/db.js';
import { binanceService } from '../services/binance.service.js';

async function patchHistoricalSapiIdentities() {
  console.log("Initializing Deep SAPI Counterparty Patch Script with True Identity Resolvers...");

  const users = await prisma.user.findMany({
    where: { externalId: { not: null } }
  });

  console.log(`Discovered ${users.length} uniquely explicit traders traversing SAPI epochs.`);

  let processedCount = 0;

  for (const user of users) {
    if (!user.externalId) continue;

    // Get ALL orders to trace the exact chronological origin and select one payload for verification
    const orders = await prisma.p2POrder.findMany({
      where: { counterparty: user.externalId },
      orderBy: { createdAt: 'asc' },
      select: { externalOrderId: true, metadata: true, createdAt: true, status: true, type: true }
    });

    if (orders.length === 0) continue;

    // Safely aggressively find the true minimum chronological historical trade date primarily from JSON metadata payloads bypassing arbitrary Postgres migration sorting
    let firstTradeTimestamp = orders[0].createdAt;
    let minEpoch = Infinity;
    
    // First, scan local metadata to find the absolute oldest chronological ID natively
    let oldestOrderId: string | null = null;

    for (const order of orders) {
       const meta = order.metadata as any;
       if (meta && meta.createTime) {
          const epoch = Number(meta.createTime);
          if (epoch < minEpoch) {
             minEpoch = epoch;
             firstTradeTimestamp = new Date(epoch);
             oldestOrderId = order.externalOrderId;
          }
       }
    }
    
    if (!oldestOrderId && orders[0].externalOrderId) {
       oldestOrderId = orders[0].externalOrderId;
    }

    // Forcefully explicitly ping Binance SAPI against the oldest known valid ID strictly retrieving their literal first temporal origin bypassing the Database!
    if (oldestOrderId) {
       const historic = await binanceService.fetchTrueLegalName(oldestOrderId);
       if (historic && historic.createTime) {
          const apiEpoch = Number(historic.createTime);
          if (apiEpoch > 0) {
              firstTradeTimestamp = new Date(apiEpoch);
          }
       }
       // 250ms WAF delay
       await new Promise(r => setTimeout(r, 250));
    }

    // Clone array physically to prevent mutating original sort sequence if needed
    const sortedOrders = [...orders];

    // Find the latest order explicitly providing valid order mapping strings (preferably COMPLETED, fallback to ANY)
    let validTrade = sortedOrders.reverse().find(o => o.status === 'COMPLETED' && o.externalOrderId);
    if (!validTrade) validTrade = sortedOrders.find(o => o.externalOrderId);

    let actualName = user.legalName || "";

    // Explicitly ask Binance SAPI to mathematically unmask this specific user
    // SKIP physically if we already have an unmasked true identity to strictly save API Rate Limits!
    if (validTrade && validTrade.externalOrderId && (!actualName || actualName.includes('*'))) {
      const names = await binanceService.fetchTrueLegalName(validTrade.externalOrderId);
      if (names) {
         // The API maps true sender to buyer/seller dynamically
         actualName = validTrade.type === 'BUY' ? (names.sellerName || actualName) : (names.buyerName || actualName);
      }
      // Natively sleep for 250ms to strictly prevent Binance HTTP 429 WAF Rate Limits!
      await new Promise(r => setTimeout(r, 250));
    }

    // Systematically mutate the User component natively securing external bounds
    await prisma.user.update({
      where: { id: user.id },
      data: {
        ...(actualName ? { legalName: actualName } : {}), // Override masked string gracefully
        createdAt: firstTradeTimestamp,
      }
    });

    processedCount++;
    if (processedCount % 50 === 0) {
      console.log(`[${processedCount}/${users.length}] Patched: ${user.externalId} -> ${actualName || 'MASKED'} at ${firstTradeTimestamp}`);
    }
  }

  console.log("Deep Patch completely structurally finalized successfully natively!");
}

patchHistoricalSapiIdentities()
  .catch((e) => {
    console.error("Migration fatal fault trace:", e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
