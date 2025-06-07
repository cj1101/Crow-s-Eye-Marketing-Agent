const axios = require('axios');

const API_BASE = 'http://localhost:3001';

async function testArrayResponses() {
  console.log('🧪 Testing API Array Response Consistency\n');

  try {
    // Test endpoints without authentication (should return empty arrays, not error objects)
    const endpoints = [
      '/media',
      '/galleries', 
      '/stories',
      '/highlights',
      '/analytics',
      '/marketing-tool/stats'
    ];

    console.log('Testing endpoints without authentication...\n');
    
    for (const endpoint of endpoints) {
      try {
        const response = await axios.get(`${API_BASE}${endpoint}`);
        console.log(`✅ ${endpoint}: Returns data structure (authenticated)`);
      } catch (error) {
        if (error.response) {
          const data = error.response.data;
          if (Array.isArray(data)) {
            console.log(`✅ ${endpoint}: Returns empty array on error`);
          } else if (data && typeof data === 'object' && data.success === false) {
            console.log(`⚠️  ${endpoint}: Returns error object (may cause .map() errors)`);
          } else {
            console.log(`❌ ${endpoint}: Returns unexpected format:`, typeof data);
          }
        } else {
          console.log(`❌ ${endpoint}: Network error`);
        }
      }
    }

    // Test with valid authentication
    console.log('\nTesting with authentication...\n');
    
    try {
      const login = await axios.post(`${API_BASE}/auth/login`, {
        email: 'creator@example.com',
        password: 'password123'
      });
      
      const token = login.data.token;
      const headers = { Authorization: `Bearer ${token}` };
      
      for (const endpoint of endpoints) {
        try {
          const response = await axios.get(`${API_BASE}${endpoint}`, { headers });
          const data = response.data;
          
          if (endpoint === '/marketing-tool/stats') {
            if (data.recentActivity && Array.isArray(data.recentActivity)) {
              console.log(`✅ ${endpoint}: recentActivity is array (${data.recentActivity.length} items)`);
            } else {
              console.log(`❌ ${endpoint}: recentActivity is not array`);
            }
          } else if (endpoint === '/analytics') {
            if (data.topPosts && Array.isArray(data.topPosts) && 
                data.platformStats && Array.isArray(data.platformStats)) {
              console.log(`✅ ${endpoint}: topPosts and platformStats are arrays`);
            } else {
              console.log(`❌ ${endpoint}: Missing or invalid array properties`);
            }
          } else {
            if (Array.isArray(data)) {
              console.log(`✅ ${endpoint}: Returns array (${data.length} items)`);
            } else {
              console.log(`❌ ${endpoint}: Does not return array:`, typeof data);
            }
          }
        } catch (error) {
          console.log(`❌ ${endpoint}: Error with auth:`, error.response?.status);
        }
      }
      
    } catch (authError) {
      console.log('❌ Authentication failed, cannot test authenticated endpoints');
    }

    console.log('\n🎯 Summary:');
    console.log('- All endpoints should return arrays or objects with array properties');
    console.log('- Error responses should not break frontend .map() calls');
    console.log('- Empty arrays are better than error objects for frontend compatibility');

  } catch (error) {
    console.error('❌ Test failed:', error.message);
  }
}

// Run the test
testArrayResponses(); 