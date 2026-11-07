export function observe(audit, snapshot, receipt) { audit.record({...snapshot,revision:receipt.revision}); }
