# Web experience workflow v2

Target: start seven-label experience development, review and freezing, then fixed-experience A/B tests from the existing report server.
Inputs: registered candidate/task, explicit model/effort/session timeout, operator reviews, frozen development entry for tests.
Outputs: separate `<report-store>-experience-v2/x-*/manifest.json`, source snapshots, immutable stage materials, model logs/patches, evaluations and review decisions. Historical research remains unchanged.
Base commit: 79e472e286ae0ff5849ba1a1dfd66b601b0cc70d.
Success command: `python3 -B -m unittest discover -s tests -p test_experience_workbench.py`.
Scope: one development case and one reflected entry per campaign; two AUTO, one reflection, two revalidations; tests use B1/A1/A2/B2. Existing Codex runner and registered case oracles; no new dependency, production publication, automatic learning during tests or paid verification calls during implementation.
