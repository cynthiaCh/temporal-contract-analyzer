// Test script to reproduce the issue
// This simulates the current behavior and shows what might be wrong

class MockHost {
  constructor() {
    this.checkCount = 0;
  }
  
  check(token) {
    // Simulate service that reports pending multiple times before becoming ready
    this.checkCount++;
    console.log(`Check call #${this.checkCount} for token ${token}`);
    
    if (this.checkCount <= 3) {
      // Report pending for first few calls
      return Promise.resolve(false);
    } else {
      // Report ready after a few pending calls
      return Promise.resolve(true);
    }
  }
  
  schedule(callback) {
    // Simulate scheduling a retry
    console.log("Scheduling retry...");
    return setTimeout(callback, 100);
  }
  
  cancel(timer) {
    // Simulate canceling a retry
    console.log("Canceling timer");
    clearTimeout(timer);
  }
  
  publish(state) {
    // Mock publish function
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

// Wait a bit to see what happens
setTimeout(() => {
  console.log("Test completed");
}, 1000);