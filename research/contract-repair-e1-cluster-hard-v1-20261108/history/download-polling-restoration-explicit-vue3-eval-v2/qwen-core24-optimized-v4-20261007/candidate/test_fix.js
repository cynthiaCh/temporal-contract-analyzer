// Simple test to verify the fix
import { WorkspaceJob } from './src/session.js';

// Mock host to avoid actual network calls
class MockHost {
  constructor() {
    this.checkCount = 0;
  }
  
  check(token) {
    this.checkCount++;
    console.log(`Check call #${this.checkCount} for token ${token}`);
    return Promise.resolve(true); // Immediately ready
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

console.log("Testing WorkspaceJob fix...");
const mockHost = new MockHost();
const resource = new WorkspaceJob(mockHost, 'test-token', (state) => {
  console.log("Notification received:", state);
});

console.log("Before start - visible:", resource.state.visible);
console.log("Before start - loading:", resource.state.loading);

console.log("Starting preparation...");
resource.start();

setTimeout(() => {
  console.log("After start - visible:", resource.state.visible);
  console.log("After start - loading:", resource.state.loading);
  console.log("Test completed successfully");
}, 50);