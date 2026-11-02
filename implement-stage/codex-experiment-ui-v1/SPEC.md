# Codex experiment workbench

Target: extend the local report center with an experiment page, inspired by the adjacent bench runner. Freeze one candidate directory, scan it once, prepare paired report conditions, run Codex on separate copies, and inspect exact prompts, logs, responses, and file changes.

Inputs: candidate directory, maintenance/review task, conditions, repetitions, explicit model, reasoning effort, timeout, read-only/edit mode.
Current web entry (user-requested simplification): one registered bench case and a model dropdown; resolve base/task automatically and freeze/start with one Run button. Detailed controls are collapsed; directory/task preparation remains a backend API.
Outputs: sibling `<report-store-name>-experiments/<experiment-id>/` with manifest.json, input/, scan report ID, and jobs/<job-id>/{workspace,prompt.md,report.md,events.jsonl,stderr.log,answer.md,result.json,changes.json}.
Success: `python3 -B -m unittest discover -s tests -p 'test_experiment_workbench.py'` and browser integration check.
Base commit: d9d5ea9cad0aa758326c085db96dce2a168a2ec0; initial working tree clean.
Scope: local exploratory experiments; existing bench and Paper 1 remain unchanged. No automatic defect scoring or claimed agent comprehension. Live model calls only follow an explicit Start action. Initial verification uses a clearly labeled fake process, never a research result.
