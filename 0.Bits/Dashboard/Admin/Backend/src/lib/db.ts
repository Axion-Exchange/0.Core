import { PrismaClient } from '@prisma/client';
import { config } from '../config/index.js';

const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined;
};

let prismaInstance: PrismaClient | undefined;
try {
  prismaInstance = globalForPrisma.prisma ?? new PrismaClient({
    datasources: {
      db: {
        url: config.DATABASE_URL
      }
    }
  });
} catch (e: any) {
  console.error('Prisma Client failed to instantiate natively:', e.message);
}

export const prisma = prismaInstance as PrismaClient;

if (config.NODE_ENV !== 'production') {
  globalForPrisma.prisma = prisma;
}

/**
 * Verify database connectivity. Called during server startup.
 */
export async function checkDatabaseHealth(): Promise<boolean> {
  try {
    await prisma.$queryRaw`SELECT 1`;
    return true;
  } catch {
    return false;
  }
}

/**
 * Gracefully disconnect from the database.
 */
export async function disconnectDatabase(): Promise<void> {
  await prisma.$disconnect();
}
