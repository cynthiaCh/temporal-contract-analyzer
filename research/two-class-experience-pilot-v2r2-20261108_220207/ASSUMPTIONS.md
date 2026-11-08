# Offline fix after a stopped execution

No further paid calls in this turn after v2r1's first infrastructure/policy false-positive. Preserve all prior snapshots and counts. This directory contains the actual corrected read-command parser and typed response code for review and offline verification, not a restarted batch. Candidate data, scorer, role/time/request caps and production/global configuration remain unchanged.

The exact denied command only read candidate docs and discarded stderr to /dev/null; its rejection was a grammar compatibility defect, not evidence of a namespace escape. Permit precisely that discard plus || true; keep writes to other paths, execution/substitution, network commands and outside-candidate reads denied. Publish supported read grammar to the extraction actor. No model retries or implicit supplementation.
