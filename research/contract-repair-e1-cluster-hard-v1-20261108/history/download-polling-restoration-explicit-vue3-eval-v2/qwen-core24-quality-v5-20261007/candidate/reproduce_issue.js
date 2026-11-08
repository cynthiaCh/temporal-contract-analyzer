// Reproduction script to understand the current behavior
import { WorkspaceJob, DialogResource } from './src/session.js';

// Mock host for testing
class MockHost {
  constructor() {
    this.checks = 0;
    this.checkResults = [];
  }
  
  check(token) {
    this.checks++;
    console.log(`Check called for token: ${token}, check #${this.checks}`);
    
    // Return a promise that resolves to either true (ready) or false (pending)
    if (this.checkResults.length > 0) {
      const result = this.checkResults.shift();
      console.log(`  Returning: ${result}`);
      return Promise.resolve(result);
    }
    
    // Default behavior - return false (pending) for first few checks, then true (ready)
    if (this.checks <= 2) {
      console.log('  Returning: false (pending)');
      return Promise.resolve(false);
    } else {
      console.log('  Returning: true (ready)');
      return Promise.resolve(true);
    }
  }
  
  schedule(callback) {
    console.log('Schedule called - will run callback in next turn');
    return setTimeout(callback, 0);
  }
  
  cancel(timer) {
    console.log('Cancel called');
    clearTimeout(timer);
  }
  
  // For testing purposes, set specific results
  setResults(results) {
    this.checkResults = [...results];
    this.checks = 0;
  }
}

// Test the current behavior
async function testCurrentBehavior() {
  console.log('=== Testing Current Behavior ===');
  
  const host = new MockHost();
  const notify = (state) => console.log('State updated:', state);
  
  const job = new WorkspaceJob(host, 'test-token', notify);
  
  console.log('Starting preparation...');
  job.start();
  
  // Wait a bit to see the process
  await new Promise(resolve => setTimeout(resolve, 100));
  
  console.log('\n=== Testing with specific results ===');
  
  // Test with a sequence that shows pending states
  host.setResults([false, false, true]); // 2 pending, then ready
  
  const job2 = new WorkspaceJob(host, 'test-token-2', notify);
  console.log('Starting preparation with pending states...');
  job2.start();
  
  await new Promise(resolve => setTimeout(resolve, 100));
}

testCurrentBehavior().catch(console.error);