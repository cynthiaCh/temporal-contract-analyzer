"""Repository-only offline demo: synthetic fixtures, no provider/model/GPU calls."""
import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

REPO=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(REPO),str(REPO/'tests')]
import evolution_fixtures
from test_development_v2 import DevelopmentTests
from test_workflow_v3 import FakeBackend
from temporal_contract_analyzer import experience_memory as memory, experience_approval as approval
from temporal_contract_analyzer import experience_lifecycle as life
from temporal_contract_analyzer.experience_workflow import Workflow
from temporal_contract_analyzer.evolution_backend import NativeBackend


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,required=True)
    args=parser.parse_args();root=args.root.resolve()
    if root.exists():parser.error('Use a new demo directory; existing data is never overwritten')
    root.mkdir(parents=True);evolution_fixtures.synthetic_bench(root/'bench',('source','transfer-a','transfer-b','holdout','boundary'))
    store=root/'memory';memory.initialize(store)
    helper=DevelopmentTests();helper.root=root;helper.store=store
    with patch.dict(os.environ,{'TCA_BENCH_ROOT':str(root/'bench')}),patch.object(NativeBackend,'execute',side_effect=AssertionError('Offline demo forbids native/model execution')):
        config=helper.config();config['visible']=None
        for item in config['cohort']['transfers']:item['visible']=None
        (root/'config.json').write_text(json.dumps(config,indent=2)+'\n')
        loop=Workflow(root/'batch');loop.prepare_config(config);fake=FakeBackend()
        state=loop.run(execute=True,backend=fake)
        assert state['status']=='awaiting_human_review',state
        parent=next(b for b in memory.records(store) if b['sha256']==state['candidate_sha256'])
        rules=deepcopy(parent['rules']);rules[0]['body']+=' Verify the accepted identity during reentry.';rules[0]['category']='verification'
        child=life.edit(store,parent['sha256'],dict(request_id='synthetic-edit',actor='SYNTHETIC_EDITOR_FIXTURE',
            reason='Offline demonstration of the human edit branch.',rules=rules,
            **{k:parent[k] for k in ('labels','requires','excludes')}))
        calls_before=len(fake.calls);loop.run(execute=True,backend=fake)
        assert len(fake.calls)==calls_before
        assert life.metadata(store,child['sha256'])['ai_status']=='not_run'
        assert life.view(store,child['sha256'])['content_review_available']
        assert not any(c['role'] in ('contract_check','candidate_check') for c in fake.calls)
        decision=approval.review_template(store,child['sha256']);decision.update(reviewer='SYNTHETIC_HUMAN_FIXTURE',
            decision='accept',reason='Simulated content review, not actual expert approval.',auto_enable=True,request_id='synthetic-accept')
        for row in decision['rules']:row.update(supported=True,reason='Synthetic fixture only.')
        approval.decide(store,child['sha256'],decision)
        state=loop.run(execute=True,backend=fake);assert state['status']=='enabled',state
        count=len(fake.calls);loop.run(execute=True,backend=fake);assert len(fake.calls)==count
        summary=dict(evidence_kind='Synthetic control-flow demonstration, NOT real repair-effect evidence',
            paid_model_calls=0,parent_sha256=parent['sha256'],edited_sha256=child['sha256'],
            final_state=state['status'],simulated_backend_calls=count,resume_added_calls=0,
            actual_active_in_temporary_store=approval.active(store)[0]['bundle']['sha256'],
            original_batch_candidate_unchanged=json.loads((loop.root/'candidate.json').read_text())['sha256']==parent['sha256'])
        (root/'DEMO.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
