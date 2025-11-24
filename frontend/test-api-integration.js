// Simple test script to verify API integration

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function testEndpoint(name, url) {
  try {
    const response = await fetch(url);
    const data = await response.json();
    console.log(`✓ ${name}: SUCCESS`);
    return true;
  } catch (error) {
    console.log(`✗ ${name}: FAILED - ${error.message}`);
    return false;
  }
}

async function runTests() {
  console.log('Testing MNP Analyzer API Integration\n');
  console.log(`API URL: ${API_URL}\n`);

  const tests = [
    ['Health Check', `${API_URL}/health`],
    ['API Info', `${API_URL}/`],
    ['Players List', `${API_URL}/players?limit=5`],
    ['Machines List', `${API_URL}/machines?limit=5`],
  ];

  let passed = 0;
  let failed = 0;

  for (const [name, url] of tests) {
    const result = await testEndpoint(name, url);
    if (result) passed++;
    else failed++;
  }

  console.log(`\n${'='.repeat(50)}`);
  console.log(`Tests Passed: ${passed}/${tests.length}`);
  console.log(`Tests Failed: ${failed}/${tests.length}`);
  console.log(`${'='.repeat(50)}`);

  if (failed === 0) {
    console.log('\n✓ All API integration tests passed!');
    console.log('\nFrontend is ready at: http://localhost:3000');
    console.log('API documentation: http://localhost:8000/docs');
  } else {
    console.log('\n✗ Some tests failed. Check the API server status.');
  }
}

runTests();
