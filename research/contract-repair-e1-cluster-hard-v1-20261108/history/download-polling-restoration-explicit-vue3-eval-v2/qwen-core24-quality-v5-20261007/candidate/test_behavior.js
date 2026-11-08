// Test to understand the current behavior
// This is a simplified test to understand the flow

// Mock host that simulates the service behavior
class MockHost {
  constructor() {
    this.checkCount = 0;
  }
  
  check(token) {
    this.checkCount++;
    console.log(`Host check called for token: ${token}, call #${this.checkCount}`);
    
    // Simulate service behavior - can return pending (false) multiple times before ready (true)
    if (this.checkCount <= 3) {
      console.log('  Service returning: false (pending)');
      return Promise.resolve(false);
    } else {
      console.log('  Service returning: true (ready)');
      return Promise.resolve(true);
    }
  }
  
  schedule(callback) {
    console.log('Host schedule called - will run callback in next turn');
    return setTimeout(callback, 10); // Small delay to simulate async
  }
  
  cancel(timer) {
    console.log('Host cancel called');
    clearTimeout(timer);
  }
  
  publish(state) {
    console.log('Host publish called with state:', state);
  }
}

// Test the current behavior
function testCurrentBehavior() {
  console.log('=== Testing Current Behavior ===');
  
  // Import the actual classes
  const { WorkspaceJob } = require('./src/session.js');
  
  const host = new MockHost();
  const notify = (state) => console.log('Notify called with:', state);
  
  console.log('Creating WorkspaceJob...');
  const job = new WorkspaceJob(host, 'test-token', notify);
  
  console.log('Starting preparation...');
  job.start();
  
  // Wait for completion
  setTimeout(() => {
    console.log('Test completed');
  }, 100);
}

// Run the test
try {
  testCurrentBehavior();
} catch (error) {
  console.error('Error in test:', error);
}