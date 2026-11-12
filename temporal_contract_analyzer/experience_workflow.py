"""V3 orchestration over the existing development/evaluation runner and scorer."""
from copy import deepcopy
import fcntl
import json
from pathlib import Path
import shutil

from . import archive, taxonomy, experience_memory as memory, experience_approval as approval
from . import experience_updates as updates, experience_checks as checks, experience_lifecycle as life
from . import experience_routing as routing, experience_screening as screening
from .candidate_files import write_files, inventory
from .core import EvidenceError, canonical, sha
from .experience_development import Development, load
from .experience_evaluation import Evaluation
from .evolution_backend import NativeBackend, ROLES

VERSION='experience-development-v3'
VALIDATION='experience-validation-v3'
EVALUATION='experience-evaluation-v3'


class ReviewWithdrawn(EvidenceError):pass
class CandidateCheckFailed(EvidenceError):pass
class ExecutionCancelled(EvidenceError):pass


def backend_for(p):
    if p.get('backend'):
        from .docker_backend import DockerBackend
        return DockerBackend()
    return NativeBackend()


class AutomatedChecks:
    AUTOMATED_CHECKS=True

    def _checked_public_input(self,key,original):
        """Check this task's retained AI receipt at the execution boundary, not per call."""
        directory=self.root/'cases'/key;folder=directory/'analysis'
        checked=load(directory/'approved-visible.json');binding=load(folder/'check-binding.json')
        if checked['task']!=original['task'] or checked['sources']!=original['sources']:
            raise EvidenceError('AI-checked public input differs from the frozen original task/source')
        raw_analysis=load(folder/'raw-analysis.json')
        policy=load(self.root/'protocol.json').get('contract_check_protocol',checks.CONTRACT_V1)
        if binding.get('kind')!='AI' or binding.get('human_acceptance') is not False \
                or binding.get('analysis')!=checked['analysis'] \
                or binding.get('check_protocol',checks.CONTRACT_V1)!=policy \
                or (binding.get('raw_analysis') if policy==checks.CONTRACT_V2 else checked['analysis'])!=raw_analysis \
                or binding.get('source_snapshot_sha256')!=sha(canonical(original['sources']).encode()):
            raise EvidenceError('Public analysis differs from its retained AI/source binding')
        proposal=dict(task=checked['task'],sources=checked['sources'],analysis=raw_analysis)
        if checks.accept_contract(load(folder/'ai-check.json'),proposal,protocol=policy)!=checked:
            raise EvidenceError('Checked analysis differs from its actual AI semantic check')
        if policy==checks.CONTRACT_V2 and load(folder/'analysis-derivation.json')!=checks.contract_derivation(raw_analysis,checked['analysis']):
            raise EvidenceError('Conservative analysis derivation drifted')
        if policy==checks.CONTRACT_V2 and load(folder/'evidence-catalog.json')!=checks.evidence_catalog(proposal):
            raise EvidenceError('Archived evidence catalog drifted')
        return checked

    def _checked_public_inputs(self,p):
        original=load(self.root/'protocol.json')
        for key,c in p['cases'].items():c['visible']=self._checked_public_input(key,original['cases'][key]['visible'])
        for i,b in enumerate(p.get('boundaries',[])):
            b['visible']=self._checked_public_input('boundary-'+str(i+1),original['boundaries'][i]['visible'])

    def verify(self):
        p=super().verify()
        for i,b in enumerate(p.get('boundaries',[]),1):
            approved=self.root/'cases'/('boundary-'+str(i))/'approved-visible.json'
            if approved.exists():b['visible']=load(approved)
        return p

    def _case_protocol(self,p,key,cap=None):
        if key.startswith('boundary-'):
            boundary=p['boundaries'][int(key.split('-')[1])-1]
            result=dict(p);result.update(p['cases']['source']);result.update(boundary)
            if cap is not None:result['session_limits']=dict(requests=cap,seconds=600)
            return result
        return super()._case_protocol(p,key,cap)

    def _analysis_setup(self,p):
        from .preanalysis import analyze_candidate
        # Only newly prepared batches opt in. Missing field means the frozen v1 policy.
        p['contract_check_protocol']=checks.CONTRACT_V2
        for key,c in p['cases'].items():
            directory=self.root/'cases'/key/'analysis';directory.mkdir(parents=True,exist_ok=True)
            if not (directory/'ast-evidence.json').exists():
                full,ast=analyze_candidate(c['visible']['sources'],node=None if p.get('backend') else p['node'])
                archive.atomic_json(directory/'ast-report.json',full);archive.atomic_json(directory/'ast-evidence.json',ast)
            # Supplied analyses are proposals too; their old review never bypasses v3 AI checking.
            approved=self.root/'cases'/key/'approved-visible.json'
            if approved.exists():approved.unlink()
        for i,b in enumerate(p.get('boundaries',[]),1):
            directory=self.root/'cases'/('boundary-'+str(i))/'input'
            write_files(directory,{n:t.encode() for n,t in b['visible']['sources'].items()})
            b.update(input_path=str(directory),candidate_files=inventory({n:t.encode() for n,t in b['visible']['sources'].items()}))
        all_keys=list(p['cases'])+['boundary-'+str(i) for i in range(1,len(p.get('boundaries',[]))+1)]
        p['slots'] += [dict(name='CONTRACT-CHECK-'+k,role='contract_check',case=k,requests=4) for k in all_keys]
        p['roles']=deepcopy(ROLES)
        return 4*len(all_keys)

    def _analyses(self,backend,p):
        all_cases=list(p['cases'].items())+[(f'boundary-{i}',b) for i,b in enumerate(p.get('boundaries',[]),1)]
        for key,c in all_cases:
            target=self.root/'cases'/key/'approved-visible.json'
            if target.exists():
                original=load(self.root/'protocol.json')
                raw=original['boundaries'][int(key.split('-')[1])-1]['visible'] if key.startswith('boundary-') else original['cases'][key]['visible']
                checked=self._checked_public_input(key,raw)
            else:
                self._status('ai_contract_checking',case=key)
                folder=self.root/'cases'/key/'analysis';folder.mkdir(parents=True,exist_ok=True)
                raw=c['visible'];analysis=raw.get('analysis')
                if analysis is None:
                    result=self._session(backend,p,'ANALYSIS-'+key,'analysis',key,
                        (folder/'prompt.md').read_text(),taxonomy.analysis_schema())
                    analysis=result['output'];archive.atomic_json(folder/'raw-analysis.json',analysis)
                else:
                    archive.atomic_json(folder/'raw-analysis.json',analysis)
                archive.atomic_json(folder/'analysis-origin.json',dict(kind='model_generated' if c.get('analysis_needed') else 'supplied_proposal',human_review=False))
                routing.validate_analysis(analysis,raw['task'],raw['sources'])
                visible=dict(task=raw['task'],sources=raw['sources'],analysis=analysis)
                ast=load(folder/'ast-evidence.json') if (folder/'ast-evidence.json').exists() else None
                archive.atomic_json(folder/'preanalysis-retrieval.json',dict(condition='AUTO',experience=None,
                    reason='No independently checked mechanism facts before analysis; avoid circular retrieval and keep old/new common analysis independent of candidate guidance.'))
                policy=p.get('contract_check_protocol',checks.CONTRACT_V1)
                if policy==checks.CONTRACT_V2:archive.atomic_json(folder/'evidence-catalog.json',checks.evidence_catalog(visible))
                result=self._session(backend,p,'CONTRACT-CHECK-'+key,'contract_check',key,
                    checks.contract_prompt(visible,ast,protocol=policy),checks.contract_schema(analysis,visible=visible,protocol=policy))
                archive.atomic_json(folder/'ai-check.json',result['output'])
                checked=checks.accept_contract(result['output'],visible,protocol=policy)
                if policy==checks.CONTRACT_V2:
                    archive.atomic_json(folder/'analysis-derivation.json',checks.contract_derivation(analysis,checked['analysis']))
                archive.atomic_json(folder/'check-binding.json',dict(kind='AI',analysis=checked['analysis'],
                    **(dict(check_protocol=policy,raw_analysis=analysis) if policy==checks.CONTRACT_V2 else {}),
                    source_snapshot_sha256=sha(canonical(raw['sources']).encode()),slot='CONTRACT-CHECK-'+key,
                    historical_guidance='not_supplied',human_acceptance=False))
                archive.atomic_json(target,checked)
            c['visible']=checked

    def _status(self,status,**values):
        state=self.state();state.update(status=status,**values);self.save(state)


