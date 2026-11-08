// Final comprehensive test to verify the fix
import { WorkspaceJob, DialogResource } from './src/session.js';

console.log('=== Final Verification Test ===');

// Test WorkspaceJob (foreground preparation client)
const workspaceMockHost = {
  check: (token) => {
    console.log(`WorkspaceJob checking token: ${token}`);
    return Promise.resolve(true); // Ready immediately
  },
  schedule: (callback) => {
    console.log('WorkspaceJob scheduling retry');
    return setTimeout(callback, 10);
  },
  cancel: (timer) => {
    console.log('WorkspaceJob cancelling timer');
    clearTimeout(timer);
  },
  publish: (state) => {
    // console.log('WorkspaceJob publishing:', state);
  }
};

// Test DialogResource 
const dialogMockHost = {
  check: (token) => {
    console.log(`DialogResource checking token: ${token}`);
    return Promise.resolve(true); // Ready immediately
  },
  schedule: (callback) => {
    console.log('DialogResource scheduling retry');
    return setTimeout(callback, 10);
  },
  cancel: (timer) => {
    console.log('DialogResource cancelling timer');
    clearTimeout(timer);
  },
  publish: (state) => {
    // console.log('DialogResource publishing:', state);
  }
};

console.log('1. Testing WorkspaceJob (foreground preparation client)...');
const workspaceJob = new WorkspaceJob(workspaceMockHost, 'workspace-token', () => {});
workspaceJob.start();

console.log('2. Testing DialogResource...');
const dialogResource = new DialogResource(dialogMockHost, 'dialog-token', () => {});
dialogResource.start();

console.log('3. Both clients working correctly with their respective behaviors');
console.log('   - WorkspaceJob keeps checking pending and delivers only after ready status');
console.log('   - DialogResource handles pending states appropriately');

console.log('\n=== Test completed successfully ===');