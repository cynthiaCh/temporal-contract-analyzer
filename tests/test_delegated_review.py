"""Offline AI-review provenance, citation, isolation, and replay safeguards."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from temporal_contract_analyzer import delegated_review as delegated
from temporal_contract_analyzer import experience_memory as memory, experience_approval as approval, taxonomy
from temporal_contract_analyzer.core import EvidenceError, sha


MODEL=dict(model='synthetic-delegated-review',reasoning_effort='high')
LIMITS=dict(requests=12,seconds=600)
QUOTE='Capture entry before callback reentry.'


class Backend:
    def __init__(self,output):self.output=output;self.calls=[]
    def execute(self,kind,payload,model,limits,directory):
        self.calls.append((kind,deepcopy(payload),deepcopy(model),deepcopy(limits),str(directory)))
        return dict(valid=True,model=deepcopy(model),requests=1,tokens=dict(input_tokens=10,output_tokens=5),output=deepcopy(self.output))


class DelegatedReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.store=self.root/'memory';memory.initialize(self.store)
        self.trajectory=self.root/'trajectory';(self.trajectory/'original').mkdir(parents=True)
        (self.trajectory/'original/main.py').write_text('entry = current\n')
        self.protocol=dict(mode='learning',task=QUOTE,task_id='synthetic-D',source_sha256='a'*64,
                           training_evaluator=dict(command=['SECRET_GOLD_PATH']))
        self.state=dict(status='awaiting_expert_summary',gold_result='SECRET_GOLD_RESULT',attempts=[dict(
            number=i,visible_passed=False,acceptance_passed=False,
            training_result=dict(valid=True,passed=False,feedback='SECRET_GOLD_FEEDBACK'),
            feedback=dict(observations=[dict(check='public-case',passed=False)],regressions=[],unknowns=[],
                          training_acceptance=dict(secret='SECRET_GOLD_ASSERTION')),
            candidate_sources={'main.py':'entry = current\n'}) for i in range(1,4)])
        self.write_state()
        self.source=self.root/'synthetic-source.json';self.source.write_text(json.dumps(dict(rules=[dict(public=QUOTE)])))
        code=sha(self.source.read_bytes())
        self.payload=dict(schema_version=memory.BUNDLE_VERSION_V2,id='synthetic-entry',version='v1',parent_sha256=None,
            taxonomy_version=taxonomy.VERSION,labels=['I'],requires=['entry_snapshot'],excludes=[],
            rules=[dict(id='R01',category='event_relation',body=QUOTE)],
            review=dict(status='candidate',kind='ai_assisted',source_sha256=code,limitations=['Synthetic fixture.']),
            audit=dict(sources=[dict(path=str(self.source),sha256=code)],
                rule_links=[dict(rule_id='R01',source_sha256=code,pointer='/rules/0')],notes=['Synthetic fixture.'],outcome_refs=[]))
        self.bundle=memory.add(self.store,self.payload,[self.source])

    def write_state(self):
        (self.trajectory/'protocol.json').write_text(json.dumps(self.protocol))
        (self.trajectory/'state.json').write_text(json.dumps(self.state))
        if not (self.trajectory/'memory-snapshot.json').exists():
            (self.trajectory/'memory-snapshot.json').write_text(json.dumps(dict(entries=[])))

    def review_output(self,decision='accept',supported=True):
        return dict(decision=decision,reason='Synthetic source-bound review.',rules=[dict(
            rule_id='R01',supported=supported,reason='Original task states this obligation.',
            evidence=[dict(file='TASK',quote=QUOTE)] if supported else [])])

    def failure_output(self,decision='candidate'):
        return dict(decision=decision,reason='Synthetic failure reflection.',confirmed_conclusions=[QUOTE],
            unverified_hypotheses=[],unresolved_behaviors=['The complete repair is still unverified.'],
            experience=dict(labels=['I'],requires=['entry_snapshot'],excludes=[],
                rules=[dict(category='event_relation',body=QUOTE)],limitations=['Synthetic fixture.']) if decision=='candidate' else None,
            rule_evidence=[dict(rule_index=1,evidence=[dict(file='TASK',quote=QUOTE)])] if decision=='candidate' else [])

    def test_public_context_excludes_every_gold_channel(self):
        context=delegated.public_context(self.trajectory)
        self.assertNotIn('SECRET_GOLD',json.dumps(context))
        self.assertEqual(len(context['attempts']),3)
        self.assertEqual(context['attempts'][0]['public_feedback']['observations'][0]['check'],'public-case')
        self.assertEqual(context['sources']['main.py'],'entry = current\n')

    def test_ai_acceptance_never_writes_or_claims_human_decisions(self):
        backend=Backend(self.review_output());directory=self.root/'review'
        result=delegated.review_candidate(backend,self.trajectory,self.store,self.bundle['sha256'],directory,MODEL,LIMITS)
        again=delegated.review_candidate(backend,self.trajectory,self.store,self.bundle['sha256'],directory,MODEL,LIMITS)
        self.assertEqual(result,again);self.assertEqual(len(backend.calls),1)
        self.assertEqual(result['decision'],'accept');self.assertFalse(result['human_reviewed'])
        self.assertEqual(approval.decisions(self.store),[]);self.assertEqual(approval.freeze(self.store)['entries'],[])
        snapshot=delegated.freeze(self.store);self.assertEqual(snapshot['schema_version'],delegated.SNAPSHOT_VERSION)
        self.assertNotIn('expert_decision',snapshot['entries'][0])
        self.assertFalse(snapshot['entries'][0]['ai_review']['human_reviewed'])
        self.assertNotIn('named_operator',json.dumps(snapshot))
        delegated.validate_snapshot(self.store,snapshot)
        self.assertNotIn('SECRET_GOLD',json.dumps(backend.calls[0][1]))

    def test_reject_does_not_enter_ai_snapshot(self):
        backend=Backend(self.review_output('reject',False))
        delegated.review_candidate(backend,self.trajectory,self.store,self.bundle['sha256'],self.root/'review',MODEL,LIMITS)
        self.assertEqual(delegated.freeze(self.store)['entries'],[])

    def test_rejecting_extra_evidence_does_not_revoke_existing_content(self):
        delegated.review_candidate(Backend(self.review_output()),self.trajectory,self.store,self.bundle['sha256'],self.root/'accept',MODEL,LIMITS)
        before=delegated.freeze(self.store)
        delegated.review_candidate(Backend(self.review_output('reject',False)),self.trajectory,self.store,self.bundle['sha256'],self.root/'evidence',MODEL,LIMITS,evidence_only=True)
        self.assertEqual(delegated.freeze(self.store),before)
        self.assertEqual(delegated.decisions(self.store)[-1]['evaluation_method'],'model_evidence_review')

    def test_accept_requires_all_rules_and_exact_public_quotes(self):
        for change in ['unsupported','invented_quote','missing_rule']:
            output=self.review_output()
            if change=='unsupported':output['rules'][0]['supported']=False
            if change=='invented_quote':output['rules'][0]['evidence'][0]['quote']='SECRET_GOLD_ASSERTION'
            if change=='missing_rule':output['rules']=[]
            with self.subTest(change=change),self.assertRaises(EvidenceError):
                delegated.review_candidate(Backend(output),self.trajectory,self.store,self.bundle['sha256'],self.root/change,MODEL,LIMITS)
        self.assertEqual(delegated.decisions(self.store),[])

    def test_interrupted_paid_stage_never_replays(self):
        class Interrupted(Backend):
            def execute(self,*args):self.calls.append(args);raise RuntimeError('Synthetic bridge interruption')
        backend=Interrupted(self.review_output());directory=self.root/'interrupted'
        with self.assertRaises(RuntimeError):
            delegated.review_candidate(backend,self.trajectory,self.store,self.bundle['sha256'],directory,MODEL,LIMITS)
        with self.assertRaisesRegex(EvidenceError,'cannot silently replay'):
            delegated.review_candidate(backend,self.trajectory,self.store,self.bundle['sha256'],directory,MODEL,LIMITS)
        self.assertEqual(len(backend.calls),1)

    def test_failure_lesson_is_ai_candidate_until_separate_review(self):
        backend=Backend(self.failure_output());directory=self.root/'failure'
        result=delegated.reflect_failure(backend,self.trajectory,self.store,directory,MODEL,LIMITS)
        again=delegated.reflect_failure(backend,self.trajectory,self.store,directory,MODEL,LIMITS)
        self.assertEqual(result,again);self.assertEqual(len(backend.calls),1)
        self.assertEqual(result['outcome'],'ai_failure_candidate');self.assertFalse(result['human_reviewed'])
        self.assertEqual(delegated.freeze(self.store)['entries'],[])
        candidate=next(b for b in memory.records(self.store) if b['sha256']==result['candidate_sha256'])
        self.assertEqual(candidate['review']['kind'],'ai_assisted')
        source=memory.source_bytes(self.store,candidate['review']['source_sha256']).decode()
        self.assertIn('ai_failure_reflection',source);self.assertNotIn('SECRET_GOLD',source)
        self.assertNotIn('submitted_by_human',source);self.assertNotIn('expert_failure',source)
        self.assertEqual(json.loads((self.trajectory/'state.json').read_text())['status'],'awaiting_expert_summary')
        delegated.review_candidate(Backend(self.review_output()),self.trajectory,self.store,candidate['sha256'],self.root/'failure-review',MODEL,LIMITS)
        snapshot=delegated.freeze(self.store);self.assertEqual(len(snapshot['entries']),1)
        delegated.validate_snapshot(self.store,snapshot)

    def test_failed_or_testing_trajectories_cannot_manufacture_lessons(self):
        backend=Backend(self.failure_output());self.state['attempts']=self.state['attempts'][:2];self.write_state()
        with self.assertRaises(EvidenceError):delegated.reflect_failure(backend,self.trajectory,self.store,self.root/'failure',MODEL,LIMITS)
        self.protocol['mode']='testing';self.write_state()
        with self.assertRaises(EvidenceError):delegated.public_context(self.trajectory)
        self.assertEqual(backend.calls,[])

    def test_no_update_is_explicit_and_has_no_guidance(self):
        backend=Backend(self.failure_output('no_update'))
        result=delegated.reflect_failure(backend,self.trajectory,self.store,self.root/'failure',MODEL,LIMITS)
        self.assertEqual(result['decision'],'no_update');self.assertIsNone(result['candidate_sha256'])
        self.assertEqual(len(memory.records(self.store)),1)
        same=delegated.record_no_update(self.store,self.trajectory,'No changed guidance.',self.root/'none')
        self.assertEqual(same,delegated.record_no_update(self.store,self.trajectory,'No changed guidance.',self.root/'none'))

    def test_tampered_context_and_human_claim_are_rejected(self):
        delegated.review_candidate(Backend(self.review_output()),self.trajectory,self.store,self.bundle['sha256'],self.root/'review',MODEL,LIMITS)
        snapshot=delegated.freeze(self.store)
        bad=deepcopy(snapshot);bad['human_reviewed']=True
        bad['sha256']=sha(delegated.canonical({k:v for k,v in bad.items() if k!='sha256'}).encode())
        with self.assertRaises(EvidenceError):delegated.validate_snapshot(self.store,bad)
        review=snapshot['entries'][0]['ai_review'];path=self.store/'workflow/ai-review-contexts'/(review['context_sha256']+'.json')
        context=json.loads(path.read_text());context['task']='Changed';path.write_text(json.dumps(context))
        with self.assertRaises(EvidenceError):delegated.validate_snapshot(self.store,snapshot)

    def test_accepted_revision_supersedes_parent_but_old_snapshot_stays_valid(self):
        delegated.review_candidate(Backend(self.review_output()),self.trajectory,self.store,self.bundle['sha256'],self.root/'first-review',MODEL,LIMITS)
        before=delegated.freeze(self.store)
        payload=deepcopy(self.payload);payload.update(version='v2',parent_sha256=self.bundle['sha256'])
        child=memory.add(self.store,payload,[self.source])
        delegated.review_candidate(Backend(self.review_output()),self.trajectory,self.store,child['sha256'],self.root/'child-review',MODEL,LIMITS)
        after=delegated.freeze(self.store)
        self.assertEqual([e['bundle']['sha256'] for e in after['entries']],[child['sha256']])
        delegated.validate_snapshot(self.store,before);delegated.validate_snapshot(self.store,after)

    def test_exact_duplicate_guidance_retains_reviews_without_inflating_snapshot(self):
        delegated.review_candidate(Backend(self.review_output()),self.trajectory,self.store,self.bundle['sha256'],self.root/'first-review',MODEL,LIMITS)
        payload=deepcopy(self.payload);payload['id']='different-case-same-guidance'
        duplicate=memory.add(self.store,payload,[self.source])
        delegated.review_candidate(Backend(self.review_output()),self.trajectory,self.store,duplicate['sha256'],self.root/'duplicate-review',MODEL,LIMITS)
        self.assertEqual(len(delegated.decisions(self.store)),2)
        self.assertEqual(len(delegated.freeze(self.store)['entries']),1)

    def test_receipt_cannot_relabel_a_generation_as_acceptance(self):
        delegated.reflect_failure(Backend(self.failure_output()),self.trajectory,self.store,self.root/'failure',MODEL,LIMITS)
        receipt=delegated.decisions(self.store)[0];old=self.store/'workflow/ai-reviews'/(receipt['sha256']+'.json')
        value={k:v for k,v in receipt.items() if k!='sha256'};value['decision']='accept'
        forged=delegated._seal(value);old.unlink()
        (old.parent/(forged['sha256']+'.json')).write_text(json.dumps(forged))
        with self.assertRaises(EvidenceError):delegated.decisions(self.store)


if __name__=='__main__':unittest.main()
