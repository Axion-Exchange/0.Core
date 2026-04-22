import { PrismaClient } from "@prisma/client";
const p = new PrismaClient();
async function main() {
  const total = await p.kycSession.count();
  const matched = await p.kycSession.count({ where: { matchedUserId: { not: null } } });
  console.log(`Sessions: ${total} | Matched: ${matched} | Unmatched: ${total - matched}`);

  const falsies = await p.kycSession.findMany({
    where: { matchedUserId: { not: null }, matchSimilarity: { lt: 1.0 } },
    include: { matchedUser: { select: { legalName: true } } },
    orderBy: { matchSimilarity: "asc" },
  });
  console.log(`\nLow-confidence matches (${falsies.length} total):`);
  for (const f of falsies) {
    console.log(`  ${f.matchSimilarity?.toFixed(2)} | ${f.matchedUser?.legalName} ↔ ${f.fullName}`);
  }
  await p.$disconnect();
}
main();
