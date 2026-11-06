Updated [usePreparation.js](/workspace/src/usePreparation.js) so the download dialog retries pending preparation and adds the file to `completed` only after a ready response. Closing, reopening, or unmounting cancels scheduled retries and prevents stale results from completing a later visit.

Syntax checks and a controlled hook test passed for pending-to-ready, close, reopen, and unmount flows.