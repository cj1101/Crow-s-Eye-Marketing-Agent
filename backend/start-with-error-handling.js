const { spawn } = require('child_process');
const axios = require('axios');

console.log('🚀 Starting Crow\'s Eye Backend with Enhanced Error Handling\n');

// Start the backend server
const server = spawn('npm', ['run', 'dev'], {
  stdio: 'inherit',
  shell: true,
  cwd: __dirname
});

server.on('error', (error) => {
  console.error('❌ Failed to start server:', error);
  process.exit(1);
});

// Wait for server to start, then test array responses
setTimeout(async () => {
  console.log('\n🧪 Testing API Response Consistency...\n');
  
  try {
    // Test health endpoint
    const health = await axios.get('http://localhost:3001/health');
    console.log('✅ Server is running and healthy\n');
    
    // Run array response tests
    require('./test-array-responses.js');
    
  } catch (error) {
    console.log('⚠️  Server may still be starting up...\n');
    
    // Try again in a few seconds
    setTimeout(async () => {
      try {
        await axios.get('http://localhost:3001/health');
        console.log('✅ Server is now ready\n');
        require('./test-array-responses.js');
      } catch (e) {
        console.log('❌ Server failed to start properly');
      }
    }, 5000);
  }
}, 3000);

// Handle graceful shutdown
process.on('SIGINT', () => {
  console.log('\n🛑 Shutting down server...');
  server.kill('SIGINT');
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.log('\n🛑 Shutting down server...');
  server.kill('SIGTERM');
  process.exit(0);
}); 