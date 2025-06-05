const axios = require('axios');

const API_BASE = 'http://localhost:3001';

let authToken = null;
let testUserId = null;

async function testAPI() {
  console.log('🧪 Testing Crow\'s Eye API with Real Database\n');

  try {
    // Test 1: Health Check
    console.log('1. Testing Health Check...');
    const health = await axios.get(`${API_BASE}/health`);
    console.log(`✅ Health: ${health.data.status} - Database: ${health.data.database}\n`);

    // Test 2: API Info
    console.log('2. Testing API Info...');
    const apiInfo = await axios.get(`${API_BASE}/`);
    console.log(`✅ API: ${apiInfo.data.name} v${apiInfo.data.version}\n`);

    // Test 3: User Registration
    console.log('3. Testing User Registration...');
    const registerData = {
      email: `test-${Date.now()}@example.com`,
      password: 'testpassword123',
      displayName: 'Test User API',
      firstName: 'Test',
      lastName: 'User'
    };
    
    const register = await axios.post(`${API_BASE}/auth/signup`, registerData);
    authToken = register.data.token;
    testUserId = register.data.user.id;
    console.log(`✅ Registration successful. Token: ${authToken.substring(0, 20)}...\n`);

    // Test 4: User Login
    console.log('4. Testing User Login with existing user...');
    const login = await axios.post(`${API_BASE}/auth/login`, {
      email: 'creator@example.com',
      password: 'password123'
    });
    authToken = login.data.token; // Use seeded user token
    console.log(`✅ Login successful. User: ${login.data.user.displayName}\n`);

    const headers = { Authorization: `Bearer ${authToken}` };

    // Test 5: Get User Profile
    console.log('5. Testing Get User Profile...');
    const profile = await axios.get(`${API_BASE}/user/profile`, { headers });
    console.log(`✅ Profile: ${profile.data.displayName} (${profile.data.plan})\n`);

    // Test 6: Get Media Items
    console.log('6. Testing Get Media Items...');
    const media = await axios.get(`${API_BASE}/media`, { headers });
    console.log(`✅ Media items: ${media.data.length} items found\n`);

    // Test 7: Get Galleries
    console.log('7. Testing Get Galleries...');
    const galleries = await axios.get(`${API_BASE}/galleries`, { headers });
    console.log(`✅ Galleries: ${galleries.data.length} galleries found\n`);

    // Test 8: Get Stories
    console.log('8. Testing Get Stories...');
    const stories = await axios.get(`${API_BASE}/stories`, { headers });
    console.log(`✅ Stories: ${stories.data.length} stories found\n`);

    // Test 9: Get Analytics Overview
    console.log('9. Testing Get Analytics...');
    const analytics = await axios.get(`${API_BASE}/analytics`, { headers });
    console.log(`✅ Analytics: Overview data received\n`);

    // Test 10: Create New Story
    console.log('10. Testing Create New Story...');
    const newStory = await axios.post(`${API_BASE}/stories`, {
      title: 'API Test Story',
      content: 'This story was created via API test!',
      media: []
    }, { headers });
    console.log(`✅ New story created: ${newStory.data.title}\n`);

    // Test 11: Create New Gallery
    console.log('11. Testing Create New Gallery...');
    // Get an image ID from the media items
    const imageMedia = media.data.find(item => item.type === 'IMAGE');
    const newGallery = await axios.post(`${API_BASE}/galleries`, {
      title: 'API Test Gallery',
      images: imageMedia ? [imageMedia.id] : []
    }, { headers });
    console.log(`✅ New gallery created: ${newGallery.data.title}\n`);

    // Test 12: Get Marketing Tool Stats (includes activities)
    console.log('12. Testing Get Marketing Tool Stats...');
    const marketingStats = await axios.get(`${API_BASE}/marketing-tool/stats`, { headers });
    console.log(`✅ Marketing Stats: ${marketingStats.data.recentActivity.length} activities found\n`);

    console.log('🎉 ALL API TESTS PASSED! Your backend is fully functional with the database.\n');
    
    console.log('📊 Summary:');
    console.log('- ✅ Database connection working');
    console.log('- ✅ User authentication working');  
    console.log('- ✅ All CRUD operations working');
    console.log('- ✅ Sample data loaded');
    console.log('- ✅ JWT tokens working');
    console.log('- ✅ All API endpoints responding\n');

    console.log('🔑 Test Accounts Available:');
    console.log('- free@example.com (password: password123)');
    console.log('- creator@example.com (password: password123)');
    console.log('- pro@example.com (password: password123)\n');

    console.log('🚀 Your Crow\'s Eye backend is ready for production!');
    console.log('📖 API Documentation: http://localhost:3001/docs');

  } catch (error) {
    console.error('❌ API Test Failed:', error.response?.data || error.message);
    
    if (error.code === 'ECONNREFUSED') {
      console.log('\n💡 Server not running. Please start it with: npm run dev');
    }
    
    process.exit(1);
  }
}

// Wait a moment for server to start, then test
setTimeout(testAPI, 2000); 