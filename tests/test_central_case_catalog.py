"""Central roster migration support without executing benchmark code."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from temporal_contract_analyzer import case_catalog


class CentralRosterTests(unittest.TestCase):
    def test_migrated_case_reads_only_registered_public_input(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root/'benchmark').mkdir()
            case = root/'case-clusters/example/arms/development'
            (case/'base/src').mkdir(parents=True)
            (case/'prompts').mkdir()
            (case/'base/src/session.js').write_text('export const x = 1;')
            (case/'prompts/task.md').write_text('Preserve shared cache ownership.')
            (case/'case.json').write_text(json.dumps(dict(id='development',framework=dict(runtime='vue3'),
                diagnostic_tasks=dict(maintenance=dict(core_prompt='prompts/task.md')))))
            (root/'benchmark/swe-tempoc.json').write_text(json.dumps(dict(cases=[dict(case_id='development',
                manifest='case-clusters/example/arms/development/case.json')])))
            with patch.dict(os.environ, {'TCA_BENCH_ROOT':str(root)}), patch.object(case_catalog,'ROOT',root):
                selected=case_catalog.case_input('development')
                self.assertEqual(selected['task'],'Preserve shared cache ownership.')
                self.assertEqual(Path(selected['candidate']), (case/'base').resolve())
                self.assertEqual(selected['case_record']['prior_exposure'],'exposed_benchmark_registry')
                self.assertEqual(selected['case_record']['adapter'],'legacy-js')


if __name__ == '__main__':
    unittest.main()
