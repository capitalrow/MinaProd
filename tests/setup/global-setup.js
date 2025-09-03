/**
 * Global Setup for MINA E2E Tests
 * Configures test environment, database, and dependencies
 */

const axios = require('axios');

async function globalSetup() {
  console.log('🚀 Starting MINA E2E Test Global Setup...');
  
  const baseURL = 'http://localhost:5000';
  const maxRetries = 30;
  const retryDelay = 2000;
  
  // Wait for server to be ready
  console.log('⏳ Waiting for MINA server to be ready...');
  
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await axios.get(`${baseURL}/health`, {
        timeout: 5000,
        validateStatus: () => true
      });
      
      if (response.status === 200) {
        console.log('✅ MINA server is ready!');
        break;
      }
      
      if (i === maxRetries - 1) {
        throw new Error(`Server not ready after ${maxRetries} attempts`);
      }
      
      console.log(`🔄 Attempt ${i + 1}/${maxRetries} - Server not ready, retrying...`);
      await new Promise(resolve => setTimeout(resolve, retryDelay));
      
    } catch (error) {
      if (i === maxRetries - 1) {
        console.error('❌ MINA server failed to start:', error.message);
        throw error;
      }
      
      console.log(`🔄 Attempt ${i + 1}/${maxRetries} - Connection failed, retrying...`);
      await new Promise(resolve => setTimeout(resolve, retryDelay));
    }
  }
  
  // Setup test database state
  try {
    console.log('🗄️ Setting up test database state...');
    
    // Clear any existing test sessions
    await axios.delete(`${baseURL}/api/test/sessions`, {
      timeout: 10000,
      validateStatus: () => true
    });
    
    console.log('✅ Test database state prepared');
    
  } catch (error) {
    console.warn('⚠️ Database cleanup failed (may not exist yet):', error.message);
  }
  
  // Verify critical endpoints
  console.log('🔍 Verifying critical endpoints...');
  
  const criticalEndpoints = [
    '/live',
    '/api/health',
    '/health/detailed'
  ];
  
  for (const endpoint of criticalEndpoints) {
    try {
      const response = await axios.get(`${baseURL}${endpoint}`, {
        timeout: 10000,
        validateStatus: () => true
      });
      
      if (response.status < 400) {
        console.log(`✅ ${endpoint} - OK (${response.status})`);
      } else {
        console.warn(`⚠️ ${endpoint} - Warning (${response.status})`);
      }
      
    } catch (error) {
      console.error(`❌ ${endpoint} - Failed:`, error.message);
    }
  }
  
  console.log('🎯 Global setup completed successfully!');
  
  // Store global test configuration
  global.testConfig = {
    baseURL,
    startTime: new Date().toISOString(),
    testRunId: `test_${Date.now()}_${Math.random().toString(36).substring(7)}`
  };
}

module.exports = globalSetup;