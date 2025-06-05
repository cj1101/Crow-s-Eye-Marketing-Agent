const { PrismaClient } = require('@prisma/client');
const bcrypt = require('bcryptjs');

const prisma = new PrismaClient();

async function main() {
  console.log('🌱 Starting database seeding...');

  // Create test users
  const hashedPassword = await bcrypt.hash('password123', 12);

  const freeUser = await prisma.user.upsert({
    where: { email: 'free@example.com' },
    update: {},
    create: {
      email: 'free@example.com',
      password: hashedPassword,
      displayName: 'Free User',
      firstName: 'Free',
      lastName: 'User',
      plan: 'FREE',
    },
  });

  const creatorUser = await prisma.user.upsert({
    where: { email: 'creator@example.com' },
    update: {},
    create: {
      email: 'creator@example.com',
      password: hashedPassword,
      displayName: 'Creator User',
      firstName: 'Creator',
      lastName: 'User',
      plan: 'CREATOR',
    },
  });

  const proUser = await prisma.user.upsert({
    where: { email: 'pro@example.com' },
    update: {},
    create: {
      email: 'pro@example.com',
      password: hashedPassword,
      displayName: 'Pro User',
      firstName: 'Pro',
      lastName: 'User',
      plan: 'PRO',
    },
  });

  console.log('✅ Users created');

  // Create sample media items
  const mediaItems = [
    {
      name: 'sample-image-1.jpg',
      type: 'IMAGE',
      url: 'https://picsum.photos/800/600?random=1',
      thumbnail: 'https://picsum.photos/200/150?random=1',
      size: 245760,
      tags: ['nature', 'landscape'],
      userId: creatorUser.id,
    },
    {
      name: 'sample-image-2.jpg',
      type: 'IMAGE',
      url: 'https://picsum.photos/800/600?random=2',
      thumbnail: 'https://picsum.photos/200/150?random=2',
      size: 189432,
      tags: ['city', 'architecture'],
      userId: creatorUser.id,
    },
    {
      name: 'sample-video-1.mp4',
      type: 'VIDEO',
      url: 'https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4',
      thumbnail: 'https://picsum.photos/200/150?random=3',
      size: 1048576,
      tags: ['demo', 'sample'],
      userId: proUser.id,
    },
  ];

  for (const media of mediaItems) {
    await prisma.mediaItem.create({
      data: media,
    });
  }

  console.log('✅ Media items created');

  // Create sample gallery
  const gallery = await prisma.gallery.create({
    data: {
      title: 'Nature Collection',
      userId: creatorUser.id,
    },
  });

  const mediaForGallery = await prisma.mediaItem.findMany({
    where: { userId: creatorUser.id, type: 'IMAGE' },
    take: 2,
  });

  for (let i = 0; i < mediaForGallery.length; i++) {
    await prisma.galleryMedia.create({
      data: {
        galleryId: gallery.id,
        mediaId: mediaForGallery[i].id,
        order: i,
      },
    });
  }

  console.log('✅ Galleries created');

  // Create sample stories
  await prisma.story.create({
    data: {
      title: 'My First Story',
      content: 'This is a sample story with some interesting content about our recent adventures.',
      userId: creatorUser.id,
    },
  });

  await prisma.story.create({
    data: {
      title: 'Marketing Tips',
      content: 'Here are some great tips for social media marketing that can help boost your engagement.',
      userId: proUser.id,
    },
  });

  console.log('✅ Stories created');

  // Create sample posts
  const post1 = await prisma.post.create({
    data: {
      content: 'Check out this amazing view! 🌅 #nature #photography #landscape',
      platforms: ['instagram', 'twitter'],
      hashtags: ['nature', 'photography', 'landscape'],
      published: true,
      userId: creatorUser.id,
    },
  });

  const post2 = await prisma.post.create({
    data: {
      content: 'Exciting news coming soon! Stay tuned for updates. 🚀',
      platforms: ['facebook', 'linkedin'],
      hashtags: ['announcement', 'exciting', 'news'],
      published: true,
      userId: proUser.id,
    },
  });

  // Create analytics data for posts
  await prisma.postAnalytics.create({
    data: {
      postId: post1.id,
      platform: 'instagram',
      views: 1250,
      likes: 89,
      comments: 12,
      shares: 5,
      engagement: 8.5,
    },
  });

  await prisma.postAnalytics.create({
    data: {
      postId: post1.id,
      platform: 'twitter',
      views: 890,
      likes: 45,
      comments: 8,
      shares: 12,
      engagement: 7.3,
    },
  });

  await prisma.postAnalytics.create({
    data: {
      postId: post2.id,
      platform: 'facebook',
      views: 2100,
      likes: 156,
      comments: 23,
      shares: 18,
      engagement: 9.4,
    },
  });

  console.log('✅ Posts and analytics created');

  // Create sample activities
  const activities = [
    {
      userId: creatorUser.id,
      action: 'Media uploaded',
      type: 'SUCCESS',
    },
    {
      userId: creatorUser.id,
      action: 'Gallery created',
      type: 'SUCCESS',
    },
    {
      userId: proUser.id,
      action: 'Post published',
      type: 'SUCCESS',
    },
    {
      userId: proUser.id,
      action: 'Analytics updated',
      type: 'INFO',
    },
  ];

  for (const activity of activities) {
    await prisma.activity.create({
      data: activity,
    });
  }

  console.log('✅ Activities created');
  console.log('🎉 Database seeding completed successfully!');
  
  console.log('\n📝 Test Accounts:');
  console.log('Free User: free@example.com (password: password123)');
  console.log('Creator User: creator@example.com (password: password123)');
  console.log('Pro User: pro@example.com (password: password123)');
}

main()
  .catch((e) => {
    console.error('❌ Seeding failed:', e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  }); 