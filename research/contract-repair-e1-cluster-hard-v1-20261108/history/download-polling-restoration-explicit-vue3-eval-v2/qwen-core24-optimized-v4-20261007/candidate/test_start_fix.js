// Test to verify the fix for WorkspaceJob start() method

class MockHost {
  constructor() {
    this.checkCount = 0;
  }
  
  check(token) {
    this.checkCount++;
    console.log(`Check call #${this.checkCount} for token ${token}`);
    // Always return pending first, then ready
    return Promise.resolve(false);
  }
  
  schedule(callback) {
    console.log("Scheduling retry...");
    return setTimeout(callback, 10);
  }
  
  cancel(timer) {
    console.log("Canceling timer");
    clearTimeout(timer);
  }
  
  publish(state) {
    console.log("Publishing state:", state);
  }
}

// Test the current implementation vs fixed implementation
import { WorkspaceJob } from './src/session.js';

console.log("=== Testing current WorkspaceJob implementation ===");

const mockHost = new MockHost();
const resource = new WorkspaceJob(mockHost, 'test-token', (state) => {
  console.log("Notification received:", state);
});

console.log("Before start - visible:", resource.state.visible);
console.log("Before start - loading:", resource.state.loading);

console.log("Starting preparation...");
resource.start();

// Wait to see the behavior
setTimeout(() => {
  console.log("After start - visible:", resource.state.visible);
  console.log("After start - loading:", resource.state.loading);
  console.log("Test completed");
}, 50);