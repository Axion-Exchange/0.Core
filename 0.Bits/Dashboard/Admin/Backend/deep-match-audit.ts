import { PrismaClient } from "@prisma/client";
const p = new PrismaClient();

async function main() {
  // Get all 88 unmatched sessions
  const unmatched = await p.kycSession.findMany({
    where: { matchedUserId: null },
    include: { provider: { select: { name: true } } },
  });
  console.log(`=== ${unmatched.length} Unmatched Didit Sessions ===\n`);

  // Load ALL chat messages
  const allChats = await p.p2PChatMessage.findMany({
    select: { content: true, orderId: true },
  });

  // Load ALL users
  const allUsers = await p.user.findMany({
    select: { id: true, legalName: true, displayName: true, email: true },
  });

  // Build lookup maps
  const orderIdToChats = new Map<string, string[]>();
  for (const c of allChats) {
    if (!orderIdToChats.has(c.orderId)) orderIdToChats.set(c.orderId, []);
    orderIdToChats.get(c.orderId)!.push(c.content);
  }

  // All chat text combined per order
  const allChatText = allChats.map(c => c.content.toLowerCase()).join(" ");

  let foundViaEmail = 0;
  let foundViaLink = 0;
  let foundViaName = 0;
  let notFound = 0;

  for (const sess of unmatched) {
    const raw = sess.rawPayload as any;
    const email = raw?.email_address?.email?.toLowerCase();
    const sessionUrl = raw?.session_url || "";
    const slugMatch = sessionUrl.match(/\/session\/([A-Za-z0-9]+)/);
    const slug = slugMatch ? slugMatch[1] : null;
    const name = sess.fullName || "";

    let found = false;
    let method = "";
    let detail = "";

    // 1. Search email in ALL chat messages
    if (email && allChatText.includes(email.toLowerCase())) {
      // Find which order
      for (const chat of allChats) {
        if (chat.content.toLowerCase().includes(email.toLowerCase())) {
          const order = await p.p2POrder.findUnique({
            where: { id: chat.orderId },
            select: { counterpartyName: true, amount: true, fiat: true, userId: true },
          });
          if (order) {
            found = true;
            method = "EMAIL_IN_CHAT";
            detail = `${email} found in chat of order ${order.counterpartyName} (${order.amount} ${order.fiat})`;
            break;
          }
        }
      }
    }

    // 2. Search Didit link slug in chat
    if (!found && slug && allChatText.includes(slug)) {
      for (const chat of allChats) {
        if (chat.content.includes(slug)) {
          const order = await p.p2POrder.findUnique({
            where: { id: chat.orderId },
            select: { counterpartyName: true, amount: true, fiat: true },
          });
          if (order) {
            found = true;
            method = "DIDIT_LINK_IN_CHAT";
            detail = `Link slug ${slug} in chat of order ${order.counterpartyName} (${order.amount} ${order.fiat})`;
            break;
          }
        }
      }
    }

    // 3. Check if email matches any user email
    if (!found && email) {
      const userMatch = allUsers.find(u => u.email?.toLowerCase() === email);
      if (userMatch) {
        found = true;
        method = "EMAIL_MATCHES_USER";
        detail = `Email ${email} matches user ${userMatch.legalName || userMatch.displayName}`;
      }
    }

    if (found) {
      const icon = sess.status === "APPROVED" ? "✅" : sess.status === "DECLINED" ? "❌" : "⏳";
      console.log(`${icon} [${method}] ${name} (${sess.status}, ${sess.provider.name})`);
      console.log(`   → ${detail}`);
      console.log();
      if (method === "EMAIL_IN_CHAT") foundViaEmail++;
      else if (method === "DIDIT_LINK_IN_CHAT") foundViaLink++;
      else foundViaName++;
    } else {
      notFound++;
    }
  }

  console.log(`\n=== Summary ===`);
  console.log(`Found via email in chat: ${foundViaEmail}`);
  console.log(`Found via Didit link in chat: ${foundViaLink}`);
  console.log(`Found via email matching user: ${foundViaName}`);
  console.log(`Truly unmatched (no trace): ${notFound}`);
  console.log(`Total unmatched sessions: ${unmatched.length}`);

  await p.$disconnect();
}
main();
