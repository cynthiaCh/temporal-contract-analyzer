# Research archive boundary

The maintained training and testing workflow is documented in [WORKFLOW.md](WORKFLOW.md).
The current experience library uses stable IDs and inline review; see
[experience storage and review](../experience-memory/README.md).

Historical experiments, raw outputs, failed and interrupted runs, scores and
publication material are research records. They are preserved for inspection and
excluded from source exports. Their original paths and execution bindings describe
the environment in which they were produced; they do not provide executable
entrypoints in the current tool. Use the corresponding Git revision and original
environment when inspecting historical methods.

The current tool does not resume retired pipelines or rewrite their results.
New experiments require a fresh preparation through the maintained workflow.


Retired research implementations, implementation-stage plans and superseded
method instructions are removed rather than maintained as alternative workflows.
The independent behavior-probe prototype is no longer part of the tool. Current
execution and everyday agent use are documented in `WORKFLOW.md` and
`PERSONAL_MCP.md`. Historical source identifiers inside frozen provenance remain
attributions, not runnable paths in this checkout.
