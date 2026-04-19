import { PrismaClient } from '@prisma/client';
import bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

async function main() {
  console.log('🌱 Seeding 0.Bits database...\n');

  // ── 1. Superadmin Account ──────────────────────────

  const passwordHash = await bcrypt.hash('AxionAdmin2026!', 12);

  const superAdmin = await prisma.admin.upsert({
    where: { email: 'admin@axion.exchange' },
    update: {},
    create: {
      email: 'admin@axion.exchange',
      passwordHash,
      displayName: 'Axion Admin',
      role: 'SUPER_ADMIN',
      isActive: true,
    },
  });
  console.log(`  ✓ Superadmin: ${superAdmin.email}`);

  // ── 2. Sample Users ────────────────────────────────

  const users = await Promise.all([
    prisma.user.upsert({
      where: { externalId: 'BNC-281940' },
      update: {},
      create: { displayName: 'WhaleCapital', externalId: 'BNC-281940', email: 'whale@capital.io', kycStatus: 'APPROVED', country: 'BRA', totalVolume: 245000, totalTrades: 156 },
    }),
    prisma.user.upsert({
      where: { externalId: 'BNC-551230' },
      update: {},
      create: { displayName: 'EuroNode Liquidity', externalId: 'BNC-551230', email: 'ops@euronode.eu', kycStatus: 'APPROVED', country: 'DEU', totalVolume: 891000, totalTrades: 423 },
    }),
    prisma.user.upsert({
      where: { externalId: 'BNC-992810' },
      update: {},
      create: { displayName: 'AlphaTraders', externalId: 'BNC-992810', kycStatus: 'PENDING', country: 'USA', totalVolume: 52000, totalTrades: 34 },
    }),
    prisma.user.upsert({
      where: { externalId: 'BNC-113570' },
      update: {},
      create: { displayName: 'BogotaPay', externalId: 'BNC-113570', email: 'admin@bogotapay.co', kycStatus: 'APPROVED', country: 'COL', totalVolume: 1240000, totalTrades: 891 },
    }),
    prisma.user.upsert({
      where: { externalId: 'BNC-774401' },
      update: {},
      create: { displayName: 'LagosBridge API', externalId: 'BNC-774401', kycStatus: 'IN_REVIEW', country: 'NGA', totalVolume: 97000, totalTrades: 67 },
    }),
    prisma.user.upsert({
      where: { externalId: 'BNC-420699' },
      update: {},
      create: { displayName: 'SolanaWhale', externalId: 'BNC-420699', kycStatus: 'NOT_STARTED', country: 'GBR', totalVolume: 18000, totalTrades: 12, isBlocked: true, blockedReason: 'Suspicious activity' },
    }),
  ]);
  console.log(`  ✓ Users: ${users.length} seeded`);

  // ── 3. P2P Accounts ────────────────────────────────

  const binanceAccount = await prisma.p2PAccount.upsert({
    where: { exchange_label: { exchange: 'binance', label: 'Binance EUR Main' } },
    update: {},
    create: { exchange: 'binance', label: 'Binance EUR Main', apiKeyEnc: 'enc_placeholder_key', apiSecretEnc: 'enc_placeholder_secret', region: 'EU', isActive: true },
  });

  const bitgetAccount = await prisma.p2PAccount.upsert({
    where: { exchange_label: { exchange: 'bitget', label: 'Bitget LATAM' } },
    update: {},
    create: { exchange: 'bitget', label: 'Bitget LATAM', apiKeyEnc: 'enc_placeholder_key', apiSecretEnc: 'enc_placeholder_secret', passphraseEnc: 'enc_placeholder_pass', region: 'LATAM', isActive: true },
  });
  console.log(`  ✓ P2P Accounts: ${binanceAccount.label}, ${bitgetAccount.label}`);

  // ── 4. Advertisements ──────────────────────────────

  const ads = await Promise.all([
    prisma.p2PAdvertisement.create({ data: { accountId: binanceAccount.id, asset: 'USDT', fiat: 'BRL', type: 'SELL', price: 5.12, marginPercent: 1.2, minLimit: 1000, maxLimit: 50000, availableQty: 25000, status: 'ACTIVE' } }),
    prisma.p2PAdvertisement.create({ data: { accountId: binanceAccount.id, asset: 'BTC', fiat: 'EUR', type: 'BUY', price: 64200, marginPercent: -0.5, minLimit: 5000, maxLimit: 100000, availableQty: 2, status: 'ACTIVE' } }),
    prisma.p2PAdvertisement.create({ data: { accountId: bitgetAccount.id, asset: 'USDC', fiat: 'COP', type: 'BUY', price: 4050, marginPercent: -1.1, minLimit: 50000, maxLimit: 200000, availableQty: 15000, status: 'ACTIVE' } }),
    prisma.p2PAdvertisement.create({ data: { accountId: binanceAccount.id, asset: 'USDT', fiat: 'NGN', type: 'SELL', price: 1250, marginPercent: 2.5, minLimit: 100000, maxLimit: 1000000, availableQty: 0, status: 'DEPLETED' } }),
    prisma.p2PAdvertisement.create({ data: { accountId: binanceAccount.id, asset: 'ETH', fiat: 'USD', type: 'SELL', price: 3450, marginPercent: 0.8, minLimit: 10000, maxLimit: 500000, availableQty: 50, status: 'PAUSED' } }),
    prisma.p2PAdvertisement.create({ data: { accountId: binanceAccount.id, asset: 'SOL', fiat: 'USD', type: 'SELL', price: 145.2, marginPercent: 1.5, minLimit: 1000, maxLimit: 20000, availableQty: 200, status: 'ACTIVE' } }),
    prisma.p2PAdvertisement.create({ data: { accountId: binanceAccount.id, asset: 'DAI', fiat: 'EUR', type: 'BUY', price: 0.99, marginPercent: -0.1, minLimit: 5000, maxLimit: 50000, availableQty: 10000, status: 'ACTIVE' } }),
    prisma.p2PAdvertisement.create({ data: { accountId: bitgetAccount.id, asset: 'BTC', fiat: 'BRL', type: 'SELL', price: 350000, marginPercent: 1.8, minLimit: 10000, maxLimit: 500000, availableQty: 1.5, status: 'PAUSED' } }),
  ]);
  console.log(`  ✓ Advertisements: ${ads.length} seeded`);

  // ── 5. Sample Orders ───────────────────────────────

  const orders = await Promise.all([
    prisma.p2POrder.create({ data: { advertisementId: ads[0]!.id, userId: users[0]!.id, asset: 'USDT', amount: 5000, fiat: 'BRL', fiatAmount: 25600, price: 5.12, type: 'SELL', counterparty: 'WhaleCapital', status: 'PENDING_RELEASE' } }),
    prisma.p2POrder.create({ data: { advertisementId: ads[1]!.id, userId: users[1]!.id, asset: 'BTC', amount: 2.5, fiat: 'EUR', fiatAmount: 160500, price: 64200, type: 'BUY', counterparty: 'EuroNode Liquidity', status: 'PENDING_FIAT' } }),
    prisma.p2POrder.create({ data: { advertisementId: ads[4]!.id, userId: users[2]!.id, asset: 'ETH', amount: 100, fiat: 'USD', fiatAmount: 345000, price: 3450, type: 'SELL', counterparty: 'AlphaTraders', status: 'APPEALING' } }),
    prisma.p2POrder.create({ data: { advertisementId: ads[2]!.id, userId: users[3]!.id, asset: 'USDC', amount: 80000, fiat: 'COP', fiatAmount: 324000000, price: 4050, type: 'BUY', counterparty: 'BogotaPay', status: 'PENDING_RELEASE' } }),
    prisma.p2POrder.create({ data: { advertisementId: ads[3]!.id, userId: users[4]!.id, asset: 'USDT', amount: 12500, fiat: 'NGN', fiatAmount: 15625000, price: 1250, type: 'SELL', counterparty: 'LagosBridge API', status: 'PENDING_FIAT' } }),
    prisma.p2POrder.create({ data: { advertisementId: ads[5]!.id, userId: users[5]!.id, asset: 'SOL', amount: 500, fiat: 'USD', fiatAmount: 72600, price: 145.2, type: 'SELL', counterparty: 'SolanaWhale', status: 'COMPLETED', completedAt: new Date() } }),
  ]);
  console.log(`  ✓ Orders: ${orders.length} seeded`);

  // ── 6. Payment Methods ─────────────────────────────

  await Promise.all([
    prisma.paymentMethod.create({ data: { label: 'Revolut EUR', type: 'BANK_TRANSFER', bankName: 'Revolut', currency: 'EUR', country: 'LTU', isActive: true, isPrimary: true } }),
    prisma.paymentMethod.create({ data: { label: 'Wise GBP', type: 'BANK_TRANSFER', bankName: 'Wise', currency: 'GBP', country: 'GBR', isActive: true } }),
    prisma.paymentMethod.create({ data: { label: 'PIX Brazil', type: 'PIX', currency: 'BRL', country: 'BRA', isActive: true } }),
    prisma.paymentMethod.create({ data: { label: 'PSE Colombia', type: 'PSE', currency: 'COP', country: 'COL', isActive: true } }),
    prisma.paymentMethod.create({ data: { label: 'SPEI Mexico', type: 'SPEI', currency: 'MXN', country: 'MEX', isActive: true } }),
  ]);
  console.log(`  ✓ Payment Methods: 5 seeded`);

  // ── 7. Portfolio ───────────────────────────────────

  await Promise.all([
    prisma.portfolio.upsert({ where: { currency: 'EUR' }, update: {}, create: { currency: 'EUR', totalBalance: 3831.49, availableBalance: 3400, lockedBalance: 431.49 } }),
    prisma.portfolio.upsert({ where: { currency: 'USDT' }, update: {}, create: { currency: 'USDT', totalBalance: 4750.42, availableBalance: 3250.42, lockedBalance: 1500 } }),
    prisma.portfolio.upsert({ where: { currency: 'BRL' }, update: {}, create: { currency: 'BRL', totalBalance: 7604.01, availableBalance: 7604.01, lockedBalance: 0 } }),
    prisma.portfolio.upsert({ where: { currency: 'COP' }, update: {}, create: { currency: 'COP', totalBalance: 1148079, availableBalance: 1148079, lockedBalance: 0 } }),
    prisma.portfolio.upsert({ where: { currency: 'MXN' }, update: {}, create: { currency: 'MXN', totalBalance: 230952.13, availableBalance: 230952.13, lockedBalance: 0 } }),
    prisma.portfolio.upsert({ where: { currency: 'BTC' }, update: {}, create: { currency: 'BTC', totalBalance: 0.045, availableBalance: 0.045, lockedBalance: 0 } }),
  ]);
  console.log(`  ✓ Portfolio: 6 currencies seeded`);

  // ── 8. Nodes ───────────────────────────────────────

  await Promise.all([
    prisma.node.upsert({ where: { hostname: 'vps-prod-01' }, update: {}, create: { hostname: 'vps-prod-01', ipAddress: '167.235.X.X', region: 'EU-FRA', provider: 'hetzner', role: 'api', status: 'ONLINE', version: '1.0.0', cpuPercent: 12.5, memoryPercent: 34.2, diskPercent: 22.1, uptimeSeconds: 864000, lastHeartbeatAt: new Date() } }),
    prisma.node.upsert({ where: { hostname: 'vps-worker-01' }, update: {}, create: { hostname: 'vps-worker-01', ipAddress: '168.119.X.X', region: 'EU-FRA', provider: 'hetzner', role: 'worker', status: 'ONLINE', version: '1.0.0', cpuPercent: 45.0, memoryPercent: 62.1, diskPercent: 38.7, uptimeSeconds: 864000, lastHeartbeatAt: new Date() } }),
    prisma.node.upsert({ where: { hostname: 'vps-db-01' }, update: {}, create: { hostname: 'vps-db-01', ipAddress: '49.13.X.X', region: 'EU-FRA', provider: 'hetzner', role: 'db', status: 'ONLINE', version: '16.2', cpuPercent: 8.3, memoryPercent: 71.5, diskPercent: 55.2, uptimeSeconds: 2592000, lastHeartbeatAt: new Date() } }),
  ]);
  console.log(`  ✓ Nodes: 3 seeded`);

  // ── 9. Sample Notifications ────────────────────────

  await Promise.all([
    prisma.notification.create({ data: { adminId: superAdmin.id, type: 'ORDER', title: 'New P2P Order', body: 'WhaleCapital placed a 5,000 USDT sell order.', actionUrl: '/p2p/orders' } }),
    prisma.notification.create({ data: { adminId: superAdmin.id, type: 'DISPUTE', title: 'Dispute Filed', body: 'AlphaTraders filed an appeal on order ORD-993.', actionUrl: '/p2p/disputes' } }),
    prisma.notification.create({ data: { adminId: superAdmin.id, type: 'KYC', title: 'KYC Pending Review', body: 'LagosBridge API submitted KYC documents for verification.', actionUrl: '/users/kyc' } }),
    prisma.notification.create({ data: { adminId: superAdmin.id, type: 'SYSTEM', title: 'Scheduled Maintenance', body: 'Database backup scheduled for 03:00 UTC tonight.' } }),
    prisma.notification.create({ data: { adminId: superAdmin.id, type: 'TREASURY', title: 'Balance Alert', body: 'USDT funding balance dropped below 2,000 threshold.' } }),
  ]);
  console.log(`  ✓ Notifications: 5 seeded`);

  console.log('\n✅ Seed complete!\n');
  console.log('  Login credentials:');
  console.log('  Email:    admin@axion.exchange');
  console.log('  Password: AxionAdmin2026!\n');
}

main()
  .then(() => prisma.$disconnect())
  .catch(async (e) => {
    console.error('Seed failed:', e);
    await prisma.$disconnect();
    process.exit(1);
  });
