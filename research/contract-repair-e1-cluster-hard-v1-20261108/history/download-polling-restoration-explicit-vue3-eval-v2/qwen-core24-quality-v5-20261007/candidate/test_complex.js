// Let me create a test that simulates a more complex scenario
// to see if there are any edge cases

class MockHost {
  constructor() {
    this.checkCount = 0;
    this.pendingCount = 0;
  }
  
  check(token) {
    this.checkCount++;
    console.log(`Host check called for token: ${token}, call #${this.checkCount}`);
    
    // Simulate service that reports pending multiple times
    if (this.checkCount <= 5) {
      console.log('  Service returning: false (pending)');
      return Promise.resolve(false);
    } else {
      console.log('  Service returning: true (ready)');
      return Promise.resolve(true);
    }
  }
  
  schedule(callback) {
    console.log('Host schedule called - will run callback in next turn');
    return setTimeout(callback, 1); // Very small delay
  }
  
  cancel(timer) {
    console.log('Host cancel called');
    clearTimeout(timer);
  }
  
  publish(state) {
    console.log('Host publish called with:', JSON.stringify(state, null, 2));
  }
}

// Test with a more complex scenario
function testComplexBehavior() {
  console.log('=== Testing Complex Behavior ===');
  
  const { WorkspaceJob } = require('./src/session.js');
  
  const host = new MockHost();
  const notify = (state) => console.log('Notify called with:', state);
  
  console.log('Creating WorkspaceJob...');
  const job = new WorkspaceJob(host, 'complex-token', notify);
  
  console.log('Starting preparation...');
  job.start();
  
  // Wait for completion
  setTimeout(() => {
    console.log('\n=== Test completed ===');
  }, 50);
}

testComplexBehavior();