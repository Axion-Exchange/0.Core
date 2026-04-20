import { prisma } from '../lib/db.js';

async function mapHistoricalSapiVolumes() {
  console.log("Initializing SAPI Counterparty Patch Script...");

  const users = await prisma.user.findMany({
    where: { externalId: { not: null } }
  });

  console.log(`Discovered ${users.length} uniquely explicit traders traversing SAPI epochs.`);

  let processedCount = 0;

  for (const user of users) {
    if (!user.externalId) continue;

    const orders = await prisma.p2POrder.findMany({
      where: { counterparty: user.externalId },
      orderBy: { createdAt: 'asc' },
      select: { counterpartyName: true, createTime: true, createdAt: true }
    });

    if (orders.length === 0) continue;

    // Intelligently trap the earliest explicit order execution timestamp spanning P2P lifecycle
    const firstTradeTimestamp = orders[0].createTime ? new Date(Number(orders[0].createTime)) : orders[0].createdAt;

    // Scan precisely for the unmasked true legal Name avoiding API boundary masks systematically
    let actualName = user.legalName || "";
    for (const order of orders) {
      if (order.counterpartyName && !order.counterpartyName.includes('*')) {
        // Only accept if it mathematically increases accuracy
        if (order.counterpartyName.length > actualName.length) {
            actualName = order.counterpartyName;
        }
      }
    }

    // Systematically mutate the User component natively securing external bounds
    await prisma.user.update({
      where: { id: user.id },
      data: {
        legalName: actualName || null,
        createdAt: firstTradeTimestamp,
      }
    });

    processedCount++;
    if (processedCount % 100 === 0) {
      console.log(`[${processedCount}/${users.length}] Patched: ${user.externalId}`);
    }
  }

  console.log("Patch completely structurally finalized successfully natively!");
}

mapHistoricalSapiVolumes()
  .catch((e) => {
    console.error("Migration fatal fault trace:", e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
