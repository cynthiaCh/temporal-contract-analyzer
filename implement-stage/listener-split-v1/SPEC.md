# Listener split specification

Target: split listener-registration-order-vanilla into two simpler local development cases.
Inputs: the analyzer-local listener base and the approved synchronous/asynchronous split.
Outputs: two case manifests, candidate bases, visible contracts, maintenance prompts, bounded references and independent JSON oracles; append-only local case registry exposed through the existing experiment workbench.
Success command: `/usr/bin/python3 -B -m unittest discover -s tests -p test_listener_split.py`.
Base commit: aaa0a2d08c5b55638a803b3654c49199226e4348.
Scope: no model runs, no benchmark or published corpus edits, no analyzer-rule changes, no target A/D outcome. Both cases retain source unit listener-registration-order and are exposed development material.
