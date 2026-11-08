// Test script to understand current behavior
// This simulates the host.check() behavior to see how the client handles pending states

class MockHost {
  constructor() {
    this.checkCount = 0;
  }
  
  check(token) {
    // Simulate service that returns pending multiple times before ready
    this.checkCount++;
    console.log(`Check called for token ${token}, count: ${this.checkCount}`);
    
    if (this.checkCount <= 3) {
      // Return pending status for first few calls
      return Promise.resolve(false);
    } else {
      // Return ready status after a few pending calls
      return Promise.resolve(true);
    }
  }
  
  schedule(callback) {
    // Simulate scheduling a retry
    return setTimeout(callback, 100);
  }
  
  cancel(timer) {
    clearTimeout(timer);
  }
  
  publish(state) {
    console.log('Publishing state:', state);
  }
}

// Import the actual implementation
import { WorkspaceJob, DialogResource } from './src/session.js';

// Test WorkspaceJob behavior
console.log("Testing WorkspaceJob behavior with multiple pending states...");

const mockHost = new MockHost();
const notify = (state) => console.log('Notification:', state);

const job = new WorkspaceJob(mockHost, 'test-token', notify);

// Start the process
job.start();

// Wait a bit to see the behavior
setTimeout(() => {
  console.log("Test completed");
}, 500);