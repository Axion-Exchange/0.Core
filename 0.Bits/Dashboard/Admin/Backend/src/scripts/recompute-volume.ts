import { PrismaClient } from '@prisma/client';
import { createLogger } from '../lib/logger.js';

const prisma = new PrismaClient();
const log = createLogger('volume-recompute');

async function recompute() {
  log.info('Initializing P2P Pseudonym Separation Engine...');

  // 1. Identify all fake aggregated Users
  const fakeUsers = await prisma.user.findMany({
    where: { externalId: { contains: '***' } },
    include: { orders: true }
  });

  log.info(`Found ${fakeUsers.length} incorrectly clustered masking accounts.`);

  let separatedCount = 0;

  for (const fakeUser of fakeUsers) {
    if (fakeUser.orders.length > 1) {
       log.info(`Shattering Cluster: ${fakeUser.externalId} -> ${fakeUser.orders.length} unique orders.`);
       // Detach each order into a purely isolated mathematical entity
       for (const order of fakeUser.orders) {
          // Create pristine isolated user
          const newIsolatedUser = await prisma.user.create({
             data: {
               // We append the order ID so it's technically pseudo-unique avoiding collision temporarily
               externalId: `${fakeUser.externalId}-${order.externalOrderId || order.id}`,
               displayName: fakeUser.displayName,
               legalName: null, // Wipe structurally false inheritances elegantly securely!
               totalVolume: order.status === 'COMPLETED' ? order.amount : 0,
               totalTrades: order.status === 'COMPLETED' ? 1 : 0,
               createdAt: order.createdAt
             }
          });
          // Transfer relational entity safely
          await prisma.p2POrder.update({
             where: { id: order.id },
             data: { userId: newIsolatedUser.id }
          });
          separatedCount++;
       }
       
       // Wipe the original massively aggregated generic ghost safely!
       await prisma.user.delete({ where: { id: fakeUser.id } });
    } else {
       // It only has 1 order, so its volume is naturally mathematically cleanly matched!
       if (fakeUser.orders.length === 1) {
          const o = fakeUser.orders[0];
          await prisma.user.update({
             where: { id: fakeUser.id },
             data: {
                totalVolume: o!.status === 'COMPLETED' ? o!.amount : 0,
                totalTrades: o!.status === 'COMPLETED' ? 1 : 0
             }
          });
       }
    }
  }

  log.info(`Separated ${separatedCount} trades natively! Commencing Real Name Grouping Scan...`);

  // 2. Perform Native Real-Name Groupings natively
  // Many users might share the identical legalName. We should safely merge them into a single User natively retaining true totals!
  const allUsersWithRealNames = await prisma.user.findMany({
    where: { 
       legalName: { not: null },
       externalId: { not: { contains: '***' } }
    },
    include: { orders: true }
  });

  // Group mathematically natively
  const groupedByRealName: Record<string, typeof allUsersWithRealNames> = {};
  for (const u of allUsersWithRealNames) {
     if (!u.legalName) continue;
     const normalized = u.legalName.trim().toUpperCase();
     if (!groupedByRealName[normalized]) groupedByRealName[normalized] = [];
     groupedByRealName[normalized].push(u);
  }

  let mergedCount = 0;

  for (const [realName, duplicates] of Object.entries(groupedByRealName)) {
     if (duplicates.length > 1) {
        log.info(`Merging ${duplicates.length} accounts mathematically resolving under true identity: ${realName}`);
        
        // Pick absolute oldest identity organically as Master identity safely
        const master: any = duplicates.sort((a,b) => a.createdAt.getTime() - b.createdAt.getTime())[0];
        const slaves = duplicates.filter(d => d.id !== master.id);

        let mergedVolume = Number(master.totalVolume);
        let mergedTrades = master.totalTrades;

        for (const slave of slaves) {
           for (const o of slave.orders) {
               await prisma.p2POrder.update({
                  where: { id: o.id },
                  data: { userId: master.id }
               });
               if (o!.status === 'COMPLETED') {
                  mergedVolume += Number(o!.amount);
                  mergedTrades += 1;
               }
           }
           await prisma.user.delete({ where: { id: slave.id } });
           mergedCount++;
        }

        await prisma.user.update({
            where: { id: master.id },
            data: { 
               totalVolume: mergedVolume,
               totalTrades: mergedTrades
            }
        });
     }
  }

  log.info(`Successfully seamlessly securely dynamically processed and fully mathematically merged ${mergedCount} valid true-name profiles!`);
}

recompute().catch(console.error).finally(() => prisma.$disconnect());
