"""Verify selective checklist delivery without changing the experience contrast."""
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from temporal_contract_analyzer import reminders, taxonomy
from temporal_contract_analyzer.cli import main
from temporal_contract_analyzer.core import EvidenceError
from temporal_contract_analyzer.experience_routing import maintenance_prompt


class ClassReminderTests(unittest.TestCase):
    def test_selected_labels_add_only_their_reminders_in_canonical_order(self):
        material = reminders.material(['A', 'L', 'I'])
        self.assertEqual(material['selected_labels'], ['L', 'I', 'A'])
        for code, text in reminders.definition()['by_label'].items():
            self.assertEqual(material['text'].count(text), 1 if code in {'L', 'I', 'A'} else 0)
        self.assertEqual(len(material['reminders_sha256']), 64)

    def test_unknown_does_not_deliver_seven_reminders_and_legacy_labels_are_rejected(self):
        material = reminders.material([])
        self.assertEqual(material['selected'], [])
        self.assertIn('当前分类未知', material['text'])
        for text in reminders.definition()['by_label'].values():
            self.assertNotIn(text, material['text'])
        for codes in (['T4'], ['L', 'L']):
            with self.assertRaises(EvidenceError):
                reminders.material(codes)

    def test_experience_comparison_shares_exact_classified_prefix(self):
        a = maintenance_prompt('Repair task', 'Candidate Contract', obligation_labels=['L', 'A'])
        b = maintenance_prompt('Repair task', 'Candidate Contract', 'Frozen experience', obligation_labels=['L', 'A'])
        self.assertEqual(b, a+'\n\nFrozen experience guidance: verify applicability against the current evidence.\nFrozen experience')
        self.assertIn(reminders.definition()['by_label']['L'], a)
        self.assertIn(reminders.definition()['by_label']['A'], a)
        self.assertNotIn(reminders.definition()['by_label']['F'], a)

    def test_unclassified_call_keeps_common_reminder_without_label_reminders(self):
        expected = ('Task\n\nCandidate automatic Contract: verify its basis against the current source; do not blindly follow unsupported policies.\nContract'
                    '\n\n完成维护任务，保留有依据的既有行为；分别核查启动、接纳、完成、取消及副作用归属。')
        self.assertEqual(maintenance_prompt('Task', 'Contract'), expected)
        self.assertNotIn('七类通用核查提醒', expected)

    def test_wrong_taxonomy_or_missing_class_cannot_silently_change_delivery(self):
        for change in ('version', 'labels'):
            data = reminders.definition()
            if change == 'version':
                data['taxonomy_version'] = 'old-four-class'
            else:
                del data['by_label']['F']
            with patch('temporal_contract_analyzer.reminders.Path.read_text', return_value=json.dumps(data)):
                with self.assertRaises(EvidenceError):
                    reminders.material(['L'])

    def test_cli_validates_visible_classification_and_generates_selected_prompt(self):
        task = 'Stop admitting new input after close.'
        analysis = dict(taxonomy_version=taxonomy.VERSION, contract=task,
                        obligation_labels=[dict(code='L', statement=task,
                                               evidence=[dict(file='TASK', line=1, quote=task)])],
                        facts=[], unknowns=[])
        with tempfile.TemporaryDirectory() as directory:
            source, target = Path(directory)/'public.json', Path(directory)/'prompt.txt'
            source.write_text(json.dumps(dict(task=task, sources={}, analysis=analysis)), encoding='utf-8')
            with redirect_stdout(StringIO()):
                self.assertEqual(main(['maintenance-prompt', str(source), '--output', str(target)]), 0)
            result = target.read_text(encoding='utf-8')
            self.assertIn('[L · 生命周期约束下的接纳与副作用]', result)
            self.assertNotIn('[R ·', result)
            self.assertNotIn('冻结经验正文', result)


if __name__ == '__main__':
    unittest.main()
