"""V3 orchestration over the existing development/evaluation runner and scorer."""
from copy import deepcopy
import fcntl
import json
from pathlib import Path
import shutil

from . import archive, taxonomy, experience_memory as memory, experience_approval as approval
from . import experience_updates as updates, experience_lifecycle as life
from . import experience_routing as routing
from .candidate_files import write_files, inventory
from .core import EvidenceError, canonical, sha
from .experience_development import Development, load
from .experience_evaluation import Evaluation
from .evolution_backend import NativeBackend, ROLES

VERSION='experience-development-v3'
VALIDATION='experience-validation-v3'
EVALUATION='experience-evaluation-v3'
HUMAN_ONLY='human-content-only-v1'


class ReviewWithdrawn(EvidenceError):pass
class ExecutionCancelled(EvidenceError):pass


def backend_for(p):
    if p.get('backend'):
        from .docker_backend import DockerBackend
        return DockerBackend()
    return NativeBackend()


class PublicInputs:
    PUBLIC_ANALYSIS_PIPELINE=True

    def _checked_public_input(self,key,original):
        """Keep task/source and retained analysis consistent without an AI audit."""
        directory=self.root/'cases'/key;folder=directory/'analysis'
        visible=load(directory/'approved-visible.json')
        if visible['task']!=original['task'] or visible['sources']!=original['sources']:
            raise EvidenceError('Public input differs from the frozen original task/source')
        binding=load(folder/'check-binding.json') if (folder/'check-binding.json').exists() else {}
        if binding.get('kind')=='not_run':
            if visible['analysis']!=load(folder/'raw-analysis.json') or binding.get('input_sha256')!=routing.input_digest(
                    visible['analysis'],visible['task'],visible['sources']):
                raise EvidenceError('Public analysis differs from its retained input snapshot')
        return visible

    def _checked_public_inputs(self,p):
        original=load(self.root/'protocol.json')
        for key,c in p['cases'].items():c['visible']=self._checked_public_input(key,original['cases'][key]['visible'])
        for i,b in enumerate(p.get('boundaries',[])):
            b['visible']=self._checked_public_input('boundary-'+str(i+1),original['boundaries'][i]['visible'])

    def verify(self):
        p=super().verify()
        for i,b in enumerate(p.get('boundaries',[]),1):
            path=self.root/'cases'/('boundary-'+str(i))/'approved-visible.json'
            if path.exists():b['visible']=load(path)
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
        p.update(review_policy=HUMAN_ONLY,contract_check_protocol='not_run')
        for key,c in p['cases'].items():
            folder=self.root/'cases'/key/'analysis';folder.mkdir(parents=True,exist_ok=True)
            if not (folder/'ast-evidence.json').exists():
                full,ast=analyze_candidate(c['visible']['sources'],node=None if p.get('backend') else p['node'])
                archive.atomic_json(folder/'ast-report.json',full);archive.atomic_json(folder/'ast-evidence.json',ast)
            supplied=self.root/'cases'/key/'approved-visible.json'
            if supplied.exists():supplied.unlink()
        for i,b in enumerate(p.get('boundaries',[]),1):
            folder=self.root/'cases'/('boundary-'+str(i))/'input'
            write_files(folder,{n:t.encode() for n,t in b['visible']['sources'].items()})
            b.update(input_path=str(folder),candidate_files=inventory({n:t.encode() for n,t in b['visible']['sources'].items()}))
        p['slots']=[s for s in p['slots'] if s['role'] not in ('contract_check','candidate_check')]
        p['roles']={k:deepcopy(v) for k,v in ROLES.items() if k in ('analysis','repair','reflect')}

    def _analyses(self,backend,p):
        all_cases=list(p['cases'].items())+[(f'boundary-{i}',b) for i,b in enumerate(p.get('boundaries',[]),1)]
        for key,c in all_cases:
            target=self.root/'cases'/key/'approved-visible.json'
            if target.exists():
                original=load(self.root/'protocol.json')
                raw=original['boundaries'][int(key.split('-')[1])-1]['visible'] if key.startswith('boundary-') else original['cases'][key]['visible']
                c['visible']=self._checked_public_input(key,raw)
                continue
            self._status('analyzing',case=key)
            folder=self.root/'cases'/key/'analysis';folder.mkdir(parents=True,exist_ok=True)
            raw=c['visible'];analysis=raw.get('analysis')
            if analysis is None:
                result=self._session(backend,p,'ANALYSIS-'+key,'analysis',key,
                    (folder/'prompt.md').read_text(),taxonomy.analysis_schema())
                analysis=result['output']
            archive.atomic_json(folder/'raw-analysis.json',analysis)
            archive.atomic_json(folder/'analysis-origin.json',dict(kind='model_generated' if c.get('analysis_needed') else 'supplied_proposal',human_review=False))
            warnings=[]
            try:routing.validate_analysis(analysis,raw['task'],raw['sources'])
            except EvidenceError as error:warnings.append(str(error))
            review=dict(input_sha256=routing.input_digest(analysis,raw['task'],raw['sources']),
                reviewer='unreviewed_model_analysis',approved=False,blocking_issues=[],evidence=[],
                scope_unknowns=analysis['unknowns'],reason='Unreviewed analysis; retrieval uses current source premises. Verify the proposal during repair.')
            visible=dict(task=raw['task'],sources=raw['sources'],analysis=analysis,review=review)
            archive.atomic_json(folder/'analysis-notes.json',dict(kind='not_run',warnings=warnings,blocking=False,human_acceptance=False))
            archive.atomic_json(folder/'check-binding.json',dict(kind='not_run',input_sha256=review['input_sha256'],human_acceptance=False))
            archive.atomic_json(target,visible);c['visible']=visible

    def _status(self,status,**values):
        state=self.state();state.update(status=status,**values);self.save(state)

