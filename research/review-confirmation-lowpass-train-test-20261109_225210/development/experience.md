R01 [Applicability]
Apply this guidance where edits are deferred, accepted text must be durable before a departure or submission returns, accepted actions retain entry values, synchronous callbacks may reenter, and durable results have a different lifetime from visible feedback.

R02 [Event relation]
For each editing burst, retain only its latest value until the quiet interval expires. When accepted deferred text must settle at a departure boundary, bind the write to the departing document, consume that batch before invoking synchronous work, and let any nested navigation or later edit remain authoritative.

R03 [Event relation]
On an accepted submission, fix the selected document and text at action entry. Ensure that accepted text is durable before recording the result, while synchronous integrations may change the current view; still return and retain the entry-bound result, and treat later input as separate work.

R04 [Preservation]
Keep visible confirmation separate from the durable accepted result: show it only while the exact accepting visit remains current. A replacement, closure, or reopening of the same document is a different visit and must not revive the earlier visit's feedback.

R05 [Exclusion]
Do not extend this editor maintenance into the adjacent preview: retain its existing quiet interval, discard unpublished preview work when hidden, and allow later preview input to schedule normally. Preserve synchronous public and injected contracts and independent services.

R06 [Verification]
Verify the candidate across quiet bursts, boundary departures, nested navigation, nested editing, submission, confirmation validity, disposal, and preview reuse. Confirm required durable outcomes and live feedback both remain, and record any remaining losses without attributing them to a particular implementation choice.
