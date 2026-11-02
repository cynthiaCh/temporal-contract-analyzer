# Temporal behavior probe feasibility

Target: build and exercise a minimal executable probe generator for declared callback APIs, without project-specific test code. Inputs are two local modules, declarative API bindings, and explicit behavioral contracts. Outputs are generated scenario JSON, per-side observations with bounded callback traces, contract evaluations and a before/after report under a new output directory.

Base commit: `4aa463d26cddb1edef9406f9e90e149f8fdbf966`.

Success command: `python3 external-tests/behavior-probe-feasibility-v1/run.py --output external-tests/behavior-probe-feasibility-v1/run-01`.

Scope: development feasibility using already inspected upstream snapshots, not a fresh held-out evaluation. No autonomous natural-language contract inference, arbitrary API discovery, LLM comparison or publication claim. The static analyzer remains frozen at 0.6.9. No new packages or commits. The prototype is a separate CLI in tools/temporal-behavior-probe.
