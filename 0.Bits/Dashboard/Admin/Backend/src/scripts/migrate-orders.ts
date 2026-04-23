import { prisma } from '../lib/db.js';

async function main() {
  const marwanAccount = await prisma.p2PAccount.findFirst({
    where: { label: 'Binance Marwan Yousif' }
  });
  
  if (marwanAccount) {
    const updated = await prisma.p2POrder.updateMany({
      where: { accountId: null },
      data: { accountId: marwanAccount.id }
    });
    console.log(`Migrated ${updated.count} orders to Binance Marwan Yousif`);
  }
}

main().catch(console.error);
