import { PrismaClient } from "@prisma/client";
const p = new PrismaClient();

async function main() {
  console.log("═══ Manual Third-Party Resolution ═══\n");

  // ── 1. KEVIN MARCEL DALLE → Link Ali Sall KYC to Kevin ──
  // Ali Sall is the company director, so link KYC to Kevin's user
  const kevinOrder = await p.p2POrder.findFirst({
    where: { counterpartyName: "KEVIN MARCEL DALLE" },
    select: { id: true, userId: true },
  });
  if (kevinOrder?.userId) {
    await p.user.update({
      where: { id: kevinOrder.userId },
      data: {
        email: "bionicstratom@proton.me",
        metadata: {
          kycEmail: "bionicstratom@proton.me",
          kycVerifiedName: "Ali Sall",
          kycProvider: "0Bit",
          kycStatus: "APPROVED",
          kycCountry: "FRA",
          kycNote: "Corporate account - Ali Sall is company director/owner",
          linkedAt: new Date().toISOString(),
        },
      },
    });
    console.log("✅ #1 Kevin Marcel Dalle → Ali Sall KYC linked (corporate)");
  }

  // ── 3. MARIN LEON → Geraldine Cardenas (wife paid) ──
  const marinOrder = await p.p2POrder.findFirst({
    where: { counterpartyName: "MARIN LEON ENRIQUE ALEJANDRO" },
    select: { id: true, userId: true, amount: true },
  });
  if (marinOrder) {
    // Find or create Geraldine as user
    let geraldine = await p.user.findFirst({
      where: { legalName: "Geraldine Margaret Cardenas Prieto" },
    });
    if (!geraldine) {
      geraldine = await p.user.create({
        data: {
          displayName: "Geraldine Margaret Cardenas Prieto",
          legalName: "Geraldine Margaret Cardenas Prieto",
          country: "VEN",
          kycStatus: "PENDING",
          metadata: {
            source: "third_party_manual",
            relationship: "wife of MARIN LEON ENRIQUE ALEJANDRO",
            kycNote: "Verified via Didit link in chat, confirmed by counterparty as wife",
            resolvedAt: new Date().toISOString(),
          },
        },
      });
      console.log(`  Created user: Geraldine (${geraldine.id})`);
    }

    // Mark order as third-party
    await p.p2POrder.update({
      where: { id: marinOrder.id },
      data: {
        actualPayerId: geraldine.id,
        isThirdParty: true,
      },
    });
    console.log(`✅ #3 Marin Leon order → actualPayer = Geraldine (wife, €${marinOrder.amount})`);
  }

  // ── 6. NILUFA HOSSAIN NILA → Shafiull Kaysar Simon (husband paid) ──
  const nilufaOrder = await p.p2POrder.findFirst({
    where: { counterpartyName: "NILUFA HOSSAIN NILA" },
    select: { id: true, userId: true, amount: true },
  });
  if (nilufaOrder) {
    // Find or create Shafiull as user
    let shafiull = await p.user.findFirst({
      where: { legalName: "Shafiull Kaysar Simon" },
    });
    if (!shafiull) {
      // Check KYC session for full data
      const kycSession = await p.kycSession.findFirst({
        where: { fullName: { contains: "Shafiull" } },
      });

      shafiull = await p.user.create({
        data: {
          displayName: "Shafiull Kaysar Simon",
          legalName: "Shafiull Kaysar Simon",
          email: "shafiullkaysarsimon090@gmail.com",
          country: kycSession?.country || "PRT",
          kycStatus: kycSession?.status === "DECLINED" ? "REJECTED" : "PENDING",
          metadata: {
            source: "third_party_manual",
            relationship: "husband of NILUFA HOSSAIN NILA (uses wife Binance)",
            kycSessionId: kycSession?.externalId,
            kycNote: "Confirmed in chat: 'I am using my wife's account, does the bank owner have to verify?'",
            resolvedAt: new Date().toISOString(),
          },
        },
      });
      console.log(`  Created user: Shafiull (${shafiull.id})`);
    }

    // Mark order as third-party
    await p.p2POrder.update({
      where: { id: nilufaOrder.id },
      data: {
        actualPayerId: shafiull.id,
        isThirdParty: true,
      },
    });
    console.log(`✅ #6 Nilufa order → actualPayer = Shafiull (husband, €${nilufaOrder.amount})`);
  }

  // ── Summary ──
  const thirdPartyCount = await p.p2POrder.count({ where: { isThirdParty: true } });
  console.log(`\n═══ Done ═══`);
  console.log(`Total orders marked as third-party: ${thirdPartyCount}`);

  await p.$disconnect();
}
main();
