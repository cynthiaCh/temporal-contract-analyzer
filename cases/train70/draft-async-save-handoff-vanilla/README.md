# Durable asynchronous saves and invalidatable status hints

Task variant `draft-async-save-handoff-vanilla` shares its source unit with the parent autosave v2 case.
It adds asynchronous acknowledgments, versioned storage, and synchronous navigation callbacks at save start; the core task remains adding debounce.
Submission is required before close; network acknowledgment need not have completed. Status hints must match both the visit and the latest edit.
This is not a strict causal pair differing by one schedule, and it does not inherit the parent's model results.

See the [candidate-visible description](base/README.md), [task metadata](case.json), and [declared schedules](oracle/schedules.json).
The separate draft-async-save-handoff-v1 study report is not distributed in this repository.
For preparation, scoring, and control verification, see the [evaluation guide](../../../../README.md).
