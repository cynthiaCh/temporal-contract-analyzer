"""Bounded v2 development over the existing Coding Agent backend. No implicit calls."""
from copy import deepcopy
import fcntl
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

from . import archive, taxonomy, experience_memory as memory, experience_approval as approval
from . import experience_routing as routing, experience_updates as updates, experience_screening as screening
from .core import EvidenceError, canonical, sha
from .candidate_files import capture, inventory, file_modes, write_files
from .case_evaluation import scoring_inputs, relation_states, delta, VERDICTS
from .case_catalog import case_input, case_root, inside, read
from .evolution_backend import NativeBackend, ROLES, SOURCE, DEPENDENCIES
from .experience_evolution import Evolution, load
from ._session_runtime.schema_validator import validate

VERSION = 'experience-development-v2'


def implementation_record():
    from .core import VERSION as package_version, ROOT
    result=dict(package_version=package_version,python_version=sys.version.split()[0],git_head=None,working_tree_dirty=None)
    try:
        result['git_head']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True,stderr=subprocess.DEVNULL).strip()
        result['working_tree_dirty']=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True))
    except (OSError,subprocess.SubprocessError):pass
    return result


def lineage(value, critical=True):
    memory.object_fields(value, {'source_unit','derived_from','prior_exposure'} | ({'critical'} if critical else set()), 'case lineage')
    if not memory.text(value['source_unit']) or not memory.text(value['prior_exposure']):
        raise EvidenceError('Record actual source unit and historical exposure')
    memory.strings(value['derived_from'], 'derived sources')
    if not critical:return value
    if not isinstance(value['critical'], list) or not value['critical']:
        raise EvidenceError('Preregister critical preservation obligations with visible-source support')
    keys = []
    for item in value['critical']:
        memory.object_fields(item, {'relation','basis'}, 'critical obligation')
        if not memory.text(item['relation']):raise EvidenceError('Missing critical relation')
        keys.append(item['relation'])
    if len(set(keys)) != len(keys):raise EvidenceError('Duplicate critical obligation')
    return value


def reviewed(visible):
    routing.validate_analysis(visible['analysis'], visible['task'], visible['sources'])
    result = updates.route_view(visible, [])
    if result['route']['reason'] in ('missing_or_drifted_semantic_review','unresolved_semantic_review'):
        raise EvidenceError('Public analysis needs an actual source-bound review')