class Workflow(PublicInputs,Development):
    PROTOCOL=VERSION

    def prepare_config(self,config):
        config=deepcopy(config);config.pop('review_policy',None)
        limit=config.pop('max_candidate_versions',2);external=config.pop('candidate_sha256',None)
        if type(limit) is not int or not 1<=limit<=20:raise EvidenceError('Declare 1..20 bounded candidate versions before execution')
        super().prepare_config(config);p=self.verify()
        self._analysis_setup(p)
        initial=300+p['analysis_cap']+p.get('fix_request_cap',0)
        p.update(max_candidate_versions=limit,initial_request_cap=initial,
            total_request_cap=initial+(limit-1)*240,global_request_cap=initial+(limit-1)*240,
            external_candidate_sha256=external,check_policy='Source analysis, actual repairs, failure review, then human content acceptance')
        p.update(reflection_delta_protocol=updates.DELTA_V1,candidate_check_protocol='not_run')
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

    def _session(self,backend,p,name,role,key,prompt,schema=None,cap=None,repair_from=None):
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
        return super()._session(backend,p,name,role,key,prompt,schema,cap,repair_from=repair_from)

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
                review=dict(status='candidate',kind='ai_assisted',source_sha256=digests[files[0]],limitations=['AI evidence review not performed; pending human content review.']),
                audit=dict(sources=list({s['sha256']:s for s in sources}.values()),rule_links=links,notes=['V3 reflection candidate; not human approval.'],outcome_refs=[]))
            bundle=memory.seal(payload)
            with life.locked(p['store']):
                if not any(b['sha256']==bundle['sha256'] for b in memory.records(p['store'])):
                    # Acceptance uses the same lock: publish pending AI state before
                    # the immutable record becomes visible, closing that race.
                    life._update(p['store'],bundle['sha256'],origin_root=str(self.root),generation=0,
                        review_policy=HUMAN_ONLY,ai_status='not_run',content_review_available=True,status='awaiting_human_review',validation_job=None,validation_status='not_started')
                    bundle=memory.add(p['store'],payload,files)
        archive.atomic_json(target,bundle)
        state=self.state();state['candidate_sha256']=bundle['sha256'];self.save(state)
        return bundle

    def _prepare_content_review(self,p,bundle):
        code=bundle['sha256']
        with life.locked(p['store']):
            decisions=[row for row in approval.decisions(p['store']) if row['candidate_sha256']==code]
            status={'accept':'content_accepted','reject':'rejected','revise':'revision_requested'}[decisions[-1]['decision']] if decisions else 'awaiting_human_review'
            life._update(p['store'],code,review_policy=HUMAN_ONLY,ai_status='not_run',
                         content_review_available=True,status=status)

    def _develop(self,backend,p):
        self._boundary(p,backend);self._analyses(backend,p)
        # Only frozen M_old participates in the common analysis and starting repair route.
        old=[e['bundle'] for e in load(self.root/'M-old.json')['entries']]
        route=updates.route_view(p['cases']['source']['visible'],old);archive.atomic_json(self.root/'starting-route.json',route)
        self._status('starting_repairs')
        for n in (1,2):self._session(backend,p,'START-'+str(n),'repair','source',self.common(self._case_protocol(p,'source'),route['experience_text']))
        self._status('repairing_failures')
        self._repair_failed_starts(backend,p)
        if not p.get('external_candidate_sha256'):
            self._status('reflecting')
            if not (self.root/'raw-reflection.json').exists():
                if (self.root/'reflection-evidence').exists():
                    result=self._session(backend,p,'EXTRACT','reflect','source','',None)
                    archive.atomic_json(self.root/'raw-reflection.json',result['output'])
                    context=load(self.root/'reflection-input.json');parents={b['sha256']:b for b in load(self.root/'prior-experiences.json')}
                    composed=updates.compose(result['output'],p['cases']['source']['visible'],context['ledger'],parents,
                        protocol=p.get('reflection_delta_protocol',updates.DELTA_V1),prior_experiences=context['prior_experiences'],failure_context=context.get('failure_observations'))
                    if composed is not None:archive.atomic_json(self.root/'composed-candidate.json',composed)
                    else:
                        self._finish_no_update(result['output']);self._status(self.state()['status'],development_done=True);return
                else:self._extract(backend,p,old)
            if self.state()['status'] in ('no_update','needs_followup','repaired','repair_exhausted'):
                self._status(self.state()['status'],development_done=True);return
            if not (self.root/'composed-candidate.json').exists():
                context=load(self.root/'reflection-input.json');parents={b['sha256']:b for b in load(self.root/'prior-experiences.json')}
                composed=updates.compose(load(self.root/'raw-reflection.json'),p['cases']['source']['visible'],context['ledger'],parents,
                    protocol=p.get('reflection_delta_protocol',updates.DELTA_V1),prior_experiences=context['prior_experiences'],failure_context=context.get('failure_observations'))
                if composed is None:
                    self._finish_no_update(load(self.root/'raw-reflection.json'));self._status(self.state()['status'],development_done=True);return
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
            life.update(p['store'],code,origin_root=str(self.root),generation=0,review_policy=HUMAN_ONLY,ai_status='not_run',content_review_available=True,validation_job=None,validation_status='not_started')
        state=self.state();state.update(development_done=True,admitted_versions=[code]);self.save(state)
        self._prepare_content_review(p,bundle);self._status('awaiting_human_review')

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
                batch_id='validation-'+code,kind='validation',analysis_cap=0,total_request_cap=240,branch_caps=dict(success=240,failure=240))
            q['slots']=[s for s in q['slots'] if s['role']=='repair' and not s['name'].startswith(('START-','FIX-'))]
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
        bundle=next(b for b in memory.records(p['store']) if b['sha256']==code)
        self._prepare_content_review(p,bundle)
        if not life.latest_acceptance(p['store'],code):return
        life.maybe_enable(p['store'],code,'workflow-worker:'+p['batch_id'])
        if meta.get('validation_status') in ('passed','failed','unknown','infrastructure_error','cancelled'):return
        task=self._task(p,code)
        if task is None:return
        q=task.verify();task._boundary(q,backend);task._store_candidate(q)
        try:
            life.update(p['store'],code,validation_status='running',status='effect_validation_running')
            self._status('effect_validation_running',validating_sha256=code)
            result_file=task.root/'development-screening.json'
            if not result_file.exists():task._validate_candidate(backend,q)
            if result_file.exists():
                gate=load(result_file)['gate'];status='passed' if gate['status']=='qualified' else 'failed' if gate['status']=='blocked' else 'unknown'
                life.validation_finished(p['store'],code,status,effect_gate=gate)
            else:
                result=task.state();status='failed' if result['status']=='source_blocked' else 'unknown'
                life.validation_finished(p['store'],code,status,validation_note=result.get('error','Critical behavior or applicability remains unresolved'))
            life.maybe_enable(p['store'],code,'workflow-worker:'+p['batch_id'])
        except BaseException as error:
            life.update(p['store'],code,validation_status='cancelled' if isinstance(error,(ReviewWithdrawn,ExecutionCancelled)) else 'infrastructure_error',validation_error=repr(error))
            task._status('stopped',error=repr(error));raise
        finally:task.report()

    def run(self,execute=False,backend=None):
        if not execute:raise EvidenceError('Execution requires explicit --execute; browsing/editing/review never dispatches models')
        p=self.verify();backend=backend or backend_for(p)
        if self.state()['status'] in ('needs_followup','repaired','repair_exhausted','infrastructure_error','reflection_incomplete','ai_check_incomplete','budget_exhausted','cancelled','ai_contract_failed'):
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
                if self.state().get('development_done') and self.state()['status'] not in ('no_update','needs_followup','repaired','repair_exhausted'):
                    self._checked_public_inputs(p)
                    versions=[]
                    for file in (Path(p['store'])/'workflow/versions').glob('*.json'):
                        meta=load(file)
                        if meta.get('origin_root')==str(self.root):versions.append(meta)
                    versions.sort(key=lambda r:(r.get('generation',0),r['candidate_sha256']))
                    for meta in versions:
                        code=meta['candidate_sha256']
                        if meta.get('status') not in ('rejected','revision_requested','authorization_revoked'):
                            self._process(backend,p,code)
                    values=[life.metadata(p['store'],r['candidate_sha256']) for r in versions]
                    self._status('enabled' if any(r.get('status')=='enabled' for r in values) else 'awaiting_human_review' if any(r.get('content_review_available') and not life.latest_acceptance(p['store'],r['candidate_sha256']) and r.get('status') not in ('rejected','revision_requested') for r in values) else (values[-1]['status'] if values else self.state()['status']))
            except BaseException as error:
                state=self.state();last=state['jobs'][-1] if state['jobs'] else {}
                status='revision_requested_or_rejected' if isinstance(error,ReviewWithdrawn) else 'cancelled' if isinstance(error,(KeyboardInterrupt,ExecutionCancelled)) else 'budget_exhausted' if 'budget' in str(error).lower() else 'reflection_incomplete' if state['status']=='reflecting' else 'infrastructure_error'
                self._status(status,error=repr(error))
            if load(auth_path).get('cancelled'):self._status('cancelled')
            self.report();return self.state()

    def report(self):
        super().report();p=self.verify();summary=load(self.root/'summary.json')
        summary.update(schema_version=p['schema_version'],state=self.state()['status'],human_checkpoint='experience content review/editing only',
            review_policy=HUMAN_ONLY,AI_audit='not_run')
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
            summary['workflow_usage'].update(planned_max_sessions=len(budget_protocol['slots'])+10*(budget_protocol['max_candidate_versions']-1),
                started=len(jobs),valid=sum(j['status']=='valid' for j in jobs),invalid=sum(j['status']=='invalid' for j in jobs))
        archive.atomic_json(self.root/'summary.json',summary)
        (self.root/'REPORT.md').write_text('# Experience learning workflow v3\n\nOnly experience content review/editing waits for a human. '
            'No paid execution follows page reads, edits or review submissions without an authorized worker.\n\n```json\n'+json.dumps(summary,indent=2)+'\n```\n')


class FrozenEvaluation(PublicInputs,Evaluation):
    PROTOCOL=EVALUATION

    def prepare_config(self,config):
        config=deepcopy(config);config.pop('review_policy',None)
        super().prepare_config(config);p=self.verify();self._analysis_setup(p)
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
                self._status('stopped',error=repr(error));self.report();return self.state()
        # Existing frozen evaluator performs actual scoring and never reflects or enables versions.
        return super().run(execute=True,backend=backend)
