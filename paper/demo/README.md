# Synthetic panel demonstration

This deliberately small example was written for the tool demonstration. It is
not a collected open-source incident or an independent benchmark case.

Requirement supplied to the reviewer: once `close()` invalidates the panel's
epoch, a `refresh()` that started in the previous epoch must not call `publish`.
The scenario does not specify repeated refresh arbitration or reopen behavior.

The controlled schedule is:

1. Start `refresh()` with a pending promise returned by `fetchValue()`.
2. Call `close()` while the promise is pending.
3. Resolve the promise to `old result`.
4. Await the continuation and observe calls to `publish`.

`replay.cjs` observes one publication for `unguarded/panel.cjs` and none for
`guarded/panel.cjs`. Its assertions check only this schedule and requirement.
Both variants retain the same three analyzer rule kinds. The guard is supplied
by the reviewer, not synthesized or certified by the analyzer.