class Development(Evolution):
    """One source, two independent transfer sources, one candidate and no retries."""

    PROTOCOL = VERSION

    def prepare_config(self, config):
        if self.root.exists():raise EvidenceError('Use a new batch directory')
        required = {'case_id','store','binary','node','calibration','source_relationship','cohort'}
        if not required <= set(config) or set(config)-required-{'visible','kind','max_rounds','backend'}:
            raise EvidenceError('Invalid v2 development configuration')
        if config.get('kind','development') != 'development' or config.get('max_rounds',1) != 1:
            raise EvidenceError('V2 defaults to one round; revisions need a separately prepared explicit batch')
        cohort = config['cohort']
        memory.object_fields(cohort, {'source','transfers','boundaries'}, 'development cohort')
        if not isinstance(cohort['transfers'],list) or len(cohort['transfers']) != 2:
            raise EvidenceError('Preregister exactly two other development sources')
        if not isinstance(cohort['boundaries'],list) or not cohort['boundaries']:
            raise EvidenceError('Preregister at least one reviewed inapplicable/unknown-premise boundary input; no extra analysis call is implied')
        specifications = [dict(case_id=config['case_id'],calibration=config['calibration'],
                               visible=config.get('visible'),lineage=cohort['source'])] + cohort['transfers']
        cases = {}
        for index, spec in enumerate(specifications):
            memory.object_fields(spec, {'case_id','calibration','visible','lineage'}, 'development case')
            key = 'source' if index == 0 else f'transfer-{index}'
            provenance = lineage(spec['lineage'])
            inputs = case_input(spec['case_id'])
            record = inputs['case_record']
            manifest_path = inside(case_root(record), record['manifest'])
            manifest = read(manifest_path)
            declared_unit = manifest.get('source_unit')
            if declared_unit is not None and declared_unit != provenance['source_unit']:
                raise EvidenceError('Declared source unit contradicts the registered manifest')
            files,_ = capture(Path(inputs['candidate']))
            sources = {name:raw.decode('utf-8') for name,raw in files.items()}
            visible = spec['visible'] or dict(task=inputs['task'],sources=sources)
            if visible.get('task') != inputs['task'] or visible.get('sources') != sources:
                raise EvidenceError('Public input must match the complete original task/source')
            for critical in provenance['critical']:
                issues = routing.evidence_issues(critical['basis'], inputs['task'], sources, 'critical basis')
                if issues:raise EvidenceError('Critical preservation basis is not candidate-visible')
            if spec['visible'] is not None:reviewed(visible)
            directory = self.root/'cases'/key
            cases[key] = dict(case=record,visible=visible,lineage=provenance,
                input_path=str(directory/'input'),candidate_files=inventory(files),
                candidate_sha256=sha(canonical(sources).encode()),file_modes=file_modes(Path(inputs['candidate']),files),
                calibration=spec['calibration'],scoring_inputs=scoring_inputs(record),
                frozen_manifest=manifest,trusted_case_path=str(directory/'trusted'/record['id']),
                frozen_probe=str(directory/'trusted'/record['id']/manifest['oracle']['probe']),
                original_case_path=str(manifest_path.parent),analysis_needed=spec['visible'] is None)
        families = [set([c['lineage']['source_unit']]+c['lineage']['derived_from']) for c in cases.values()]
        if any(a & b for i,a in enumerate(families) for b in families[i+1:]) \
                or len({c['candidate_sha256'] for c in cases.values()}) != 3:
            raise EvidenceError('Derived variants or identical source cannot count as independent sources')
        for boundary in cohort['boundaries']:
            memory.object_fields(boundary,{'visible','lineage'},'boundary input')
            lineage(boundary['lineage'],critical=False);reviewed(boundary['visible'])
        with (Path(config['store'])/'decision.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            frozen = approval.freeze(config['store'])
            prior_records=memory.records(config['store'])
            parent_selection={entry['bundle']['id']:entry['bundle']['sha256'] for entry in approval.active(config['store'])}
            prior_reviews=approval.decisions(config['store'])
        self.root.mkdir(parents=True)
        for key, case in cases.items():
            write_files(Path(case['input_path']),{n:b.encode() for n,b in case['visible']['sources'].items()},case['file_modes'])
            shutil.copytree(case['original_case_path'], case['trusted_case_path'],
                ignore=shutil.ignore_patterns('.git','node_modules','__pycache__','*.pyc'))
            if case['analysis_needed']:
                from .preanalysis import analyze_candidate
                full,evidence = analyze_candidate(case['visible']['sources'],node=None if config.get('backend') else config['node'])
                archive.atomic_json(self.root/'cases'/key/'analysis/ast-report.json',full)
                archive.atomic_json(self.root/'cases'/key/'analysis/ast-evidence.json',evidence)
                (self.root/'cases'/key/'analysis/prompt.md').write_text(
                    routing.analysis_prompt(case['visible']['task'],case['visible']['sources'],evidence),encoding='utf-8')
            else:
                archive.atomic_json(self.root/'cases'/key/'approved-visible.json',case['visible'])
        runtime = self.root/'session-runtime';runtime.mkdir()
        for name in DEPENDENCIES:shutil.copyfile(SOURCE/name,runtime/name)
        (self.root/'controller-prompt.md').write_bytes((Path(__file__).parent/'prompts/MASTER_PROMPT.md').read_bytes())
        archive.atomic_json(self.root/'M-old.json',frozen)
        archive.atomic_json(self.root/'prior-experiences.json',prior_records)
        archive.atomic_json(self.root/'prior-reviews.json',prior_reviews)
        slots = [dict(name=f'ANALYSIS-{k}',role='analysis',case=k,requests=12) for k,c in cases.items() if c['analysis_needed']]
        slots += [dict(name=f'START-{n}',role='repair',case='source',requests=24) for n in (1,2)]
        slots += [dict(name='EXTRACT',role='reflect',case='source',requests=12)]
        slots += [dict(name=f'SOURCE-NEW-{n}',role='repair',case='source',requests=24) for n in (1,2)]
        for key in ('transfer-1','transfer-2'):
            slots += [dict(name=f'{key}-{name}',role='repair',case=key,requests=24) for name in ('NEW-1','OLD-1','OLD-2','NEW-2')]
        protocol = dict(schema_version=VERSION,execution_policy=VERSION,batch_id='dev-'+uuid.uuid4().hex[:16],
            implementation=implementation_record(),
            kind='development',max_rounds=1,cases=cases,store=str(Path(config['store']).resolve()),
            binary=str(Path(config['binary']).resolve()),node=str(Path(config['node']).resolve()),
            roles=ROLES,slots=slots,runtime_source=str(runtime),boundaries=cohort['boundaries'],
            branch_caps=dict(success=290,failure=300,success_no_update=50,failure_no_update=60),
            analysis_cap=12*sum(c['analysis_needed'] for c in cases.values()),
            source_relationship=config['source_relationship'],no_retry=True,concurrency=1,
            parent_selection=parent_selection,
            critical_policy='Preregistered visible obligations; losses block and unknowns remain pending',
            qualification_policy='cross-source-development-screen-v2; old active metadata is not qualification')
        if config.get('backend'):
            from .docker_backend import validate_config
            protocol['backend']=validate_config(config['backend'])
        archive.atomic_json(self.root/'protocol.json',protocol)
        self.save(dict(status='analysis_prepared' if cases['source']['analysis_needed'] else 'prepared',
                       analysis_keys=['source'] if cases['source']['analysis_needed'] else [],analysis_stage='source',
                       jobs=[],candidate_sha256=None,round=1,branch=None))
        with (Path(config['store'])/'evolution-execution.lock').open('a') as execution_lock, \
                (Path(config['store'])/'decision.lock').open('a') as lock:
            try:fcntl.flock(execution_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError as error:raise EvidenceError('Cannot register development sources during another execution') from error
            fcntl.flock(lock,fcntl.LOCK_EX)
            usage_path=Path(config['store'])/'development-usage.json'
            usage=load(usage_path) if usage_path.exists() else []
            registered={key:dict(case_id=c['case']['id'],lineage=c['lineage']) for key,c in cases.items()}
            registered.update({f'boundary-{i}':dict(case_id=None,lineage=b['lineage']) for i,b in enumerate(cohort['boundaries'],1)})
            usage.append(dict(batch_id=protocol['batch_id'],cases=registered))
            archive.atomic_json(usage_path,usage)
        self.report()
        return self.state()

    def verify(self):
        """Read recorded configuration; no per-call whole-batch hash walk."""
        p = load(self.root/'protocol.json')
        if p['schema_version'] != self.PROTOCOL:raise EvidenceError('Wrong protocol')
        for key,case in p['cases'].items():
            approved = self.root/'cases'/key/'approved-visible.json'
            if approved.exists():case['visible']=load(approved)
        return p

    def _case_protocol(self, p, key, cap=None):
        value = dict(p, **p['cases'][key])
        if cap is not None:value['session_limits']=dict(requests=cap,seconds=600)
        return value

    def _boundary(self, p, backend):
        """Input/calibration correspondence once at the batch startup boundary."""
        if (self.root/'last-boundary-check.json').exists():
            p['boundary_preflight_complete']=True
            return
        for key,case in p['cases'].items():
            files,_ = capture(Path(case['input_path']))
            if inventory(files) != case['candidate_files']:
                raise EvidenceError('Captured original input changed')
            backend.preflight(self._case_protocol(p,key))
            local=self._case_protocol(p,key);local['boundary_preflight_complete']=True
            original=backend.score(local,case['input_path'],self.root/'cases'/key/'original')
            if original.get('verdict') not in VERDICTS:raise EvidenceError('Invalid original scorer verdict')
            states=relation_states(original)
            if any(c['relation'] not in states for c in case['lineage'].get('critical',[])):
                raise EvidenceError('Preregistered critical relation is absent from the scoring version')
            archive.atomic_json(self.root/'cases'/key/'original-score.json',original)
        p['boundary_preflight_complete']=True
        archive.atomic_json(self.root/'last-boundary-check.json',dict(at=archive.now(),cases=list(p['cases']),
            scope='Input/calibration at execution boundary, no implementation hash lock'))

    def common(self, protocol, body=None):
        path=Path(protocol['input_path']).parent/'common-prompt.md'
        if not path.exists():path.write_text(super().common(protocol),encoding='utf-8')
        base=path.read_text(encoding='utf-8')
        return base if body is None else base+'\n\nFrozen experience guidance; verify applicability:\n'+body

    def _session(self, backend, p, name, role, key, prompt, schema=None, cap=None):
        state = self.state()
        slot = next((s for s in p['slots'] if s['name']==name and s['role']==role and s['case']==key),None)
        if slot is None or any(j['slot']==name for j in state['jobs']):raise EvidenceError('Unplanned slot or prohibited retry')
        cap = cap or slot['requests']
        limits = p.get('total_request_cap', p['analysis_cap'] + p.get('branch_caps',{}).get(state.get('branch'),300))
        spent = sum(j['requests'] for j in state['jobs'] if type(j.get('requests')) is int)
        if cap > slot['requests'] or spent + cap > limits:
            raise EvidenceError('Frozen branch request budget exhausted')
        directory = self.root/'runs'/name;directory.mkdir(parents=True)
        (directory/'prompt.md').write_text(prompt,encoding='utf-8')
        if schema is not None:archive.atomic_json(directory/'schema.json',schema)
        job = dict(slot=name,role=role,case=key,status='started',requests=None,usage=None,seconds=None,request_cap=cap)
        state['jobs'].append(job);self.save(state);started=time.monotonic()
        try:
            local = self._case_protocol(p,key,cap)
            if role=='reflect':local['reflection_evidence_path']=str(self.root/'reflection-evidence')
            result=backend.execute(local,role,prompt,schema,directory)
            archive.atomic_json(directory/'result.json',result)
            job['usage']=result.get('usage');job['requests']=(job['usage'] or {}).get('requests_started')
            if type(job['requests']) is not int or not 0<job['requests']<=cap:
                raise EvidenceError('Unknown or invalid request accounting; stop without retry')
            if result.get('completed') is not True or result.get('infrastructure_valid') is not True \
                    or role=='repair' and result.get('scoring_admissible') is not True:
                raise EvidenceError('Incomplete/infrastructure-invalid session, not a behavioral failure')
            if schema is not None:validate(result['output'],schema)
            if role=='repair':
                outcome=backend.score(local,result['final_candidate'],directory/'score')
                if outcome.get('verdict') not in VERDICTS:raise EvidenceError('Invalid scorer verdict')
                relation_states(outcome)
                job['outcome']=outcome
                original=self.root/'cases'/key/'original-score.json'
                if original.exists():job['original_delta']=delta(load(original),outcome)
                archive.atomic_json(directory/'score.json',outcome)
            job['status']='valid';job['seconds']=time.monotonic()-started;self.save(state)
            return result
        except BaseException as error:
            job.update(status='invalid',error=repr(error),seconds=time.monotonic()-started)
            self.save(state)
            archive.atomic_json(directory/'error.json',dict(error=repr(error),behavioral_failure=False,
                usage=job['usage'],requests=job['requests'],raw_material='backend streams and native archive',no_retry=True))
            raise

    def run(self, execute=False, backend=None):
        p=self.verify()
        if not execute and getattr(backend,'kind',None)!='synthetic_fixture_not_model_or_effectiveness_evidence':
            raise EvidenceError('Live execution requires an explicit --execute')
        if backend is None:
            if p.get('backend'):
                from .docker_backend import DockerBackend
                backend=DockerBackend()
            else:backend=NativeBackend()
        with (Path(p['store'])/'evolution-execution.lock').open('a') as lock:
            try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError as error:raise EvidenceError('Another batch is executing') from error
            state=self.state()
            if state['status'] not in ('analysis_prepared','prepared','candidate_approved','transfer_analysis_prepared','transfer_prepared'):
                raise EvidenceError('Only a fresh or explicitly reviewed stage can execute; no implicit retry')
            entering=state['status'];state['status']='running';state['backend_kind']=backend.kind;self.save(state)
            try:
                self._boundary(p,backend)
                if entering in ('analysis_prepared','transfer_analysis_prepared'):
                    for key in self.state()['analysis_keys']:
                        folder=self.root/'cases'/key/'analysis'
                        result=self._session(backend,p,f'ANALYSIS-{key}','analysis',key,
                            (folder/'prompt.md').read_text(),taxonomy.analysis_schema())
                        archive.atomic_json(folder/'raw-analysis.json',result['output'])
                        archive.atomic_json(folder/'review-input.json',dict(case=key,analysis=result['output'],
                            reviewer=None,approved=None,blocking_issues=[],scope_unknowns=[],evidence=[],reason=''))
                    state=self.state();state['status']='analysis_review';self.save(state)
                elif entering=='prepared':
                    old=[e['bundle'] for e in load(self.root/'M-old.json')['entries']]
                    route=updates.route_view(p['cases']['source']['visible'],old)
                    archive.atomic_json(self.root/'starting-route.json',route)
                    for n in (1,2):
                        self._session(backend,p,f'START-{n}','repair','source',
                            self.common(self._case_protocol(p,'source'),route['experience_text']))
                    self._extract(backend,p,old)
                elif entering=='candidate_approved':
                    self._validate_candidate(backend,p)
                else:
                    self._transfer(backend,p,load(self.root/'candidate.json'))
            except BaseException as error:
                state=self.state();state['status']='cancelled' if isinstance(error,KeyboardInterrupt) else (
                    'reflection_incomplete' if entering=='prepared' and state.get('jobs') and state['jobs'][-1]['role']=='reflect' else 'stopped')
                state['error']=repr(error);self.save(state)
            self.report()
            return self.state()

    def review_analysis(self, request):
        if self.state()['status']!='analysis_review':raise EvidenceError('No public analysis review is pending')
        memory.object_fields(request,{'case','analysis','reviewer','approved','blocking_issues',
                                     'scope_unknowns','evidence','reason'},'public analysis review')
        request=deepcopy(request);key=request.pop('case',None);p=self.verify()
        if key not in p['cases'] or key not in self.state().get('analysis_keys',list(p['cases'])) or not p['cases'][key]['analysis_needed']:
            raise EvidenceError('Unknown analysis case')
        target=self.root/'cases'/key/'approved-visible.json'
        if target.exists():raise EvidenceError('Public analysis was already frozen')
        raw=p['cases'][key]['visible']
        analysis=request.pop('analysis')
        review=routing.review_template(analysis,raw['task'],raw['sources']);review.update(request)
        visible=dict(raw,analysis=analysis,review=review);reviewed(visible)
        archive.atomic_json(target,visible)
        state=self.state()
        keys=state.get('analysis_keys',list(p['cases']))
        if all((self.root/'cases'/k/'approved-visible.json').exists() for k in keys):
            state['status']='transfer_prepared' if state.get('analysis_stage')=='transfer' else 'prepared'
        self.save(state);self.report();return state

    def _extract(self, backend, p, old):
        state=self.state();starting=[j for j in state['jobs'] if j['slot'].startswith('START-')]
        state['branch']='success' if all(j['outcome']['verdict']=='PASS' for j in starting) else 'failure';self.save(state)
        ledger={'TASK':dict(kind='original_task',text=p['cases']['source']['visible']['task'])}
        for i,(name,body) in enumerate(sorted(p['cases']['source']['visible']['sources'].items()),1):
            ledger[f'S{i:03d}']=dict(kind='source_document',path=name,text=body)
        for job in starting:
            result=load(self.root/'runs'/job['slot']/'result.json')
            ledger['O-'+job['slot']]=dict(kind='execution_observation',outcome=job['outcome'],
                original_delta=job['original_delta'],patch=result.get('patch',''),agent_claim=result.get('output'),
                claim_status='Unverified self-report',verified_causes=[])
        parents={b['sha256']:b for b in load(self.root/'prior-experiences.json')}
        selectable={code:b for code,b in parents.items() if b['id'] not in p['parent_selection'] or p['parent_selection'][b['id']]==code}
        context=dict(ledger=ledger,analysis=p['cases']['source']['visible']['analysis'],
            prior_experiences={code:dict(id=b['id'],rules=b['rules'],labels=b['labels'],requires=b['requires'],
                excludes=b['excludes'],qualification='Prior guidance, not new normative evidence') for code,b in parents.items()},
            active_old_versions=[b['sha256'] for b in old],
            original=load(self.root/'cases/source/original-score.json'),expert_feedback=None)
        context['expert_feedback']=[dict(candidate_sha256=row['candidate_sha256'],decision=row['decision'],
            scope=row['scope'],reason=row['reason'],rules=row['rules'],
            qualification='Retained review feedback, not an independently verified cause') for row in load(self.root/'prior-reviews.json')]
        from . import reminders
        context['fixed_manual_material']=dict(taxonomy=taxonomy.definition(),reminders=reminders.definition(),
            qualification='Human-authored fixed checks are not learned experience')
        archive.atomic_json(self.root/'reflection-input.json',context)
        evidence=self.root/'reflection-evidence';evidence.mkdir()
        archive.atomic_json(evidence/'evidence.json',context)
        write_files(evidence/'source',{n:t.encode() for n,t in p['cases']['source']['visible']['sources'].items()})
        retained=[]
        for job in starting:
            native=self.root/'runs'/job['slot']/'native/archive'
            for name in ('events.jsonl','stderr.log','raw-answer.txt','patch.diff','usage.json','response-validation.json'):
                path=native/name
                if path.is_file():
                    target=evidence/'starting'/job['slot']/name;target.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copyfile(path,target);retained.append(str(target.relative_to(evidence)))
        archive.atomic_json(evidence/'index.json',dict(source='Only this source task and its two starting repairs',files=retained))
        prompt=('Extract either no_update with a specific reason, or ONE evidence-backed incremental new/revised '
            'text experience in English. Success does not establish the cause of success; failure does not establish '
            'a cause from assertion names or agent claims. Check novelty against prior guidance. Do not relabel '
            'the fixed manual reminders as learned results. Add a genuinely supported mechanism check or '
            'applicability boundary. Do not pad rule '
            'counts or rewrite untouched rules. Retain applicability, event relations, preservation, exclusions and '
            'falsifiable verification where relevant. Do not include case IDs, source paths, evidence IDs, scorer '
            'names or copyable patches in rule bodies. Unknown causes remain unknown. A prior rule is not normative '
            'proof. Each changed policy needs original-task/source support. Return the typed schema, not a JSON '
            'string or a second full prose copy. The complete authorized material is below and in read-only '
            '/workspace/evidence.json and /workspace/source. Tools may only use closed-grammar workspace reads; '
            'no execution, writes, network, scorer/reference access or additional validation. No retry or extra '
            'organizer session.\n'+canonical(context))
        result=self._session(backend,p,'EXTRACT','reflect','source',prompt,
            updates.schema(p['cases']['source']['visible'],ledger,selectable),cap=2 if state['branch']=='success' else 12)
        raw=result['output'];archive.atomic_json(self.root/'raw-reflection.json',raw)
        composed=updates.compose(raw,p['cases']['source']['visible'],ledger,selectable)
        if composed is None:
            state=self.state();state.update(status='no_update',no_update_reason=raw['reason']);self.save(state);return
        archive.atomic_json(self.root/'composed-candidate.json',composed)
        (self.root/'candidate-experience.md').write_text(memory.render(composed),encoding='utf-8')
        review=dict(reviewer=None,approved=None,blocking_issues=[],novelty_reason='',
            rules=[dict(rule_id=r['id'],supported=None,reason='') for r in composed['rules']])
        archive.atomic_json(self.root/'candidate-review-input.json',review)
        state=self.state();state['status']='candidate_review';self.save(state)

    def review_candidate(self, request):
        if self.state()['status']!='candidate_review':raise EvidenceError('No candidate review is pending')
        memory.object_fields(request,{'reviewer','approved','blocking_issues','novelty_reason','rules'},'candidate review')
        candidate=load(self.root/'composed-candidate.json')
        if request['reviewer']!='execution_agent_visible_input_only' or type(request['approved']) is not bool \
                or not isinstance(request['blocking_issues'],list) or not memory.text(request['novelty_reason']) \
                or not isinstance(request['rules'],list) or any(not isinstance(r,dict) for r in request['rules']) \
                or [r.get('rule_id') for r in request['rules']] != [r['id'] for r in candidate['rules']] \
                or any(type(r.get('supported')) is not bool or not memory.text(r.get('reason')) for r in request['rules']):
            raise EvidenceError('Record the actual AI-assisted per-rule source/novelty/conflict review')
        archive.atomic_json(self.root/'candidate-review.json',dict(request,independent_human_approval=False))
        state=self.state()
        state['status']='candidate_approved' if request['approved'] and not request['blocking_issues'] \
            and all(r['supported'] for r in request['rules']) else 'candidate_rejected'
        self.save(state);self.report();return state

    def _store_candidate(self, p):
        value=load(self.root/'composed-candidate.json');raw=load(self.root/'raw-reflection.json');parent=value['parent']
        paths=[self.root/n for n in ('raw-reflection.json','reflection-input.json','candidate-review.json')]
        codes={path:sha(path.read_bytes()) for path in paths}
        sources=[] if parent is None else deepcopy(parent['audit']['sources'])
        sources += [dict(path=str(path),sha256=codes[path]) for path in paths]
        # Existing immutable source IDs remain IDs, not new log/hash chains.
        sources=list({s['sha256']:s for s in sources}.values())
        links=[]
        for rule,origin in zip(value['rules'],value['origins']):
            if 'change_index' in origin:
                links.append(dict(rule_id=rule['id'],source_sha256=codes[paths[0]],pointer='/changes/'+str(origin['change_index'])))
            else:
                old_id=parent['rules'][origin['parent_index']]['id']
                links.extend(dict(link,rule_id=rule['id']) for link in parent['audit']['rule_links'] if link['rule_id']==old_id)
        if {link['rule_id'] for link in links}!={rule['id'] for rule in value['rules']}:
            raise EvidenceError('Every composed rule needs retained provenance; do not invent missing support')
        payload=dict(schema_version=memory.BUNDLE_VERSION_V2,id=parent['id'] if parent else p['batch_id'],
            version=p['batch_id'],parent_sha256=None if parent is None else parent['sha256'],taxonomy_version=taxonomy.VERSION,
            labels=value['labels'],requires=value['requires'],excludes=value['excludes'],rules=value['rules'],
            review=dict(status='candidate',kind='ai_assisted',source_sha256=codes[paths[2]],
                limitations=['AI-assisted source review; pending independent named operator content acceptance.']+raw['unresolved']),
            audit=dict(sources=sources,rule_links=links,notes=['One program-applied delta; untouched rule bodies retained.'],outcome_refs=[]))
        bundle=memory.add(p['store'],payload,paths+[Path(p['store'])/'sources'/s['sha256'] for s in sources
            if s['sha256'] not in set(codes.values())])
        state=self.state();state['candidate_sha256']=bundle['sha256'];self.save(state)
        archive.atomic_json(self.root/'candidate.json',bundle)
        return bundle

    def _validate_candidate(self, backend, p):
        candidate=self._store_candidate(p)
        old=[e['bundle'] for e in load(self.root/'M-old.json')['entries']]
        new=updates.new_view(old,candidate)
        archive.atomic_json(self.root/'M-new.json',dict(scope='prospective_development_only',bundles=new,
            qualification='Not expert approval or default activation'))
        routes={}
        prompts={}
        for key,c in [('source',p['cases']['source'])]:
            routes[key]={arm:updates.route_view(c['visible'],view) for arm,view in [('old',old),('new',new)]}
            prompts[key]={arm:self.common(self._case_protocol(p,key),route['experience_text']) for arm,route in routes[key].items()}
        archive.atomic_json(self.root/'source-validation-routes.json',routes)
        archive.atomic_json(self.root/'source-validation-prompts.json',prompts)
        boundary=[]
        unresolved_boundary=False
        for boundary_input in p['boundaries']:
            visible=boundary_input['visible']
            left=updates.route_view(visible,old);right=updates.route_view(visible,new)
            unresolved_boundary=unresolved_boundary or right['selected_sha256']==candidate['sha256']
            boundary.append(dict(old=left,new=right,identical=left['experience_text']==right['experience_text'],
                                 lineage=boundary_input['lineage'],model_status='not_run',effect_equivalence=None))
        archive.atomic_json(self.root/'boundary-checks.json',boundary)
        if unresolved_boundary:
            state=self.state();state.update(status='pending_validation',error='A declared boundary selected the candidate; applicability or boundary identity needs review')
            self.save(state);return
        for n in (1,2):self._session(backend,p,f'SOURCE-NEW-{n}','repair','source',prompts['source']['new'])
        state=self.state();before=[j['outcome'] for j in state['jobs'] if j['slot'].startswith('START-')]
        after=[j['outcome'] for j in state['jobs'] if j['slot'].startswith('SOURCE-NEW-')]
        critical=screening.critical_check(before+[load(self.root/'cases/source/original-score.json')],after,
            [v['relation'] for v in p['cases']['source']['lineage']['critical']])
        archive.atomic_json(self.root/'source-preservation.json',critical)
        if critical['lost'] or critical['unknown']:
            state['status']='source_blocked' if critical['lost'] else 'pending_validation';self.save(state);return
        pending=[key for key in ('transfer-1','transfer-2') if not (self.root/'cases'/key/'approved-visible.json').exists()]
        if pending:
            state.update(status='transfer_analysis_prepared',analysis_keys=pending,analysis_stage='transfer')
            self.save(state);return
        self._transfer(backend,p,candidate)

    def _transfer(self,backend,p,candidate):
        old=[e['bundle'] for e in load(self.root/'M-old.json')['entries']]
        new=updates.new_view(old,candidate)
        routes={key:{arm:updates.route_view(c['visible'],view) for arm,view in [('old',old),('new',new)]}
                for key,c in p['cases'].items()}
        prompts={key:{arm:self.common(self._case_protocol(p,key),r['experience_text']) for arm,r in rows.items()}
                 for key,rows in routes.items()}
        archive.atomic_json(self.root/'comparison-routes.json',routes)
        archive.atomic_json(self.root/'comparison-prompts.json',prompts)
        for key in ('transfer-1','transfer-2'):
            for name,arm in [('NEW-1','new'),('OLD-1','old'),('OLD-2','old'),('NEW-2','new')]:
                self._session(backend,p,f'{key}-{name}','repair',key,prompts[key][arm])
        state=self.state()
        before=[j['outcome'] for j in state['jobs'] if j['slot'].startswith('START-')]
        after=[j['outcome'] for j in state['jobs'] if j['slot'].startswith('SOURCE-NEW-')]
        def scores(names):return [j['outcome'] for name in names for j in state['jobs'] if j['slot']==name and j['status']=='valid']
        source=dict(source_unit=p['cases']['source']['lineage']['source_unit'],old=before,new=after,
            original=load(self.root/'cases/source/original-score.json'),
            critical_relations=[v['relation'] for v in p['cases']['source']['lineage']['critical']])
        transfers=[dict(source_unit=p['cases'][key]['lineage']['source_unit'],
            old=scores([key+'-OLD-1',key+'-OLD-2']),new=scores([key+'-NEW-1',key+'-NEW-2']),
            prompts_identical=prompts[key]['old']==prompts[key]['new'],
            original=load(self.root/'cases'/key/'original-score.json'),
            critical_relations=[v['relation'] for v in p['cases'][key]['lineage']['critical']]) for key in ('transfer-1','transfer-2')]
        report=dict(schema_version=screening.VERSION,candidate_sha256=candidate['sha256'],source=source,transfers=transfers,
            budget=dict(within=True,complete=all(type(j.get('requests')) is int for j in state['jobs']),
                        requests=sum(j['requests'] for j in state['jobs']),unknown_requests=0,
                        cap=p['branch_caps'][state['branch']]+p['analysis_cap']),
            source_relationships=dict({key:c['lineage'] for key,c in p['cases'].items()},
                **{f'boundary-{i}':b['lineage'] for i,b in enumerate(p['boundaries'],1)}),slots=state['jobs'],
            raw_artifacts=str(self.root),no_final_test_feedback=True)
        result=screening.save(p['store'],report)
        archive.atomic_json(self.root/'development-screening.json',result)
        state=self.state();state['status']='awaiting_review' if result['gate']['status']=='qualified' else 'pending_validation'
        state['screening']=result['gate'];self.save(state)

    def sync_review(self):
        state=self.state()
        if state.get('candidate_sha256') is not None and state['status'] in ('awaiting_review','pending_validation','accepted','rejected'):
            p=self.verify()
            rows=[r for r in approval.decisions(p['store']) if r['candidate_sha256']==state['candidate_sha256']]
            if rows:
                state['expert_feedback']=rows[-1]
                if rows[-1]['decision']=='reject':state['status']='rejected'
                elif rows[-1]['decision']=='accept' and screening.qualified(p['store'],state['candidate_sha256']):
                    state['status']='accepted'
                self.save(state)
        return state

    def report(self):
        p=self.verify();state=self.sync_review();jobs=state['jobs'];by={j['slot']:j for j in jobs}
        slots=[dict(s,status=by.get(s['name'],{}).get('status','not_run'),
                    outcome=by.get(s['name'],{}).get('outcome'),original_delta=by.get(s['name'],{}).get('original_delta'),
                    usage=by.get(s['name'],{}).get('usage'),actual_requests=by.get(s['name'],{}).get('requests'),
                    seconds=by.get(s['name'],{}).get('seconds')) for s in p['slots']]
        costs={}
        for key in ('input_tokens','output_tokens','total_tokens','cached_input_tokens','reasoning_output_tokens'):
            values=[((j.get('usage') or {}).get('observed_usage_subtotal') or (j.get('usage') or {}).get('total_usage') or {}).get(key) for j in jobs]
            known=[v for v in values if type(v) in (int,float)]
            costs[key]=dict(known_subtotal=sum(known) if known else None,sessions_without_known_usage=len(values)-len(known))
        unknown=[(j.get('usage') or {}).get('usage_unknown_requests') for j in jobs]
        summary=dict(schema_version=p['schema_version'],status=state['status'],branch=state.get('branch'),
            planned=len(slots),started=len(jobs),valid=sum(j['status']=='valid' for j in jobs),
            invalid=sum(j['status']=='invalid' for j in jobs),unstarted=len(slots)-len(jobs),slots=slots,
            valid_behavior_scores=sum('outcome' in j and j['status']=='valid' for j in jobs),
            whole_passes=sum(j.get('outcome',{}).get('verdict')=='PASS' and j['status']=='valid' for j in jobs),
            known_requests=sum(j['requests'] for j in jobs if type(j.get('requests')) is int),
            unknown_request_sessions=sum(type(j.get('requests')) is not int for j in jobs),token_cost=costs,
            requests_with_unknown_token_usage=sum(unknown) if all(type(n) is int for n in unknown) else None,
            known_seconds=sum(j['seconds'] for j in jobs if type(j.get('seconds')) in (int,float)),
            candidate_sha256=state.get('candidate_sha256'),screening=state.get('screening'),
            no_update_reason=state.get('no_update_reason'),error=state.get('error'),
            qualification='Development only; no final evaluation or generalization claim',
            financial_cost=None,engineering_agent_usage=None)
        summary['whole_pass_rate']=summary['whole_passes']/summary['valid_behavior_scores'] if summary['valid_behavior_scores'] else None
        summary['pooled_rate_scope']='Descriptive count over distinct repair slots, not an old/new effect estimate'
        if p['kind']=='development':
            groups={};comparisons=[]
            for key,case in p['cases'].items():
                arms={'old': [f'START-{n}' for n in (1,2)], 'new':[f'SOURCE-NEW-{n}' for n in (1,2)]} if key=='source' else {
                    arm:[f'{key}-{arm.upper()}-{n}' for n in (1,2)] for arm in ('old','new')}
                selected={}
                for arm,names in arms.items():
                    entries=[by[name] for name in names if name in by]
                    valid=[j for j in entries if j['status']=='valid' and 'outcome' in j];selected[arm]=valid
                    token_values=[((j.get('usage') or {}).get('observed_usage_subtotal') or
                                   (j.get('usage') or {}).get('total_usage') or {}).get('total_tokens') for j in entries]
                    count=sum(j['outcome']['verdict']=='PASS' for j in valid)
                    groups[key+'/'+arm]=dict(source_unit=case['lineage']['source_unit'],planned=2,started=len(entries),
                        valid_scores=len(valid),invalid=sum(j['status']=='invalid' for j in entries),unstarted=2-len(entries),
                        whole_passes=count,whole_pass_rate=count/len(valid) if valid else None,
                        known_requests=sum(j['requests'] for j in entries if type(j.get('requests')) is int),
                        unknown_request_sessions=sum(type(j.get('requests')) is not int for j in entries),
                        known_tokens=sum(t for t in token_values if type(t) is int) if any(type(t) is int for t in token_values) else None,
                        sessions_without_known_tokens=sum(type(t) is not int for t in token_values),
                        seconds=sum(j['seconds'] for j in entries if type(j.get('seconds')) in (int,float)))
                if len(selected['old'])==2 and len(selected['new'])==2:
                    comparisons += [dict(case=key,old=old['slot'],new=new['slot'],**delta(old['outcome'],new['outcome']))
                                    for old in selected['old'] for new in selected['new']]
            summary.update(groups=groups,comparisons=comparisons)
        archive.atomic_json(self.root/'summary.json',summary)
        (self.root/'REPORT.md').write_text('# Bounded development v2\n\nNo unstarted or invalid slot is a behavioral failure. '
            'Raw prompts, patches, scores, usage and critical/source evidence remain separate. Content acceptance and '
            'development qualification are both required before explicit default activation.\n\n```json\n'+
            json.dumps(summary,ensure_ascii=False,indent=2)+'\n```\n',encoding='utf-8')
