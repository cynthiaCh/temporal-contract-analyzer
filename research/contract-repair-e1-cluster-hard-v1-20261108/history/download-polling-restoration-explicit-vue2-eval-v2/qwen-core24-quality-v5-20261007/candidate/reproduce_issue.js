// Reproduction script to understand the current behavior
import { WorkspaceJob } from './src/session.js';

// Mock host for testing
const mockHost = {
  check: (token) => {
    console.log(`Checking token: ${token}`);
    // Simulate pending status first, then ready
    if (mockHost.checkCount === 0) {
      mockHost.checkCount++;
      return Promise.resolve(false); // Pending
    } else {
      return Promise.resolve(true); // Ready
    }
  },
  schedule: (callback) => {
    console.log('Scheduling retry');
    return setTimeout(callback, 100);
  },
  cancel: (timer) => {
    console.log('Cancelling timer');
    clearTimeout(timer);
  },
  publish: (state) => {
    console.log('Publishing state:', state);
  }
};

mockHost.checkCount = 0;

// Test the current behavior
console.log('Testing WorkspaceJob behavior...');

const job = new WorkspaceJob(mockHost, 'test-token', (state) => {
  console.log('Received state update:', state);
});

job.start();