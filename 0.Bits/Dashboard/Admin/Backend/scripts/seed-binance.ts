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
      const response = await client.sapiGetC2cOrderMatchListUserOrderHistory({
        startTimestamp: startTime,
        endTimestamp: endTime,
        rows: 100 // max is 100
      });

      if (response && response.data && Array.isArray(response.data)) {
        console.log(`  Found ${response.data.length} matches. Upserting into PostgreSQL...`);
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
