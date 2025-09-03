/**
 * Global Teardown for MINA E2E Tests
 * Cleans up test data and generates final reports
 */

const fs = require('fs').promises;
const path = require('path');
const axios = require('axios');

async function globalTeardown() {
  console.log('🧹 Starting MINA E2E Test Global Teardown...');
  
  const baseURL = global.testConfig?.baseURL || 'http://localhost:5000';
  
  try {
    // Clean up test sessions
    console.log('🗄️ Cleaning up test data...');
    
    await axios.delete(`${baseURL}/api/test/sessions`, {
      timeout: 10000,
      validateStatus: () => true
    });
    
    console.log('✅ Test data cleaned up');
    
  } catch (error) {
    console.warn('⚠️ Test cleanup failed:', error.message);
  }
  
  try {
    // Generate test summary
    console.log('📊 Generating test summary...');
    
    const testSummary = {
      testRunId: global.testConfig?.testRunId || 'unknown',
      startTime: global.testConfig?.startTime || 'unknown',
      endTime: new Date().toISOString(),
      baseURL: baseURL,
      summary: 'E2E test run completed'
    };
    
    const resultsDir = path.join(process.cwd(), 'tests', 'results');
    await fs.mkdir(resultsDir, { recursive: true });
    
    await fs.writeFile(
      path.join(resultsDir, 'test-summary.json'),
      JSON.stringify(testSummary, null, 2)
    );
    
    console.log('✅ Test summary generated');
    
  } catch (error) {
    console.error('❌ Failed to generate test summary:', error.message);
  }
  
  console.log('🎯 Global teardown completed!');
}

module.exports = globalTeardown;