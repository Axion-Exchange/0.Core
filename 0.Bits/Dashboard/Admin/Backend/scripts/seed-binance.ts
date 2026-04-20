import { prisma } from '../src/lib/db.js';
import { binanceService } from '../src/services/binance.service.js';
import { AdType, OrderStatus } from '@prisma/client';

async function seedBinanceHistory() {
  console.log('Initiating 6-month historical Database Archive for Binance P2P...');
  if (!binanceService['enabled']) {
    console.error('Binance keys missing. Aborting seed.');
    process.exit(1);
  }

  const client = (binanceService as any).client;

  // Binance limits c2c history queries, often requiring 30-day windows.
  // We will loop across the last 6 months in 25-day sliding windows.
  let endTime = Date.now();
  const windowMs = 25 * 24 * 60 * 60 * 1000; 
  let totalArchived = 0;

  for (let i = 0; i < 7; i++) { // roughly 175 days
    const startTime = endTime - windowMs;
    console.log(`[Window ${i+1}/7] Indexing SAPI ${new Date(startTime).toISOString()} -> ${new Date(endTime).toISOString()}`);

    try {
      let page = 1;
      let hasMore = true;

      while (hasMore) {
        const response: any = await client.sapiGetC2cOrderMatchListUserOrderHistory({
          startTimestamp: startTime,
          endTimestamp: endTime,
          page: page,
          rows: 100 // Binance natively caps to 100
        });

        if (response && response.data && Array.isArray(response.data) && response.data.length > 0) {
          const batchSize = response.data.length;
          console.log(`  [Page ${page}] Found ${batchSize} matches. Upserting into PostgreSQL...`);
          
          for (const order of response.data) {
            let mappedStatus: OrderStatus = OrderStatus.PENDING_FIAT;
            if (order.orderStatus === 'COMPLETED') mappedStatus = OrderStatus.COMPLETED;
            else if (order.orderStatus === 'CANCELLED' || order.orderStatus === 'CANCELLED_BY_SYSTEM') mappedStatus = OrderStatus.CANCELLED;

            const createTime = new Date(Number(order.createTime));
            await prisma.p2POrder.upsert({
              where: { externalOrderId: order.orderNumber },
              create: {
                externalOrderId: order.orderNumber,
                asset: order.asset, 
                fiat: order.fiat, 
                amount: parseFloat(order.amount) || 0,
                fiatAmount: parseFloat(order.totalPrice) || 0,
                price: parseFloat(order.unitPrice) || 0,
                type: order.tradeType === 'BUY' ? AdType.BUY : AdType.SELL, 
                counterparty: order.counterPartNickName || 'Binance P2P User',
                paymentMethod: order.payMethodName,
                status: mappedStatus,
                createdAt: createTime,
                completedAt: mappedStatus === OrderStatus.COMPLETED ? createTime : null, 
                metadata: order, 
              },
              update: {
                status: mappedStatus,
                metadata: order,
              }
            });
            totalArchived++;
          }

          if (batchSize < 50) {
            hasMore = false; // Exhausted window natively, Binance max array return is ~50
          } else {
            page++;
          }
          await new Promise(r => setTimeout(r, 600)); // strict rate limit pacing
        } else {
          hasMore = false; // Graceful exit
        }
      }
    } catch (e: any) {
      console.error(`  Warning: Window API failed: `, e.message);
    }
    
    endTime = startTime;
    // Delay 1 second to respect Binance IP constraints securely
    await new Promise(r => setTimeout(r, 1000));
  }

  console.log(`\n======================================\n`);
  console.log(`✅ DATABASE SYNCHRONIZATION COMPLETE!`);
  console.log(`📦 Accurately archived ${totalArchived} immutable historical trades inside PostgreSQL!`);
  console.log(`\n======================================\n`);
  process.exit(0);
}

seedBinanceHistory();
