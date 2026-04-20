import { PrismaClient } from '@prisma/client';
import { config } from '../config/index.js';

const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined;
};

let prismaInstance: PrismaClient | undefined;
try {
  prismaInstance = globalForPrisma.prisma ?? new PrismaClient({
    log: config.NODE_ENV === 'development'
      ? ['query', 'info', 'warn', 'error']
      : ['warn', 'error'],
  });
} catch (e) {
  console.warn('Prisma Client failed to instantiate. Database functions will use fallback logic.');
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
