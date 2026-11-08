// Test to understand the expected behavior
// Based on the issue: "The archaeological excavation atlas service can now report that a package is still pending before it becomes ready. Update the foreground preparation client so it keeps checking pending preparation and delivers the package only after a ready status."

// The key insight is that the client should:
// 1. Keep checking while pending
// 2. Only deliver package when ready
// 3. This should work even if service reports many pending states

import { WorkspaceJob } from './src/session.js';

// Mock host that simulates the exact scenario described in the issue
const mockHost = {
  check: (token) => {
    console.log(`[CHECK] Checking token: ${token}`);
    // Simulate service that reports pending multiple times before ready
    if (mockHost.checkCount < 5) {
      mockHost.checkCount++;
      console.log(`  -> Service reports PENDING (check #${mockHost.checkCount})`);
      return Promise.resolve(false); // Pending
    } else {
      console.log(`  -> Service reports READY`);
      return Promise.resolve(true); // Ready
    }
  },
  schedule: (callback) => {
    console.log('[SCHEDULE] Scheduling retry callback');
    return setTimeout(callback, 10);
  },
  cancel: (timer) => {
    console.log('[CANCEL] Cancelling timer');
    clearTimeout(timer);
  },
  publish: (state) => {
    console.log('[PUBLISH] State published:', JSON.stringify({
      visible: state.visible,
      loading: state.loading,
      retryScheduled: state.retryScheduled,
      checkCount: state.checkCount,
      completed: state.completed.length > 0,
      token: state.token
    }, null, 2));
  }
};

mockHost.checkCount = 0;

console.log('=== Testing the exact scenario from the issue ===');
console.log('Issue: "The archaeological excavation atlas service can now report that a package is still pending before it becomes ready."');
console.log('Expected: Foreground preparation client keeps checking pending preparation and delivers package only after ready status.');
console.log('');

const job = new WorkspaceJob(mockHost, 'test-token', (state) => {
  console.log('[UPDATE] Received state update');
});

job.start();

// Wait to see the full behavior
setTimeout(() => {
  console.log('\n=== Test completed ===');
  console.log('If the client is working correctly, it should have:');
  console.log('1. Checked multiple times while pending');
  console.log('2. Only delivered package when ready');
  console.log('3. Set loading to false and added to completed when ready');
}, 200);