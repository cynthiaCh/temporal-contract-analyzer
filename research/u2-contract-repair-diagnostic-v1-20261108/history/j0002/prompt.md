# Task

The preparation service can now report that a file is still pending before it becomes ready. Update the file download dialog so it keeps checking pending preparation and delivers the file only after a ready status.


Temporal contract: pending preparation must be polled until ready. While the
foreground preparation remains pending or a retry is scheduled, the dialog
must remain loading and must not report completion. Closing the foreground
dialog invalidates its timer and every in-flight response; reopening starts a
new generation and old responses must remain inert. The adjacent background
export is workspace-owned and continues after its panel closes unless the
authorization suffix explicitly migrates it to dialog ownership.

Work only from the provided candidate workspace; do not inspect repository history, benchmark materials, or the network. For JavaScript self-checks use this exact runtime: /home/sribd/Downloads/wangshu/temporal-contract-bench-git/results/student-case-expansion-runtime/node18/bin/node. Record its --version. Perform relevant self-checks.
