/**
 * Seed script for 0pool.io backend
 * Seeds: admin user, client role, admin role, all 16 liquidity pools, and system settings
 */
import { PrismaClient } from '@prisma/client';
import bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

async function main() {
  console.log('🌱 Seeding database...\n');

  // ─── ROLES ────────────────────────────────────────────
  const adminRole = await prisma.userRole.upsert({
    where: { slug: 'admin' },
    update: {},
    create: { slug: 'admin', name: 'Administrator', isProtected: true },
  });

  const clientRole = await prisma.userRole.upsert({
    where: { slug: 'client' },
    update: {},
    create: { slug: 'client', name: 'Client', isDefault: true },
  });

  console.log('✅ Roles created');

  // ─── ADMIN USER ───────────────────────────────────────
  const adminPassword = await bcrypt.hash('admin123', 12);
  const admin = await prisma.user.upsert({
    where: { email: 'admin@0pools.io' },
    update: {},
    create: {
      email: 'admin@0pools.io',
      passwordHash: adminPassword,
      name: 'Admin',
      roleId: adminRole.id,
      status: 'ACTIVE',
      isProtected: true,
      emailVerifiedAt: new Date(),
    },
  });

  // Demo client user
  const clientPassword = await bcrypt.hash('client123', 12);
  const client = await prisma.user.upsert({
    where: { email: 'demo@0pool.io' },
    update: {},
    create: {
      email: 'demo@0pool.io',
      passwordHash: clientPassword,
      name: 'Demo Investor',
      roleId: clientRole.id,
      status: 'ACTIVE',
      emailVerifiedAt: new Date(),
    },
  });

  console.log('✅ Users created (admin@0pools.io / admin123, demo@0pool.io / client123)');

  // ─── POOLS ────────────────────────────────────────────
  const poolsData = [
    { name: 'USDT/EUR', tvl: 150200000, vol: 45100000, rate: 0.1, apr: 12.50, chain: 'Ethereum', risk: 'Low' as const, icon: 'https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/svg/color/usdt.svg' },
    { name: 'USDC/EUR', tvl: 120400000, vol: 38200000, rate: 0.1, apr: 11.20, chain: 'Ethereum', risk: 'Low' as const, icon: 'https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/svg/color/usdc.svg' },
    { name: 'BTC/EUR', tvl: 540100000, vol: 210500000, rate: 0.2, apr: 4.50, chain: 'Bitcoin', risk: 'Medium' as const, icon: 'https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/svg/color/btc.svg' },
    { name: 'USDT/MXN', tvl: 85300000, vol: 22400000, rate: 0.3, apr: 14.10, chain: 'Tron', risk: 'Low' as const, icon: 'https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/svg/color/usdt.svg' },
    { name: 'USDC/MXN', tvl: 76800000, vol: 19800000, rate: 0.3, apr: 13.50, chain: 'Polygon', risk: 'Low' as const, icon: 'https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/svg/color/usdc.svg' },
    { name: 'USDT/BRL', tvl: 110200000, vol: 41200000, rate: 0.3, apr: 15.20, chain: 'Tron', risk: 'Low' as const, icon: 'https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/svg/color/usdt.svg' },
    { name: 'USDC/BRL', tvl: 95500000, vol: 36500000, rate: 0.3, apr: 14.80, chain: 'Polygon', risk: 'Low' as const, icon: 'https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/svg/color/usdc.svg' },
    { name: 'ETH/EUR', tvl: 420700000, vol: 180300000, rate: 0.2, apr: 5.20, chain: 'Ethereum', risk: 'Medium' as const, icon: 'https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/svg/color/eth.svg' },
    { name: 'SOL/EUR', tvl: 310400000, vol: 140200000, rate: 0.3, apr: 8.50, chain: 'Solana', risk: 'High' as const, icon: 'https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/svg/color/sol.svg' },
    { name: 'ETH/MXN', tvl: 64200000, vol: 28400000, rate: 0.4, apr: 6.10, chain: 'Ethereum', risk: 'Medium' as const, icon: 'https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/svg/color/eth.svg' },
    { name: 'ETH/COP', tvl: 42100000, vol: 18200000, rate: 0.4, apr: 7.20, chain: 'Ethereum', risk: 'Medium' as const, icon: 'https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/svg/color/eth.svg' },
    { name: 'BTC/MXN', tvl: 125800000, vol: 65300000, rate: 0.4, apr: 5.10, chain: 'Bitcoin', risk: 'Medium' as const, icon: 'https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/svg/color/btc.svg' },
    { name: 'BTC/BRL', tvl: 185400000, vol: 82100000, rate: 0.4, apr: 5.80, chain: 'Bitcoin', risk: 'Medium' as const, icon: 'https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/svg/color/btc.svg' },
    { name: 'BTC/COP', tvl: 68900000, vol: 32400000, rate: 0.4, apr: 6.50, chain: 'Bitcoin', risk: 'Medium' as const, icon: 'https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/svg/color/btc.svg' },
    { name: 'USDT/CLP', tvl: 55200000, vol: 21500000, rate: 0.3, apr: 16.50, chain: 'Tron', risk: 'Low' as const, icon: 'https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/svg/color/usdt.svg' },
    { name: 'USDC/CLP', tvl: 48600000, vol: 18400000, rate: 0.3, apr: 15.80, chain: 'Polygon', risk: 'Low' as const, icon: 'https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/svg/color/usdc.svg' },
  ];

  for (const pool of poolsData) {
    await prisma.pool.upsert({
      where: { id: poolsData.indexOf(pool) + 1 },
      update: {
        totalTvl: pool.tvl,
        volume24h: pool.vol,
        apy: pool.apr,
        feeRate: pool.rate,
      },
      create: {
        name: pool.name,
        chain: pool.chain,
        riskTier: pool.risk,
        apy: pool.apr,
        feeRate: pool.rate,
        totalTvl: pool.tvl,
        volume24h: pool.vol,
        icon: pool.icon,
        description: `Institutional ${pool.name} liquidity pool on ${pool.chain}`,
        cryptoDepositAddress: '0x9A48aFb488eB3Fc2e445084931aC3660DE3A2Bf5',
      },
    });
  }

  console.log(`✅ ${poolsData.length} liquidity pools seeded`);

  // ─── SYSTEM SETTINGS ──────────────────────────────────
  const existingSettings = await prisma.systemSetting.findFirst();
  if (!existingSettings) {
    await prisma.systemSetting.create({
      data: {
        brandName: '0pools',
        brandLogo: 'https://0pools.io/logo.png',
        depositBeneficiary: '0pools SP ZOO',
        cryptoDepositAddress: '0x9A48aFb488eB3Fc2e445084931aC3660DE3A2Bf5',
        primaryColor: '#00FF66',
        supportEmail: 'support@0pool.io',
        currency: 'EUR',
      },
    });
    console.log('✅ System settings created');
  }

  // ─── VOLUME SNAPSHOTS (sample data) ───────────────────
  const pools = await prisma.pool.findMany();
  const now = new Date();

  for (const pool of pools) {
    // 30 daily snapshots
    for (let i = 0; i < 30; i++) {
      const date = new Date(now);
      date.setDate(date.getDate() - i);

      await prisma.poolVolumeSnapshot.create({
        data: {
          poolId: pool.id,
          volume: Math.floor(Math.random() * 50000000 + 20000000),
          period: 'daily',
          date,
        },
      });
    }

    // 12 weekly snapshots
    for (let i = 0; i < 12; i++) {
      const date = new Date(now);
      date.setDate(date.getDate() - (i * 7));

      await prisma.poolVolumeSnapshot.create({
        data: {
          poolId: pool.id,
          volume: Math.floor(Math.random() * 200000000 + 100000000),
          period: 'weekly',
          date,
        },
      });
    }

    // 6 monthly snapshots
    for (let i = 0; i < 6; i++) {
      const date = new Date(now);
      date.setMonth(date.getMonth() - i);

      await prisma.poolVolumeSnapshot.create({
        data: {
          poolId: pool.id,
          volume: Math.floor(Math.random() * 600000000 + 400000000),
          period: 'monthly',
          date,
        },
      });
    }
  }

  console.log('✅ Volume snapshots seeded (30D + 12W + 6M)');

  console.log('\n🎉 Database seeded successfully!\n');
}

main()
  .catch((e) => {
    console.error('❌ Seed failed:', e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
