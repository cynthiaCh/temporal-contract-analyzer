// More comprehensive test to understand the issue
import { WorkspaceJob } from './src/session.js';

// Mock host for testing with multiple pending states
const mockHost = {
  check: (token) => {
    console.log(`Checking token: ${token} - check count: ${mockHost.checkCount}`);
    // Simulate multiple pending states before ready
    if (mockHost.checkCount < 3) {
      mockHost.checkCount++;
      console.log('  -> Returning false (pending)');
      return Promise.resolve(false); // Pending
    } else {
      console.log('  -> Returning true (ready)');
      return Promise.resolve(true); // Ready
    }
  },
  schedule: (callback) => {
    console.log('Scheduling retry');
    return setTimeout(callback, 50);
  },
  cancel: (timer) => {
    console.log('Cancelling timer');
    clearTimeout(timer);
  },
  publish: (state) => {
    console.log('Publishing state:', JSON.stringify(state, null, 2));
  }
};

mockHost.checkCount = 0;

console.log('=== Testing WorkspaceJob with multiple pending states ===');

const job = new WorkspaceJob(mockHost, 'test-token', (state) => {
  console.log('Received state update:');
  console.log(JSON.stringify(state, null, 2));
});

job.start();

// Wait a bit to see the full behavior
setTimeout(() => {
  console.log('\n=== Test completed ===');
}, 500);