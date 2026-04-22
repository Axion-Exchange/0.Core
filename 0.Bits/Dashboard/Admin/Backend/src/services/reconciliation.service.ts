import { parse } from 'csv-parse';
import { PrismaClient, OrderStatus, AdType } from '@prisma/client';
import fs from 'fs';
import { parse as dateParse } from 'date-fns';

const prisma = new PrismaClient();

export class ReconciliationService {
  /**
   * Processes a Binance P2P Order History CSV.
   * Explodes masked users and prevents volume double counting.
   */
  static async processCSV(filePath: string): Promise<any> {
    const results: any[] = [];
    const parser = fs.createReadStream(filePath).pipe(
      parse({
        columns: true,
        skip_empty_lines: true,
        trim: true,
      })
    );

    let processed = 0;
    let newlyInserted = 0;
    let explodedUsers = 0;

    for await (const record of parser) {
      processed++;
      
      // 1. Sanitize OrderNumber from any Excel formulas like '="123"' or pre-pended quotes
      const rawOrderNo = record['Order Number'];
      if (!rawOrderNo) continue;
      const orderNumber = String(rawOrderNo).replace(/[^0-9a-zA-Z-]/g, '');

      const orderTypeStr = record['Order Type']; // e.g., 'Buy' or 'Sell'
      const asset = record['Asset'];
      const fiat = record['Fiat'];
      const totalFiat = parseFloat(record['Total Price']);
      const price = parseFloat(record['Price']);
      const amount = parseFloat(record['Amount']);
      const counterpartyNickname = record['Counterparty'] || 'Unknown';
      const counterpartyRealName = record['Counterparty Real Name'] || null; // Sometimes available
      const statusStr = record['Status'];
      let createdTimeStr = record['Created Time'] || ''; // Format varying, e.g. "2025-10-27 10:00:00"

      if (!orderNumber || !amount || !fiat) {
        continue;
      }

      // Map AdType (From merchant perspective: If customer 'Buy', merchant 'SELL')
      // Note: Binance CSV "Order Type" is usually the merchant's direction in Merchant exports.
      const type: AdType = orderTypeStr?.toUpperCase().includes('BUY') ? AdType.BUY : AdType.SELL;

      // Map Status
      let status: OrderStatus = OrderStatus.PENDING_FIAT;
      const s = statusStr?.toUpperCase() || '';
      if (s.includes('COMPLETED')) status = OrderStatus.COMPLETED;
      else if (s.includes('CANCEL') || s.includes('CLOSED')) status = OrderStatus.CANCELLED;
      else if (s.includes('APPEAL')) status = OrderStatus.APPEALING;
      else if (s.includes('RELEASED')) status = OrderStatus.RELEASED;

      // 2. Strict UTC Timezone parsing to prevent PnL drift
      // Binance explicitly outputs UTC, but without 'Z' Node assumes standard local time.
      if (createdTimeStr && !createdTimeStr.endsWith('Z')) {
        createdTimeStr = createdTimeStr.replace(' ', 'T') + 'Z';
      }
      const createdAt = new Date(createdTimeStr);

      // --- LOGIC: Exploding Masked Users ---
      // If the nickname is masked (e.g. P2P***, Use***) AND we have a Real Name in the system or CSV,
      // we decouple them into a distinct user using the real name as a unique anchor if possible.
      // But standard CSVs don't always have "Counterparty Real Name". We will use the order Number 
      // to find existing orders and re-evaluate. Let's just properly map to a user node.
      
      let userExternalId = counterpartyNickname;
      if (counterpartyNickname.includes('***') && counterpartyRealName) {
        // Explode into a distinct user based on the real name hash or string
        userExternalId = `EXPLODED_${counterpartyRealName.replace(/\s+/g, '_')}`;
        explodedUsers++;
      }

      // 1. Transactionally lock and process the user to prevent volume race conditions
      await prisma.$transaction(async (tx) => {
        // Ensure the correct target user exists (Masked vs Exploded)
        let targetUser = await tx.user.findUnique({
          where: { externalId: userExternalId }
        });

        if (!targetUser) {
           targetUser = await tx.user.create({
             data: {
               externalId: userExternalId,
               displayName: counterpartyNickname,
               legalName: counterpartyRealName || null,
               totalVolume: 0,
               totalTrades: 0,
             }
           });
        } else if (counterpartyRealName && !targetUser.legalName) {
           targetUser = await tx.user.update({
             where: { id: targetUser.id },
             data: { legalName: counterpartyRealName }
           });
        }

        // 2. Check for duplicate order to avoid volume double-counting
        const existingOrder = await tx.p2POrder.findUnique({
          where: { externalOrderId: orderNumber }
        });

        if (!existingOrder) {
          // Brand NEW Order
          await tx.p2POrder.create({
             data: {
               externalOrderId: orderNumber,
               userId: targetUser.id,
               asset,
               amount,
               fiat,
               fiatAmount: totalFiat,
               price,
               type,
               status,
               counterparty: counterpartyNickname,
               counterpartyName: counterpartyRealName,
               createdAt: isNaN(createdAt.getTime()) ? new Date() : createdAt
             }
          });
          newlyInserted++;

          if (status === OrderStatus.COMPLETED || status === OrderStatus.RELEASED) {
            await tx.user.update({
              where: { id: targetUser.id },
              data: {
                totalVolume: { increment: amount },
                totalTrades: { increment: 1 }
              }
            });
          }
        } else {
          // EXISTING Order. Check if it needs DECOUPLING to an exploded user
          const isStatusChangedToComplete = (existingOrder.status !== OrderStatus.COMPLETED && existingOrder.status !== OrderStatus.RELEASED) &&
                                            (status === OrderStatus.COMPLETED || status === OrderStatus.RELEASED);

          const needsOwnerCorrection = existingOrder.userId !== targetUser.id;

          // If the order was already completed, it means its volume is currently counted on the OLD user.
          // If we shift ownership, we subtract from old, add to new.
          const wasPreviouslyCompleted = existingOrder.status === OrderStatus.COMPLETED || existingOrder.status === OrderStatus.RELEASED;

          // Apply Status / Owner Update cleanly
          await tx.p2POrder.update({
            where: { id: existingOrder.id },
            data: { 
               status,
               userId: targetUser.id,
               counterpartyName: counterpartyRealName || existingOrder.counterpartyName 
            }
          });

          // Handover Historical Volume IF owner is changing and was counted already!
          if (needsOwnerCorrection && wasPreviouslyCompleted) {
            // Subtract from wrong old user (the masked master)
            await tx.user.update({
               where: { id: existingOrder.userId ?? undefined },
               data: {
                 totalVolume: { decrement: existingOrder.amount },
                 totalTrades: { decrement: 1 }
               }
            });
            // Add to the correct target user
            await tx.user.update({
               where: { id: targetUser.id },
               data: {
                 totalVolume: { increment: existingOrder.amount },
                 totalTrades: { increment: 1 }
               }
            });
          }

          // If status JUST became completed AND it wasn't before (so volume wasn't counted yet)
          if (isStatusChangedToComplete) {
            await tx.user.update({
               where: { id: targetUser.id },
               data: {
                 totalVolume: { increment: amount },
                 totalTrades: { increment: 1 }
               }
            });
          }
        }
      });
    }

    return { processed, newlyInserted, explodedUsers };
  }
}
