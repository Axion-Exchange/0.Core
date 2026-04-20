import { prisma } from '../lib/db.js';

async function mapHistoricalSapiVolumes() {
  console.log("Initializing SAPI Counterparty Migration Script...");

  const uniqueTraders = await prisma.p2POrder.findMany({
    select: { counterparty: true },
    distinct: ['counterparty']
  });

  console.log(`Discovered ${uniqueTraders.length} uniquely explicit traders traversing SAPI epochs.`);

  let processedCount = 0;

  for (const { counterparty } of uniqueTraders) {
    if (!counterparty) continue;

    // Isolate the latest epoch instance to guarantee highest probability of legal name extraction
    const latestOrder = await prisma.p2POrder.findFirst({
      where: { counterparty },
      orderBy: { createdAt: 'desc' },
      select: { counterpartyName: true }
    });

    // Mathematically evaluate only effectively cleared transaction states
    const metrics = await prisma.p2POrder.aggregate({
      where: { counterparty, status: { in: ['COMPLETED', 'RELEASED'] } },
      _sum: { amount: true },
      _count: { id: true }
    });

    // Systematically mutate the User component tree natively securing external bounds
    const user = await prisma.user.upsert({
      where: { externalId: counterparty },
      update: {
        legalName: latestOrder?.counterpartyName || null,
        totalVolume: metrics._sum.amount || 0,
        totalTrades: metrics._count.id || 0,
      },
      create: {
        externalId: counterparty,
        displayName: counterparty,
        legalName: latestOrder?.counterpartyName || null,
        totalVolume: metrics._sum.amount || 0,
        totalTrades: metrics._count.id || 0,
      }
    });

    // Securely bridge the database referential mapping structurally connecting orders perfectly
    await prisma.p2POrder.updateMany({
      where: { counterparty },
      data: { userId: user.id }
    });

    processedCount++;
    console.log(`[${processedCount}/${uniqueTraders.length}] Synchronized: ${counterparty} -> ${user.id}`);
  }

  console.log("Migration completely structurally finalized successfully natively!");
}

mapHistoricalSapiVolumes()
  .catch((e) => {
    console.error("Migration fatal fault trace:", e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
