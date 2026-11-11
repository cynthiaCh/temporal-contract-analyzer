"""Synthetic incremental content reviews only; no actual expert or model actions."""
from contextlib import redirect_stdout
from copy import deepcopy
from io import StringIO
import json
from pathlib import Path
import shutil
import subprocess
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import build_opener, ProxyHandler, Request

import test_experience_memory as fixtures
from temporal_contract_analyzer import experience_memory as memory, experience_approval as approval
from temporal_contract_analyzer.core import EvidenceError, canonical
from temporal_contract_analyzer.cli import main
from temporal_contract_analyzer.memory_review import ReviewServer


class IncrementalReviewTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixtures.MemoryTests('test_storage_preserves_single_source_body_and_evidence')
        self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
        self.store=self.fixture.store
        payload=deepcopy(self.fixture.payload)
        for i in (6,7):
            payload['rules'].append(dict(id=f'R{i:02d}',category='preservation',body=f'Synthetic retained obligation {i}.'))
            payload['audit']['rule_links'].append(dict(rule_id=f'R{i:02d}',source_sha256=payload['review']['source_sha256'],pointer='/rules/0'))
        self.parent=memory.add(self.store,payload,[self.fixture.source])
        self.parent_request=dict(reviewer='SYNTHETIC_PARENT_REVIEWER',decision='accept',scope='research',
            reason='Synthetic accepted source findings, not real expert approval.',
            rules=[dict(rule_id=r['id'],supported=True,reason='Synthetic parent '+r['id']) for r in self.parent['rules']])
        self.parent_decision=approval.decide(self.store,self.parent['sha256'],self.parent_request)
        self.payload={k:deepcopy(v) for k,v in self.parent.items() if k in memory.FIELDS}
        self.payload.update(schema_version=memory.BUNDLE_VERSION_V2,version='child-v2',parent_sha256=self.parent['sha256'])
        self.payload['review']['status']='candidate'
        self.payload['rules'][1]['body']='Synthetic revised entry relation: capture before reentry.'
        self.child=self.add(self.payload)

    def add(self,payload):
        return memory.add(self.store,payload,[self.fixture.source])

    def request(self,bundle=None):
        value=approval.review_template(self.store,(bundle or self.child)['sha256'])
        value.update(reviewer='SYNTHETIC_CHILD_REVIEWER',decision='accept',reason='Synthetic explicit delta review.')
        for rule in value['rules']:
            rule.update(supported=True,reason='Synthetic new finding '+rule['rule_id'])
        return value

    def files(self):
        return {p.name:p.read_bytes() for p in (self.store/'decisions').glob('*.json')}

    def test_only_changed_rule_requires_input_and_parent_findings_are_audited(self):
        plan=approval.review_plan(self.store,self.child['sha256'])
        self.assertEqual(plan['required_rule_ids'],['R02'])
        self.assertEqual(plan['inherited_rule_ids'],['R01','R03','R04','R05','R06','R07'])
        before=(self.store/'records'/(self.child['sha256']+'.json')).read_bytes()
        request=self.request();self.assertEqual(len(request['rules']),1)
        saved=approval.decide(self.store,self.child['sha256'],request)
        self.assertEqual(saved['schema_version'],'experience-expert-decision-v2')
        self.assertEqual(len(saved['rules']),7)
        for finding in saved['rules']:
            if finding['rule_id']=='R02':
                self.assertNotIn('inherited_from',finding)
            else:
                self.assertEqual(finding['reason'],'Synthetic parent '+finding['rule_id'])
                self.assertEqual(finding['inherited_from'],dict(parent_sha256=self.parent['sha256'],
                    decision_sha256=self.parent_decision['sha256'],rule_id=finding['rule_id']))
        self.assertEqual(approval.decisions(self.store)[-1],saved)
        self.assertEqual(approval.active(self.store),[])
        self.assertEqual((self.store/'records'/(self.child['sha256']+'.json')).read_bytes(),before)
        self.assertEqual(approval.review_plan(self.store,self.child['sha256'])['mode'],'full')

    def test_missing_changed_finding_forged_inheritance_and_unknown_ids_rejected(self):
        for change in ('missing','unknown','invalid_id','duplicate','forged','base','unsupported','scope'):
            request=self.request()
            if change=='missing':request['rules']=[]
            elif change=='unknown':request['rules'][0]['rule_id']='R99'
            elif change=='invalid_id':request['rules'][0]['rule_id']=[]
            elif change=='duplicate':request['rules']*=2
            elif change=='forged':request['rules'][0]['inherited_from']={'rule_id':'R02'}
            elif change=='base':request['inherit_from']['decision_sha256']='a'*64
            elif change=='unsupported':request['rules'][0]['supported']=False
            else:request['scope']='exploratory'
            before=self.files()
            with self.subTest(change=change),self.assertRaises(EvidenceError):
                approval.decide(self.store,self.child['sha256'],request)
            self.assertEqual(self.files(),before)

    def test_changed_labels_conditions_boundaries_and_global_evidence_force_full_review(self):
        for change in ('labels','requires','excludes','taxonomy','boundary','boundary_evidence','outcomes'):
            payload=deepcopy(self.payload);payload['version']='change-'+change
            if change=='labels':payload['labels']=['L']
            elif change=='requires':payload['requires'].append('inline_reentry')
            elif change=='excludes':payload['excludes']=['discard_boundary_policy']
            elif change=='taxonomy':payload.update(taxonomy_version=memory.LEGACY_TAXONOMY,labels=['T3'])
            elif change=='boundary':payload['rules'][0]['body']='Synthetic different applicability.'
            elif change=='boundary_evidence':payload['audit']['rule_links'][0]['pointer']='/rules/1'
            else:payload['audit']['outcome_refs']=[dict(source_sha256=payload['review']['source_sha256'],pointer='/rules/0')]
            bundle=self.add(payload);plan=approval.review_plan(self.store,bundle['sha256'])
            with self.subTest(change=change):
                self.assertEqual(plan['mode'],'full')
                self.assertEqual(len(plan['required_rule_ids']),7)
                self.assertTrue(plan['shared_context_changes'])
                request=self.request();request['rules']=[dict(rule_id='R02',supported=True,reason='Synthetic.')]
                with self.assertRaises(EvidenceError):approval.decide(self.store,bundle['sha256'],request)

    def test_rule_evidence_change_requires_that_rule_too(self):
        payload=deepcopy(self.payload);payload['version']='new-evidence'
        payload['audit']['rule_links'][2]['pointer']='/rules/1'
        child=self.add(payload);plan=approval.review_plan(self.store,child['sha256'])
        self.assertEqual(plan['required_rule_ids'],['R02','R03'])
        self.assertEqual(len(plan['inherited_rule_ids']),5)
        saved=approval.decide(self.store,child['sha256'],self.request(child))
        self.assertNotIn('inherited_from',saved['rules'][2])

    def test_reviewer_can_override_an_unchanged_rule_without_reviewing_every_rule(self):
        request=self.request();request['decision']='revise'
        request['rules'].append(dict(rule_id='R03',supported=False,reason='Synthetic interaction needs review.'))
        saved=approval.decide(self.store,self.child['sha256'],request)
        self.assertEqual(sum('inherited_from' in r for r in saved['rules']),5)
        self.assertFalse(saved['rules'][2]['supported'])
        self.assertNotIn('inherited_from',saved['rules'][2])
        self.assertEqual(approval.review_plan(self.store,self.child['sha256'])['mode'],'full')

    def test_stale_parent_acceptance_rejection_or_revision_blocks_old_form(self):
        request=self.request()
        for decision in ('revise','reject','accept'):
            update=deepcopy(self.parent_request);update['decision']=decision
            approval.decide(self.store,self.parent['sha256'],update)
            before=self.files()
            with self.subTest(decision=decision),self.assertRaises(EvidenceError):
                approval.decide(self.store,self.child['sha256'],request)
            self.assertEqual(self.files(),before)
        fresh=approval.review_plan(self.store,self.child['sha256'])
        self.assertNotEqual(fresh['inherit_from'],request['inherit_from'])
        self.assertEqual(fresh['required_rule_ids'],['R02'])

    def test_self_consistent_digest_cannot_launder_modified_parent_finding(self):
        saved=approval.decide(self.store,self.child['sha256'],self.request())
        old=self.store/'decisions'/f"{saved['sequence']:08d}-{saved['sha256']}.json"
        saved['rules'][2]['reason']='Forged replacement of the actual parent finding'
        saved['sha256']=memory.digest(canonical({k:v for k,v in saved.items() if k!='sha256'}))
        new=old.with_name(f"{saved['sequence']:08d}-{saved['sha256']}.json")
        old.unlink();new.write_text(json.dumps(saved))
        with self.assertRaisesRegex(EvidenceError,'Inherited findings differ'):approval.decisions(self.store)

    def test_chained_inheritance_and_frozen_v2_decision_keep_historical_provenance(self):
        first=approval.decide(self.store,self.child['sha256'],self.request())
        payload={k:deepcopy(v) for k,v in self.child.items() if k in memory.FIELDS}
        payload.update(version='grandchild-v3',parent_sha256=self.child['sha256'])
        payload['rules'][4]['body']='Synthetic revised verification.'
        grandchild=self.add(payload);plan=approval.review_plan(self.store,grandchild['sha256'])
        self.assertEqual(plan['required_rule_ids'],['R05'])
        saved=approval.decide(self.store,grandchild['sha256'],self.request(grandchild))
        self.assertEqual(saved['rules'][2]['inherited_from']['decision_sha256'],first['sha256'])
        from evolution_fixtures import synthetic_screen
        synthetic_screen(self.store,grandchild['sha256'])
        approval.activate(self.store,grandchild['sha256'],None,'SYNTHETIC_OPERATOR')
        frozen=approval.freeze(self.store)
        revoked=deepcopy(self.parent_request);revoked['decision']='reject'
        approval.decide(self.store,self.parent['sha256'],revoked)
        self.assertEqual(approval.validate_snapshot(self.store,frozen),frozen)
        tampered=deepcopy(frozen);d=tampered['entries'][0]['expert_decision'];d['rules'][0]['reason']='TAMPERED'
        d['sha256']=memory.digest(canonical({k:v for k,v in d.items() if k!='sha256'}))
        tampered['sha256']=memory.digest(canonical({k:v for k,v in tampered.items() if k!='sha256'}))
        with self.assertRaises(EvidenceError):approval.validate_snapshot(self.store,tampered)

    def test_cli_template_is_incremental_with_explicit_full_review_option(self):
        for full,count in ((False,1),(True,7)):
            out=StringIO();args=['experience-memory','review-template',self.child['sha256'],'--store',str(self.store)]
            if full:args.append('--full')
            with redirect_stdout(out):self.assertEqual(main(args),0)
            request=json.loads(out.getvalue());self.assertEqual(len(request['rules']),count)
            self.assertEqual('inherit_from' in request,not full)
            self.assertEqual(request['reviewer'],'')
            self.assertTrue(all(r['supported'] is False for r in request['rules']))
        self.assertEqual(len(approval.decisions(self.store)),1)

    def test_http_partial_review_requires_changed_rule_and_saves_references(self):
        server=ReviewServer(self.store);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        opener=build_opener(ProxyHandler({}));base=server.url+'/api/records/'+self.child['sha256']
        try:
            with opener.open(base,timeout=5) as response:data=json.load(response)
            self.assertEqual(data['review_plan']['required_rule_ids'],['R02'])
            body=dict(reviewed=True,activate=False,expected_current=None,decision=self.request())
            invalid=deepcopy(body);invalid['decision']['rules']=[]
            def post(value):
                return opener.open(Request(base+'/decision',data=json.dumps(value).encode(),
                    headers={'Content-Type':'application/json','X-TCA-Request':'local'}),timeout=5)
            with self.assertRaises(HTTPError):post(invalid)
            self.assertEqual(len(approval.decisions(self.store)),1)
            with post(body) as response:
                result=json.load(response)
            self.assertFalse(result['active']);self.assertFalse(result['default_active'])
            self.assertEqual(sum('inherited_from' in r for r in result['decision']['rules']),6)
            with opener.open(base,timeout=5) as response:saved=json.load(response)
            self.assertEqual(saved['decisions'][-1],result['decision'])
        finally:
            server.shutdown();server.server_close();thread.join(3)

    @unittest.skipUnless(shutil.which('node'),'Browser DOM fixture needs existing Node; no installation')
    def test_browser_form_only_submits_changed_rule_and_can_switch_to_full(self):
        data=dict(bundle=self.child,activation=approval.activation_options(self.store,self.child['sha256']),
            review_plan=approval.review_plan(self.store,self.child['sha256']),decisions=[])
        saved=approval.decide(self.store,self.child['sha256'],self.request())
        readonly=dict(data,review_plan=approval.review_plan(self.store,self.child['sha256']),decisions=[saved])
        fixture=Path(__file__).with_name('memory_review_dom_fixture.cjs')
        source=Path(__file__).resolve().parent.parent/'temporal_contract_analyzer/web/memory-review.js'
        result=subprocess.run(['node',str(fixture)],input=json.dumps(dict(source=str(source),data=data,readonly=readonly)),
            capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn('incremental DOM passed',result.stdout)

