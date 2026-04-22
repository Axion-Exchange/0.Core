import { PrismaClient } from "@prisma/client";
const p = new PrismaClient();

async function main() {
  // Check what Januar transactions look like
  const januarTxns = await p.transaction.findMany({
    where: { source: "januar", type: "TRANSFER_IN" },
    select: { description: true, amount: true, metadata: true },
  });

  console.log(`Total Januar PAYINs: ${januarTxns.length}\n`);

  // Search for the 3 third-party names
  const names = ["Ali Sall", "Geraldine", "Cardenas", "Shafiull", "Kaysar", "Simon", "Paysend"];

  for (const name of names) {
    const lower = name.toLowerCase();
    let found = 0;
    for (const t of januarTxns) {
      const meta = t.metadata as any;
      const senderName = (meta?.senderName || meta?.counterparty?.name || t.description || "").toLowerCase();
      if (senderName.includes(lower)) {
        found++;
        console.log(`  "${name}" found in: sender="${senderName}", amount=${t.amount}`);
      }
    }
    if (found === 0) console.log(`  "${name}" → NOT FOUND in any Januar PAYIN`);
  }

  // Also check what fields are in metadata
  const sample = januarTxns[0];
  if (sample) {
    const meta = sample.metadata as any;
    console.log("\nSample Januar metadata keys:", Object.keys(meta || {}).join(", "));
    console.log("senderName:", meta?.senderName);
    console.log("counterparty:", JSON.stringify(meta?.counterparty));
    console.log("description:", sample.description);
  }

  // Search specifically around the order amounts
  console.log("\n--- Searching by amount ranges ---");
  // Kevin: 5720.82 EUR
  const kevin = januarTxns.filter(t => {
    const amt = parseFloat(t.amount.toString());
    return amt >= 5000 && amt <= 6000;
  });
  console.log(`Kevin range (5000-6000): ${kevin.length} txns`);
  for (const t of kevin) {
    const meta = t.metadata as any;
    console.log(`  ${t.amount} | ${meta?.senderName || t.description || "no name"}`);
  }

  // Marin: 173.61 → wife paid 150
  const marin = januarTxns.filter(t => {
    const amt = parseFloat(t.amount.toString());
    return amt >= 145 && amt <= 180;
  });
  console.log(`\nMarin range (145-180): ${marin.length} txns`);
  for (const t of marin.slice(0, 10)) {
    const meta = t.metadata as any;
    console.log(`  ${t.amount} | ${meta?.senderName || t.description || "no name"}`);
  }

  // Nilufa: 114.28
  const nilufa = januarTxns.filter(t => {
    const amt = parseFloat(t.amount.toString());
    return amt >= 110 && amt <= 120;
  });
  console.log(`\nNilufa range (110-120): ${nilufa.length} txns`);
  for (const t of nilufa.slice(0, 10)) {
    const meta = t.metadata as any;
    console.log(`  ${t.amount} | ${meta?.senderName || t.description || "no name"}`);
  }

  await p.$disconnect();
}
main();
