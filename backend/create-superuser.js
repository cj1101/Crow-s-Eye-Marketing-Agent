const { PrismaClient } = require('@prisma/client');
const bcrypt = require('bcryptjs');

const prisma = new PrismaClient();

async function createSuperUser() {
  try {
    console.log('Creating/updating super user account for charlie@suarezhouse.net...');
    
    const email = 'charlie@suarezhouse.net';
    const password = 'CrowsEye2024!'; // You may want to change this
    const hashedPassword = await bcrypt.hash(password, 10);
    
    // Check if user already exists
    const existingUser = await prisma.user.findUnique({
      where: { email }
    });
    
    if (existingUser) {
      // Update existing user to PRO plan
      const updatedUser = await prisma.user.update({
        where: { email },
        data: {
          plan: 'PRO',
          displayName: 'Charlie Suarez (Super Admin)',
          firstName: 'Charlie',
          lastName: 'Suarez',
          updatedAt: new Date()
        }
      });
      
      console.log('✅ Super user account updated successfully!');
      console.log(`User ID: ${updatedUser.id}`);
      console.log(`Email: ${updatedUser.email}`);
      console.log(`Plan: ${updatedUser.plan}`);
      console.log(`Display Name: ${updatedUser.displayName}`);
    } else {
      // Create new super user
      const newUser = await prisma.user.create({
        data: {
          email,
          password: hashedPassword,
          displayName: 'Charlie Suarez (Super Admin)',
          firstName: 'Charlie',
          lastName: 'Suarez',
          plan: 'PRO'
        }
      });
      
      console.log('✅ Super user account created successfully!');
      console.log(`User ID: ${newUser.id}`);
      console.log(`Email: ${newUser.email}`);
      console.log(`Plan: ${newUser.plan}`);
      console.log(`Display Name: ${newUser.displayName}`);
      console.log(`Default Password: CrowsEye2024! (Please change this after first login)`);
    }
    
  } catch (error) {
    console.error('❌ Error creating super user:', error);
  } finally {
    await prisma.$disconnect();
  }
}

createSuperUser(); 