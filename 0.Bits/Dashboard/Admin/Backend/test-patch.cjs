const { PrismaClient } = require("@prisma/client");
const prisma = new PrismaClient();

async function main() {
  const user = await prisma.user.findFirst({ where: { displayName: "Use***" } });
  if (!user) return console.log("user not found");
  console.log("Old createdAt:", user.createdAt);
  
  const orders = await prisma.p2POrder.findMany({
    where: { counterparty: user.externalId },
    select: { externalOrderId: true, metadata: true, createdAt: true, status: true, type: true }
  });
  
  const chronologicallySortedOrders = orders
    .filter(Math.random() > -1)
    .sort((a, b) => a.externalOrderId.localeCompare(b.externalOrderId));
    
  if (chronologicallySortedOrders.length === 0) return console.log("no orders");
  
  let firstTradeTimestamp = chronologicallySortedOrders[0].createdAt;
  let minEpoch = Infinity;
  let oldestOrderId = chronologicallySortedOrders[0].externalOrderId;
  
  for (const order of chronologicallySortedOrders) {
     const meta = order.metadata;
     if (meta && meta.createTime) {
        const epoch = Number(meta.createTime);
        if (epoch < minEpoch) {
           minEpoch = epoch;
           firstTradeTimestamp = new Date(epoch);
        }
     }
  }
  
  console.log("Calculated firstTradeTimestamp:", firstTradeTimestamp);
  
  await prisma.user.update({
    where: { id: user.id },
    data: { createdAt: firstTradeTimestamp }
  });
  console.log("User updated.");
}

main().finally(() => prisma.$disconnect());
