import { PrismaClient } from "@prisma/client";
const prisma = new PrismaClient();

async function main() {
  const user = await prisma.user.findFirst({ where: { email: { equals: "youyoussef2005@gmail.com", mode: "insensitive" } } });
  if (!user) {
    console.log("User not found.");
    return;
  }

  const pool = await prisma.pool.findFirst({ where: { name: "USDT/EUR" } });
  if (!pool) {
    console.log("Pool not found: USDT/EUR");
    return;
  }

  const depositDate = new Date("2026-03-20T13:30:00Z");
  const amount = 11573;

  // Create completed Transaction
  const tx = await prisma.transaction.create({
    data: {
      userId: user.id,
      poolId: pool.id,
      type: "DEPOSIT",
      amount: amount,
      currency: "EUR",
      status: "COMPLETED",
      reference: "AX-" + Math.random().toString(36).substring(2, 10).toUpperCase(),
      createdAt: depositDate,
      updatedAt: depositDate
    }
  });
  console.log(`Created TX: ${tx.id} at ${tx.createdAt}`);

  // Create Position
  const existingPos = await prisma.position.findFirst({
    where: { userId: user.id, poolId: pool.id }
  });

  if (existingPos) {
      await prisma.position.update({
          where: { id: existingPos.id },
          data: {
              investedAmount: { increment: amount },
              currentValue: { increment: amount }
          }
      });
      console.log("Updated Position");
  } else {
      await prisma.position.create({
          data: {
              userId: user.id,
              poolId: pool.id,
              status: "ACTIVE",
              investedAmount: amount,
              currentValue: amount,
              currency: "EUR",
              createdAt: depositDate,
              updatedAt: depositDate
          }
      });
      console.log("Created Position");
  }
}

main().then(() => prisma.$disconnect());
