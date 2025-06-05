import { PrismaClient } from '@prisma/client';

// Global Prisma client instance
let prisma: PrismaClient;

declare global {
  var __prisma: PrismaClient | undefined;
}

// Ensure single instance in development (hot reload protection)
if (process.env.NODE_ENV === 'production') {
  prisma = new PrismaClient();
} else {
  if (!global.__prisma) {
    global.__prisma = new PrismaClient({
      log: ['query', 'info', 'warn', 'error'],
    });
  }
  prisma = global.__prisma;
}

// Graceful shutdown
process.on('beforeExit', async () => {
  await prisma.$disconnect();
});

export { prisma };
export default prisma; 