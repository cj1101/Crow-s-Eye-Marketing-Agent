const { PrismaClient } = require('@prisma/client');
require('dotenv').config();

const prisma = new PrismaClient();

async function testConnection() {
  try {
    console.log('🔄 Testing database connection...');
    console.log('DATABASE_URL:', process.env.DATABASE_URL ? 'Set' : 'Not set');
    
    // Try to connect and run a simple query
    await prisma.$connect();
    console.log('✅ Database connection successful!');
    
    // Test if we can query (this will fail if tables don't exist yet, which is fine)
    try {
      const result = await prisma.$queryRaw`SELECT 1 as test`;
      console.log('✅ Database query test successful:', result);
    } catch (queryError) {
      console.log('ℹ️  Database connected but no tables yet (this is expected before migration)');
    }
    
  } catch (error) {
    console.error('❌ Database connection failed:');
    console.error('Error:', error.message);
    
    if (error.message.includes('ENOTFOUND')) {
      console.log('\n💡 This usually means:');
      console.log('   - DATABASE_URL is incorrect');
      console.log('   - Network connectivity issues');
      console.log('   - Neon database endpoint is wrong');
    } else if (error.message.includes('authentication failed')) {
      console.log('\n💡 This usually means:');
      console.log('   - Username or password is incorrect');
      console.log('   - DATABASE_URL credentials are wrong');
    }
    
    process.exit(1);
  } finally {
    await prisma.$disconnect();
  }
}

testConnection(); 