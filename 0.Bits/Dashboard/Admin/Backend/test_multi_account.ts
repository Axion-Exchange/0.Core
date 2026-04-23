import { prisma } from './src/lib/db.js';
import { binanceService } from './src/services/binance.service.js';

async function test() {
  const accounts = await prisma.p2PAccount.findMany({
    where: { isActive: true }
  });
  console.log(`Found ${accounts.length} active accounts.`);
  
  for (const acc of accounts) {
    console.log(`Testing account ID: ${acc.id} (${acc.label})`);
    const { enabled, client, rsaPem } = binanceService.getClient(acc);
    console.log(`Enabled: ${enabled}`);
    console.log(`Client exists: ${!!client}`);
    console.log(`Is RSA: ${!!rsaPem}`);
  }
}

test().catch(console.error).finally(() => prisma.$disconnect());
