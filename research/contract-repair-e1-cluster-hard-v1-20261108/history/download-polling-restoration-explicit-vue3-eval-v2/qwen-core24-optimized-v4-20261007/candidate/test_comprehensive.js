// More comprehensive test to understand the issue

class MockHost {
  constructor() {
    this.checkCount = 0;
    this.pendingCalls = 0;
  }
  
  check(token) {
    this.checkCount++;
    console.log(`Check call #${this.checkCount} for token ${token}`);
    
    // Simulate service that reports pending multiple times before becoming ready
    if (this.checkCount <= 2) {
      return Promise.resolve(false); // pending
    } else {
      return Promise.resolve(true); // ready
    }
  }
  
  schedule(callback) {
    console.log("Scheduling retry...");
    return setTimeout(callback, 50);
  }
  
  cancel(timer) {
    console.log("Canceling timer");
    clearTimeout(timer);
  }
  
  publish(state) {
    console.log("Publishing state:", state);
  }
}

// Test the current implementation
import { WorkspaceJob } from './src/session.js';

const mockHost = new MockHost();
const resource = new WorkspaceJob(mockHost, 'test-token', (state) => {
  console.log("Notification received:", state);
});

console.log("Starting preparation...");
resource.start();

// Wait to see the full process
setTimeout(() => {
  console.log("Test completed");
  console.log(`Total check calls: ${mockHost.checkCount}`);
}, 500);