class Workflow(AutomatedChecks,Development):
    PROTOCOL=VERSION

    def prepare_config(self,config):
        config=deepcopy(config);limit=config.pop('max_candidate_versions',2);external=config.pop('candidate_sha256',None)
        if type(limit) is not int or not 1<=limit<=20:raise EvidenceError('Declare 1..20 bounded candidate versions before execution')
        super().prepare_config(config);p=self.verify()
        check_cap=self._analysis_setup(p)
        p['slots'].append(dict(name='CANDIDATE-CHECK',role='candidate_check',case='source',requests=4))
        initial=300+p['analysis_cap']+check_cap+4
        p.update(max_candidate_versions=limit,initial_request_cap=initial,
            total_request_cap=initial+(limit-1)*244,global_request_cap=initial+(limit-1)*244,
            external_candidate_sha256=external,check_policy='Separate budgeted semantic model checks; no human intermediate forms')
        p.update(reflection_delta_protocol=updates.DELTA_V2,candidate_check_protocol=checks.CANDIDATE_V2)
        if external is not None and not any(b['sha256']==external for b in memory.records(p['store'])):
            raise EvidenceError('Unknown supplied candidate; prepare against a store containing its immutable record/evidence')
        archive.atomic_json(self.root/'protocol.json',p)
        self._status('prepared',development_done=False,admitted_versions=[])
        self.report();return self.state()

    def sync_review(self):
        state=self.state();p=self.verify()
        if p['schema_version']!=VERSION:return state
        versions=[load(f) for f in (Path(p['store'])/'workflow/versions').glob('*.json') if load(f).get('origin_root')==str(self.root)]
        versions.sort(key=lambda r:(r.get('generation',0),r['candidate_sha256']))
        state['versions']=versions
        if versions and state['status'] not in ('cancelled','infrastructure_error','reflection_incomplete','ai_contract_failed','ai_check_incomplete','budget_exhausted'):
            state['status']=versions[-1]['status']
        self.save(state);return state

    def _all_jobs(self,p):
        root=Path(p.get('origin_root',self.root));jobs=[]
        for file in [root/'state.json']+sorted((root/'validations').glob('*/state.json')):
            state=load(file)
            jobs.extend(dict(j,run_root=str(file.parent),validation_candidate_sha256=state.get('candidate_sha256') if file.parent!=root else None)
                for j in state['jobs'] if not j.get('reused'))
        return jobs

    def _session(self,backend,p,name,role,key,prompt,schema=None,cap=None):
        previous=next((j for j in self.state()['jobs'] if j['slot']==name),None)
        if previous:
            if previous['status']=='valid':return load(self.root/'runs'/name/'result.json')
            raise EvidenceError('Started/incomplete slot cannot be retried; preserve partial archive')
        origin=Path(p.get('origin_root',self.root));auth=life.load(origin/'execution-authorization.json')
        if auth and auth.get('cancelled'):raise ExecutionCancelled('Execution authorization cancelled')
        if not auth:raise EvidenceError('Execution not authorized')
        budget_p=load(origin/'protocol.json');jobs=self._all_jobs(p)
        if any(type(j.get('requests')) is not int for j in jobs):raise EvidenceError('Unknown request accounting blocks further dispatch')
        slot=next(s for s in p['slots'] if s['name']==name)
        if sum(j['requests'] for j in jobs)+(cap or slot['requests'])>budget_p['global_request_cap']:
            raise EvidenceError('Declared workflow budget exhausted')
        if p.get('schema_version')==VALIDATION and role=='repair' and not life.latest_acceptance(p['store'],p['candidate_sha256']):
            raise ReviewWithdrawn('Human acceptance withdrawn during validation; stop remaining slots')
        return super()._session(backend,p,name,role,key,prompt,schema,cap)

    def _store_candidate(self,p):
        target=self.root/'candidate.json'
        if target.exists():
            bundle=load(target);expected=p.get('candidate_sha256') or p.get('external_candidate_sha256') or self.state().get('candidate_sha256')
            if expected and bundle['sha256']!=expected:raise EvidenceError('Candidate snapshot differs from the exact version binding')
            stored=next((b for b in memory.records(p['store']) if b['sha256']==bundle['sha256']),None)
            if stored!=bundle:raise EvidenceError('Candidate snapshot differs from its immutable store record')
            return bundle
        if p.get('candidate_sha256') or p.get('external_candidate_sha256'):
            code=p.get('candidate_sha256') or p['external_candidate_sha256']
            bundle=next(b for b in memory.records(p['store']) if b['sha256']==code)
        else:
            value=load(self.root/'composed-candidate.json');parent=value['parent']
            files=[self.root/'raw-reflection.json',self.root/'reflection-input.json']
            if p.get('candidate_handoff'):
                files += [self.root/name for name in ('composition-derivation.json','original-response-schema.json','handoff.json')]
                if (self.root/'original-reflection-response.txt').is_file():files.append(self.root/'original-reflection-response.txt')
            digests={f:sha(f.read_bytes()) for f in files}
            sources=deepcopy(parent['audit']['sources']) if parent else []
            sources += [dict(path=str(f),sha256=digests[f]) for f in files]
            links=[]
            for rule,origin in zip(value['rules'],value['origins']):
                if 'change_index' in origin:links.append(dict(rule_id=rule['id'],source_sha256=digests[files[0]],pointer='/changes/'+str(origin['change_index'])))
                else:
                    old=parent['rules'][origin['parent_index']]['id']
                    links.extend(dict(r,rule_id=rule['id']) for r in parent['audit']['rule_links'] if r['rule_id']==old)
            payload=dict(schema_version=memory.BUNDLE_VERSION_V2,id=parent['id'] if parent else p['batch_id'],version=p['batch_id'],
                parent_sha256=parent['sha256'] if parent else None,taxonomy_version=taxonomy.VERSION,
                **{k:value[k] for k in ('labels','requires','excludes','rules')},
                review=dict(status='candidate',kind='ai_assisted',source_sha256=digests[files[0]],limitations=['Pending AI evidence check and exact-version human content review.']),
                audit=dict(sources=list({s['sha256']:s for s in sources}.values()),rule_links=links,notes=['V3 reflection candidate; not human approval.'],outcome_refs=[]))
            bundle=memory.seal(payload)
            with life.locked(p['store']):
                if not any(b['sha256']==bundle['sha256'] for b in memory.records(p['store'])):
                    # Acceptance uses the same lock: publish pending AI state before
                    # the immutable record becomes visible, closing that race.
                    life._update(p['store'],bundle['sha256'],origin_root=str(self.root),generation=0,
                        ai_status='pending',status='ai_check_pending',validation_job=None,validation_status='not_started')
                    bundle=memory.add(p['store'],payload,files)
        archive.atomic_json(target,bundle)
        state=self.state();state['candidate_sha256']=bundle['sha256'];self.save(state)
        return bundle

    def _candidate_check(self,backend,p,bundle):
        code=bundle['sha256'];self._status('ai_candidate_checking')
        life.update(p['store'],code,status='ai_candidate_checking')
        origin=Path(p.get('origin_root',self.root));context=load(origin/'reflection-input.json')
        # Freeze this unstarted check's protocol without rewriting an old batch.
        # Existing checks retain their original response contract on recovery.
        binding=self.root/'candidate-check-protocol.json'
        if binding.exists():policy=load(binding)['protocol']
        else:
            already_started=any(j['slot']=='CANDIDATE-CHECK' for j in self.state()['jobs'])
            policy=p.get('candidate_check_protocol',checks.CANDIDATE_V1 if already_started else checks.CANDIDATE_V2)
            archive.atomic_json(binding,dict(candidate_sha256=code,protocol=policy,
                prior_versions=list(context.get('prior_experiences',{})),
                scope='This check only; historical reflection/action and earlier checks are unchanged'))
        if load(binding)['candidate_sha256']!=code:raise EvidenceError('Candidate check protocol belongs to another version')
        result=self._session(backend,p,'CANDIDATE-CHECK','candidate_check','source',
            checks.candidate_prompt(bundle,context,protocol=policy),checks.candidate_schema(bundle,context['ledger'],
                protocol=policy,prior_experiences=context.get('prior_experiences',{})))
        archive.atomic_json(self.root/'candidate-ai-check.json',dict(candidate_sha256=code,kind='AI',protocol=policy,result=result['output'],human_acceptance=False))
        life.update(p['store'],code,ai_result=result['output'],ai_check_path=str(self.root/'candidate-ai-check.json'))
        try:checks.accept_candidate(result['output'],bundle,context,p['cases']['source']['visible'],protocol=policy)
        except EvidenceError as error:raise CandidateCheckFailed(str(error)) from error
        with life.locked(p['store']):
            decisions=[row for row in approval.decisions(p['store']) if row['candidate_sha256']==code]
            status={'accept':'content_accepted_waiting_validation','reject':'rejected','revise':'revision_requested'}[decisions[-1]['decision']] if decisions else 'awaiting_human_review'
            life._update(p['store'],code,ai_status='passed',ai_check_path=str(self.root/'candidate-ai-check.json'),
                status=status,ai_unknowns=result['output']['unknowns'])

    def _develop(self,backend,p):
        self._boundary(p,backend);self._analyses(backend,p)
        # Only frozen M_old participates in the common analysis and starting repair route.
        old=[e['bundle'] for e in load(self.root/'M-old.json')['entries']]
        route=updates.route_view(p['cases']['source']['visible'],old);archive.atomic_json(self.root/'starting-route.json',route)
        self._status('starting_repairs')
        for n in (1,2):self._session(backend,p,'START-'+str(n),'repair','source',self.common(self._case_protocol(p,'source'),route['experience_text']))
        if not p.get('external_candidate_sha256'):
            self._status('reflecting')
            if not (self.root/'raw-reflection.json').exists():
                if (self.root/'reflection-evidence').exists():
                    result=self._session(backend,p,'EXTRACT','reflect','source','',None)
                    archive.atomic_json(self.root/'raw-reflection.json',result['output'])
                    context=load(self.root/'reflection-input.json');parents={b['sha256']:b for b in load(self.root/'prior-experiences.json')}
                    composed=updates.compose(result['output'],p['cases']['source']['visible'],context['ledger'],parents,
                        protocol=p.get('reflection_delta_protocol',updates.DELTA_V1),prior_experiences=context['prior_experiences'])
                    if composed is not None:archive.atomic_json(self.root/'composed-candidate.json',composed)
                    else:self._status('no_update',development_done=True,no_update_reason=result['output']['reason']);return
                else:self._extract(backend,p,old)
            if self.state()['status']=='no_update':self._status('no_update',development_done=True);return
            if not (self.root/'composed-candidate.json').exists():
                context=load(self.root/'reflection-input.json');parents={b['sha256']:b for b in load(self.root/'prior-experiences.json')}
                composed=updates.compose(load(self.root/'raw-reflection.json'),p['cases']['source']['visible'],context['ledger'],parents,
                    protocol=p.get('reflection_delta_protocol',updates.DELTA_V1),prior_experiences=context['prior_experiences'])
                if composed is None:self._status('no_update',development_done=True);return
                archive.atomic_json(self.root/'composed-candidate.json',composed)
        else:
            # A legacy/unbound edited candidate can enter a fresh authorized v3 development batch.
            starts=[j for j in self.state()['jobs'] if j['slot'].startswith('START-')]
            ledger={'TASK':dict(kind='original_task',text=p['cases']['source']['visible']['task'])}
            ledger.update({f'S{i:03d}':dict(kind='source_document',path=n,text=t) for i,(n,t) in enumerate(sorted(p['cases']['source']['visible']['sources'].items()),1)})
            archive.atomic_json(self.root/'reflection-input.json',dict(ledger=ledger,analysis=p['cases']['source']['visible']['analysis'],
                original=load(self.root/'cases/source/original-score.json'),starting_records=starts,prior_experiences=load(self.root/'prior-experiences.json'),
                note='Existing immutable candidate, not a new reflection. Actual source starts retained.'))
            self._status('candidate_prepared',branch='success' if all(j['outcome']['verdict']=='PASS' for j in starts) else 'failure')
        bundle=self._store_candidate(p);code=bundle['sha256']
        existing=life.metadata(p['store'],code)
        if existing and existing.get('origin_root') not in (None,str(self.root)):raise EvidenceError('Candidate already bound to another immutable workflow')
        if not existing or not existing.get('origin_root'):
            life.update(p['store'],code,origin_root=str(self.root),generation=0,ai_status='pending',validation_job=None,validation_status='not_started')
        state=self.state();state.update(development_done=True,admitted_versions=[code]);self.save(state)
        self._candidate_check(backend,p,bundle);self._status('awaiting_human_review')

    def _task(self,p,code):
        directory=self.root/'validations'/code
        if not directory.exists():
            state=self.state();admitted=state.get('admitted_versions',[])
            if code not in admitted:
                if len(admitted)>=p['max_candidate_versions']:
                    life.update(p['store'],code,status='budget_exhausted',enable_blocker='Declared candidate-version budget exhausted');return None
                admitted.append(code);state['admitted_versions']=admitted;self.save(state)
            directory.mkdir(parents=True);q=deepcopy(p)
            q.update(schema_version=VALIDATION,execution_policy=VALIDATION,origin_root=str(self.root),candidate_sha256=code,
                batch_id='validation-'+code,kind='validation',analysis_cap=0,total_request_cap=244,branch_caps=dict(success=244,failure=244))
            q['slots']=[s for s in q['slots'] if s['role']=='repair' and not s['name'].startswith('START-')]+[
                dict(name='CANDIDATE-CHECK',role='candidate_check',case='source',requests=4)]
            archive.atomic_json(directory/'protocol.json',q)
            starts=[dict(deepcopy(j),reused=True,requests=0,usage=None,seconds=0) for j in self.state()['jobs'] if j['slot'].startswith('START-')]
            archive.atomic_json(directory/'state.json',dict(status='prepared',jobs=starts,candidate_sha256=code,branch=self.state()['branch']))
            shutil.copyfile(self.root/'M-old.json',directory/'M-old.json')
            for key in p['cases']:
                destination=directory/'cases'/key;destination.mkdir(parents=True)
                shutil.copyfile(self.root/'cases'/key/'original-score.json',destination/'original-score.json')
                shutil.copyfile(self.root/'cases'/key/'approved-visible.json',destination/'approved-visible.json')
            shutil.copyfile(self.root/'last-boundary-check.json',directory/'last-boundary-check.json')
        task=Workflow(directory);task.PROTOCOL=VALIDATION
        q=task.verify()
        if q['candidate_sha256']!=code or q['batch_id']!='validation-'+code or q['origin_root']!=str(self.root):
            raise EvidenceError('Existing validation task is bound to a different candidate or origin')
        if any(c['visible']!=p['cases'][key]['visible'] for key,c in q['cases'].items()) or q['boundaries']!=p['boundaries']:
            raise EvidenceError('Validation public analysis differs from its frozen common source analysis')
        life.update(p['store'],code,validation_job=q['batch_id'],validation_root=str(directory))
        return task

    def _process(self,backend,p,code):
        meta=life.metadata(p['store'],code)
        if meta.get('status') in ('rejected','revision_requested'):return
        task=self._task(p,code)
        if task is None:return
        q=task.verify();task._boundary(q,backend);bundle=task._store_candidate(q)
        try:
            if meta.get('ai_status')=='pending':
                task._candidate_check(backend,q,bundle);task._status(life.metadata(p['store'],code)['status'])
            meta=life.metadata(p['store'],code)
            if meta.get('ai_status')!='passed':return
            accepted=life.latest_acceptance(p['store'],code)
            if not accepted:return
            if meta.get('validation_status') in ('passed','failed','unknown','infrastructure_error','cancelled'): 
                if meta['validation_status']=='passed':life.maybe_enable(p['store'],code,'workflow-worker:'+p['batch_id'])
                return
            life.update(p['store'],code,validation_status='running',status='effect_validation_running')
            self._status('effect_validation_running',validating_sha256=code)
            result_file=task.root/'development-screening.json'
            if not result_file.exists():task._validate_candidate(backend,q)
            if result_file.exists():
                gate=load(result_file)['gate'];status='passed' if gate['status']=='qualified' else 'failed' if gate['status']=='blocked' else 'unknown'
                life.validation_finished(p['store'],code,status,effect_gate=gate)
            else:
                result=task.state();status='failed' if result['status']=='source_blocked' else 'unknown'
                life.validation_finished(p['store'],code,status,enable_blocker=result.get('error','Critical preservation or applicability did not establish qualification'))
            if status=='passed':life.maybe_enable(p['store'],code,'workflow-worker:'+p['batch_id'])
        except BaseException as error:
            meta=life.metadata(p['store'],code)
            if isinstance(error,(ReviewWithdrawn,ExecutionCancelled)):life.update(p['store'],code,validation_status='cancelled',enable_blocker=repr(error))
            elif meta.get('ai_status')=='pending':
                incomplete=task.state()['jobs'][-1].get('status')=='invalid'
                life.update(p['store'],code,ai_status='incomplete' if incomplete else 'failed',status='ai_check_incomplete' if incomplete else 'ai_candidate_failed',enable_blocker=repr(error))
            else:life.update(p['store'],code,validation_status='infrastructure_error',status='infrastructure_error',enable_blocker=repr(error))
            task._status('stopped',error=repr(error));raise
        finally:task.report()

    def run(self,execute=False,backend=None):
        if not execute:raise EvidenceError('Execution requires explicit --execute; browsing/editing/review never dispatches models')
        p=self.verify();backend=backend or backend_for(p)
        if self.state()['status'] in ('infrastructure_error','reflection_incomplete','ai_check_incomplete','budget_exhausted','cancelled','ai_contract_failed'):
            return self.state()
        auth_path=self.root/'execution-authorization.json'
        if not auth_path.exists():archive.atomic_json(auth_path,dict(root=str(self.root),request_cap=p['global_request_cap'],cancelled=False,at=archive.now()))
        auth=load(auth_path)
        if auth.get('root')!=str(self.root) or auth.get('request_cap')!=p['global_request_cap']:
            raise EvidenceError('Frozen execution authorization or budget drifted')
        state=self.state();state['backend_kind']=backend.kind;self.save(state)
        with (Path(p['store'])/'evolution-execution.lock').open('a') as lock:
            try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError as error:raise EvidenceError('A workflow is already executing; no duplicate dispatch') from error
            try:
                if load(auth_path).get('cancelled'):self._status('cancelled');return self.state()
                if p.get('candidate_handoff') and not (self.root/'handoff-preflight.json').exists():
                    for key in p['cases']:backend.preflight(self._case_protocol(p,key))
                    archive.atomic_json(self.root/'handoff-preflight.json',dict(at=archive.now(),
                        scope='Revalidate original calibration/runtime for the explicitly authorized continuation; reuse original scores.'))
                if not self.state().get('development_done') and self.state()['status'] not in ('ai_contract_failed','ai_check_incomplete','infrastructure_error','budget_exhausted','cancelled'):
                    self._develop(backend,p)
                if self.state().get('development_done') and self.state()['status']!='no_update':
                    self._checked_public_inputs(p)
                    versions=[]
                    for file in (Path(p['store'])/'workflow/versions').glob('*.json'):
                        meta=load(file)
                        if meta.get('origin_root')==str(self.root):versions.append(meta)
                    versions.sort(key=lambda r:(r.get('generation',0),r['candidate_sha256']))
                    for meta in versions:
                        code=meta['candidate_sha256']
                        if meta.get('ai_status')=='pending' or meta.get('ai_status')=='passed' and life.latest_acceptance(p['store'],code):
                            self._process(backend,p,code)
                    values=[life.metadata(p['store'],r['candidate_sha256']) for r in versions]
                    self._status('enabled' if any(r.get('status')=='enabled' for r in values) else 'awaiting_human_review' if any(r.get('ai_status')=='passed' and not life.latest_acceptance(p['store'],r['candidate_sha256']) and r.get('status') not in ('rejected','revision_requested') for r in values) else (values[-1]['status'] if values else self.state()['status']))
            except BaseException as error:
                state=self.state();last=state['jobs'][-1] if state['jobs'] else {}
                phase=state['status'];status='revision_requested_or_rejected' if isinstance(error,ReviewWithdrawn) else 'ai_candidate_failed' if isinstance(error,CandidateCheckFailed) else 'cancelled' if isinstance(error,(KeyboardInterrupt,ExecutionCancelled)) else 'budget_exhausted' if 'budget' in str(error).lower() else 'ai_check_incomplete' if last.get('status')=='invalid' and last.get('role') in ('contract_check','candidate_check','analysis') else 'ai_contract_failed' if phase=='ai_contract_checking' else 'ai_candidate_failed' if phase=='ai_candidate_checking' else 'reflection_incomplete' if phase=='reflecting' and last.get('slot')=='EXTRACT' and (last.get('status')=='valid' or isinstance(error,ValueError)) else 'infrastructure_error'
                self._status(status,error=repr(error))
                code=self.state().get('candidate_sha256')
                if code and phase=='ai_candidate_checking':life.update(p['store'],code,ai_status='failed',status=status,enable_blocker=repr(error))
            if load(auth_path).get('cancelled'):self._status('cancelled')
            self.report();return self.state()

    def report(self):
        super().report();p=self.verify();summary=load(self.root/'summary.json')
        summary.update(schema_version=p['schema_version'],state=self.state()['status'],human_checkpoint='experience content review/editing only',
            review_policy=p.get('review_policy',LEGACY_CHECKS),AI_audit='not_run' if human_only(p) else 'legacy_budgeted_checks')
        summary['counts_scope']='This task only; root repair reservations are executed in separately reported exact-version validation tasks.'
        actual=[j for j in self.state()['jobs'] if not j.get('reused')]
        summary.update(started=len(actual),valid=sum(j['status']=='valid' for j in actual),invalid=sum(j['status']=='invalid' for j in actual),
            unstarted=len(p['slots'])-len(actual),reused_source_baselines=[j['slot'] for j in self.state()['jobs'] if j.get('reused')],
            valid_behavior_scores=sum(j['status']=='valid' and 'outcome' in j for j in actual),
            whole_passes=sum(j['status']=='valid' and j.get('outcome',{}).get('verdict')=='PASS' for j in actual))
        summary['whole_pass_rate']=summary['whole_passes']/summary['valid_behavior_scores'] if summary['valid_behavior_scores'] else None
        usage=[(j.get('usage') or {}).get('usage_unknown_requests') for j in actual]
        summary['requests_with_unknown_token_usage']=sum(usage) if all(type(n) is int for n in usage) else None
        summary['token_cost']={}
        for key in ('input_tokens','output_tokens','total_tokens','cached_input_tokens','reasoning_output_tokens'):
            values=[((j.get('usage') or {}).get('observed_usage_subtotal') or (j.get('usage') or {}).get('total_usage') or {}).get(key) for j in actual]
            known=[v for v in values if type(v) in (int,float)]
            summary['token_cost'][key]=dict(known_subtotal=sum(known) if known else None,sessions_without_known_usage=len(values)-len(known))
        if p.get('global_request_cap'):
            jobs=self._all_jobs(p)
            budget_protocol=load(Path(p.get('origin_root',self.root))/'protocol.json')
            tokens=[((j.get('usage') or {}).get('observed_usage_subtotal') or (j.get('usage') or {}).get('total_usage') or {}).get('total_tokens') for j in jobs]
            unknown=[(j.get('usage') or {}).get('usage_unknown_requests') for j in jobs]
            summary['workflow_usage']=dict(known_requests=sum(j['requests'] for j in jobs if type(j.get('requests')) is int),
                unknown_request_sessions=sum(type(j.get('requests')) is not int for j in jobs),request_cap=p['global_request_cap'],
                known_token_subtotal=sum(t for t in tokens if type(t) is int) if any(type(t) is int for t in tokens) else None,
                sessions_without_known_tokens=sum(type(t) is not int for t in tokens),
                requests_with_unknown_token_usage=sum(unknown) if all(type(n) is int for n in unknown) else None,
                known_seconds=sum(j['seconds'] for j in jobs if type(j.get('seconds')) in (int,float)),
                valid_behavior_scores=sum(j['status']=='valid' and 'outcome' in j for j in jobs),jobs=jobs,engineering_usage=None)
            summary['workflow_usage'].update(planned_max_sessions=len(budget_protocol['slots'])+11*(budget_protocol['max_candidate_versions']-1),
                started=len(jobs),valid=sum(j['status']=='valid' for j in jobs),invalid=sum(j['status']=='invalid' for j in jobs))
        archive.atomic_json(self.root/'summary.json',summary)
        (self.root/'REPORT.md').write_text('# Automated evidence workflow v3\n\nOnly experience content review/editing waits for a human. '
            'No paid execution follows page reads, edits or review submissions without an authorized worker.\n\n```json\n'+json.dumps(summary,indent=2)+'\n```\n')


class FrozenEvaluation(AutomatedChecks,Evaluation):
    PROTOCOL=EVALUATION

    def prepare_config(self,config):
        super().prepare_config(config);p=self.verify();extra=self._analysis_setup(p)
        p['total_request_cap']+=extra;p['analysis_cap']+=extra
        archive.atomic_json(self.root/'protocol.json',p);self._status('prepared');self.report();return self.state()

    def run(self,execute=False,backend=None):
        if not execute:raise EvidenceError('Frozen evaluation requires explicit --execute')
        p=self.verify();backend=backend or backend_for(p)
        if self.state()['status'] in ('evaluation_complete','stopped','ai_contract_failed'):return self.state()
        with (Path(p['store'])/'evolution-execution.lock').open('a') as lock:
            try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError as error:raise EvidenceError('Another task is executing') from error
            try:self._boundary(p,backend);self._analyses(backend,p);self._status('prepared')
            except BaseException as error:
                self._status('ai_contract_failed',error=repr(error));self.report();return self.state()
        # Existing frozen evaluator performs actual scoring and never reflects or enables versions.
        return super().run(execute=True,backend=backend)
