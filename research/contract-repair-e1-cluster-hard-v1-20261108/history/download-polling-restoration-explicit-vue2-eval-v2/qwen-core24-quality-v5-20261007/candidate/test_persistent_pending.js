// Test to simulate potential issue with multiple pending states
import { WorkspaceJob } from './src/session.js';

// Mock host that simulates a problematic scenario
const mockHost = {
  check: (token) => {
    console.log(`Checking token: ${token}`);
    // Simulate many pending states before ready
    return Promise.resolve(false); // Always return pending (this might be the issue)
  },
  schedule: (callback) => {
    console.log('Scheduling retry');
    return setTimeout(callback, 10);
  },
  cancel: (timer) => {
    console.log('Cancelling timer');
    clearTimeout(timer);
  },
  publish: (state) => {
    console.log('Publishing state:', JSON.stringify(state, null, 2));
  }
};

console.log('=== Testing WorkspaceJob with persistent pending ===');

const job = new WorkspaceJob(mockHost, 'test-token', (state) => {
  console.log('Received state update:');
  console.log(JSON.stringify(state, null, 2));
});

job.start();

// This should keep retrying but let's see what happens
setTimeout(() => {
  console.log('\n=== Test completed - should keep retrying ===');
}, 100);