import { PrismaClient } from "@prisma/client";
const p = new PrismaClient();

async function readOrderChat(nameFilter: string, label: string) {
  const order = await p.p2POrder.findFirst({
    where: { counterpartyName: { contains: nameFilter } },
    select: { id: true, counterpartyName: true, amount: true, fiat: true, externalOrderId: true, createdAt: true, status: true },
  });
  if (!order) { console.log(`\nNo order for: ${nameFilter}`); return; }

  const msgs = await p.p2PChatMessage.findMany({
    where: { orderId: order.id },
    orderBy: { timestamp: "asc" },
  });

  console.log(`\n${"=".repeat(80)}`);
  console.log(`ORDER: ${order.counterpartyName}`);
  console.log(`  Amount: ${order.amount} ${order.fiat} | Status: ${order.status} | Date: ${order.createdAt.toISOString().substring(0,10)}`);
  console.log(`  Third-party label: ${label}`);
  console.log(`${"=".repeat(80)}`);
  for (const msg of msgs) {
    const time = msg.timestamp.toISOString().substring(11, 16);
    const who = (msg.sender || "system").padEnd(8);
    const text = msg.content.replace(/\n/g, " ").substring(0, 250);
    const flag = text.includes("@") || text.includes("verify.didit") ? " <<< EMAIL/LINK" : "";
    console.log(`  [${time}] ${who}| ${text}${flag}`);
  }
}

async function main() {
  await readOrderChat("KEVIN MARCEL", "Ali Sall (APPROVED, FRA)");
  await readOrderChat("CALDERA BARRETO", "Abdul Wahid Opu (DECLINED, PRT)");
  await readOrderChat("MARIN LEON", "Geraldine Margaret Cardenas (ABANDONED)");
  await readOrderChat("Reagan", "OGAGA (DECLINED, USA)");
  await readOrderChat("NILUFA", "Shafiull Kaysar Simon (DECLINED, PRT)");

  // Arabic name - find by email in chat
  const arabicMsg = await p.p2PChatMessage.findFirst({
    where: { content: { contains: "i.tsvetov" } },
  });
  if (arabicMsg) {
    const order = await p.p2POrder.findUnique({
      where: { id: arabicMsg.orderId },
      select: { id: true, counterpartyName: true, amount: true, fiat: true, createdAt: true, status: true },
    });
    if (order) {
      const msgs = await p.p2PChatMessage.findMany({
        where: { orderId: order.id },
        orderBy: { timestamp: "asc" },
      });
      console.log(`\n${"=".repeat(80)}`);
      console.log(`ORDER: ${order.counterpartyName}`);
      console.log(`  Amount: ${order.amount} ${order.fiat} | Status: ${order.status} | Date: ${order.createdAt.toISOString().substring(0,10)}`);
      console.log(`  Third-party label: Ivan Tsvetov Ivanov (APPROVED, BGR)`);
      console.log(`${"=".repeat(80)}`);
      for (const msg of msgs) {
        const time = msg.timestamp.toISOString().substring(11, 16);
        const who = (msg.sender || "system").padEnd(8);
        const text = msg.content.replace(/\n/g, " ").substring(0, 250);
        const flag = text.includes("@") || text.includes("verify.didit") ? " <<< EMAIL/LINK" : "";
        console.log(`  [${time}] ${who}| ${text}${flag}`);
      }
    }
  }

  await p.$disconnect();
}
main();
