import { PrismaClient } from "@prisma/client";
const prisma = new PrismaClient();
async function main() {
  const users = await prisma.user.findMany({ 
     where: { externalId: { not: null } },
     orderBy: { totalVolume: "desc" },
     take: 1
  });
  if (users.length === 0) return console.log("User not found");
  
  console.log("User:", users[0].legalName || users[0].displayName);
  
  const o = await prisma.p2POrder.findMany({ 
    where: { counterparty: users[0].externalId }, 
    orderBy: { externalOrderId: "asc" },
    take: 2
  });
  console.log(JSON.stringify(o, null, 2));
}
main().finally(() => prisma.$disconnect());
