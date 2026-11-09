"""Finite offline checks of actual frozen wiring, not new experiment results."""
import copy
import json
import unittest
from pathlib import Path
from toolflow import route, canonical, digest

A=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text())


class Wiring(unittest.TestCase):
    def test_registered_text_is_exact_R03_revision(self):
        e=read(A/'frozen-library.json')[0]
        self.assertEqual(e['text'],(A/'experience-source/candidate-experience.md').read_text())
        self.assertEqual(e['text_sha256'],'b560d2b8de712eb51fe331bc53a79bfa0c8e64a6620eda440d66051edc048674')
        self.assertEqual(e['sha256'],digest(canonical({k:v for k,v in e.items() if k!='sha256'})))

    def test_actual_route_can_be_reconstructed_without_management_metadata(self):
        for alias in ['T1','T2']:
            data=read(A/'routing'/alias/'visible-input.json')
            self.assertEqual(set(data),{'task','sources','analysis','semantic_review','library'})
            result=route(data['analysis'],data['sources'],data['library'],task=data['task'],review=data['semantic_review'])
            self.assertEqual(result,read(A/'routing'/alias/'route.json'))
            for key in ['case_id','cluster','history','score','source_case']:
                polluted=copy.deepcopy(data['analysis']);polluted[key]='hidden'
                self.assertEqual(route(polluted,data['sources'],data['library'],task=data['task'],review=data['semantic_review'])['condition'],'AUTO')

    def test_prompt_delta_is_exact_selected_text_or_empty(self):
        for alias in ['T1','T2']:
            a=(A/'prompts'/alias/'A.md').read_text();b=(A/'prompts'/alias/'B.md').read_text()
            decision=read(A/'routing'/alias/'route.json')
            if decision['selected']:
                self.assertEqual(b,a+'\n\n以下为冻结经验原文，按当前证据核查适用性：\n'+read(A/'frozen-library.json')[0]['text'])
            else:self.assertEqual(a,b)
            for forbidden in ['R-task','C-ownership','O-auto1','candidate_sha256','开发成绩','source_case']:
                self.assertNotIn(forbidden,b)

    def test_exact_schedule_and_no_repeated_slot(self):
        rows=read(A/'schedule.json')
        self.assertEqual([(r['alias'],r['arm'],r['repeat']) for r in rows],
                         [('T1','B',1),('T1','A',1),('T2','A',1),('T2','B',1),
                          ('T1','A',2),('T1','B',2),('T2','B',2),('T2','A',2)])
        self.assertEqual(len({r['slot'] for r in rows}),8)
        self.assertTrue(all(r['phase']=='repair' for r in rows))

    def test_score_versions_keep_required_and_forbidden_dimensions(self):
        cases=read(A/'cases.json')
        for c in cases:
            rules=read(A/'materials'/c['alias']/'evaluation/effects.json')['variants']['ungranted']
            standards=read(A/'materials'/c['alias']/'standards.json')
            expected={k:True for k in rules['required']};expected.update({k:False for k in rules['forbidden']})
            self.assertEqual({r['effect']:r['expected'] for r in standards},expected)
            self.assertEqual(len(expected),29 if c['alias']=='T1' else 24)


if __name__=='__main__':unittest.main(verbosity=2)
