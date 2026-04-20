import { PrismaClient } from '@prisma/client/index.js';

export const prisma = new PrismaClient();

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
