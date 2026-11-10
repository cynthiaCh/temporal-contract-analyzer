"""Bounded development automation with a mandatory external expert checkpoint."""
import html
import fcntl
import json
from pathlib import Path
import time
import uuid

from . import archive, taxonomy, experience_memory as memory, experience_approval as approval
from . import experience_routing as routing
from .core import EvidenceError, canonical, sha
from .candidate_files import capture, inventory, file_modes, write_files
from .case_evaluation import delta, relation_states, scoring_inputs
from .evolution_backend import NativeBackend, ROLES


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def reflection_schema(visible, ids):
    strings=lambda values:dict(type='array',items=dict(type='string',enum=list(values)))
    known=[f['predicate'] for f in visible['analysis']['facts'] if f['state']=='known']
    absent=[f['predicate'] for f in visible['analysis']['facts'] if f['state']=='contradicted']
    return dict(type='object',properties=dict(
        requires=dict(strings(known),minItems=1),excludes=strings(absent),
        rules=dict(type='array',minItems=5,maxItems=7,items=dict(type='object',properties=dict(
            category=dict(type='string',enum=list(memory.CATEGORIES)),
            body=dict(type='string',minLength=1,maxLength=1600),
            support=dict(strings(ids),minItems=1),
            causal_status=dict(type='string',enum=['documented_relation','observed_relation','hypothesis','unknown'])),
            required=['category','body','support','causal_status'],additionalProperties=False)),
        unresolved=dict(type='array',items=dict(type='string'))),
        required=['requires','excludes','rules','unresolved'],additionalProperties=False)


def validate_reflection(value, visible, ledger):
    memory.object_fields(value,{'requires','excludes','rules','unresolved'},'reflection')
    known={f['predicate'] for f in visible['analysis']['facts'] if f['state']=='known'}
    absent={f['predicate'] for f in visible['analysis']['facts'] if f['state']=='contradicted'}
    memory.strings(value['requires'],'requires',known,True)
    memory.strings(value['excludes'],'excludes',absent)
    memory.strings(value['unresolved'],'unresolved')
    if not isinstance(value['rules'],list) or not 5<=len(value['rules'])<=7:
        raise EvidenceError('Reflection must produce one complete five-to-seven-rule bundle')
    categories=set()
    for rule in value['rules']:
        memory.object_fields(rule,{'category','body','support','causal_status'},'reflection rule')
        if rule['category'] not in memory.CATEGORIES or not memory.text(rule['body']) or len(rule['body'])>1600 \
                or rule['causal_status'] not in ('documented_relation','observed_relation','hypothesis','unknown'):
            raise EvidenceError('Invalid reflection rule')
        memory.strings(rule['support'],'rule support',ledger,True)
        if not any(ledger[key]['kind'] in ('original_task','source_document') for key in rule['support']):
            raise EvidenceError('A normative rule needs task/source support, not observations alone')
        categories.add(rule['category'])
    if categories != set(memory.CATEGORIES):
        raise EvidenceError('Reflection omitted applicability, preservation, boundaries or verification')
    return value


class Evolution:
    def __init__(self, root):
        self.root=Path(root).resolve()

    def state(self):
        return load(self.root/'state.json')

    def save(self,state):
        archive.atomic_json(self.root/'state.json',state)

    def pin(self,name,value):
        path=self.root/name
        if path.exists():raise EvidenceError('Artifact already exists: '+name)
        archive.atomic_json(path,value)
        state=self.state();state['pinned'][name]=sha(path.read_bytes());self.save(state)

    def prepare(self,case_id,visible,store,binary,node,calibration,kind='development',max_rounds=1,
                source_relationship='',backend=None):
        from .case_catalog import case_input
        if self.root.exists():raise EvidenceError('Use a new evolution directory')
        if kind not in ('development','evaluation') or type(max_rounds) is not int or not 1<=max_rounds<=2:
            raise EvidenceError('Choose development/evaluation and one or two bounded rounds')
        if not memory.text(source_relationship):raise EvidenceError('Record source relationship and prior exposure')
        inputs=case_input(case_id)
        if backend is not None:
            from .docker_backend import validate_config
            backend=validate_config(backend)
        files,skipped=capture(Path(inputs['candidate']))
        sources={name:raw.decode('utf-8') for name,raw in files.items()}
        automatic_analysis=visible is None
        if automatic_analysis:
            visible=dict(task=inputs['task'],sources=sources)
        else:
            if set(visible)!={'task','sources','analysis','review'}:
                raise EvidenceError('Provide reviewed visible input or omit visible for automatic analysis')
        if visible['task']!=inputs['task'] or visible['sources']!=sources:
            raise EvidenceError('Visible input must match the complete original candidate and task')
        if not automatic_analysis:
            routing.validate_analysis(visible['analysis'],visible['task'],sources)
        frozen=approval.freeze(store)
        if not automatic_analysis:
            routed=memory.retrieve(store,visible,frozen['sha256'],frozen)
            if routed['route']['reason'] in ('missing_or_drifted_semantic_review','unresolved_semantic_review'):
                raise EvidenceError('Provide a genuine source-bound analysis review before automation')
            if kind=='development' and not any(f['state']=='known' for f in visible['analysis']['facts']):
                raise EvidenceError('No established mechanism premises for development')
            if kind=='development' and not visible['analysis']['obligation_labels']:
                raise EvidenceError('Development requires at least one evidence-supported obligation label')
        else:
            from .preanalysis import analyze_candidate
            ast_report,ast_evidence=analyze_candidate(sources,node=None if backend else node)
        self.root.mkdir(parents=True)
        (self.root/'controller-prompt.md').write_bytes((Path(__file__).resolve().parent/'prompts/MASTER_PROMPT.md').read_bytes())
        write_files(self.root/'input',files,file_modes(Path(inputs['candidate']),files))
        slots = [(f'BASE-{n}','repair') for n in (1,2)] if kind=='development' else [
            (name,'repair') for name in ('B1','A1','A2','B2')]
        if automatic_analysis:
            slots.insert(0,('ANALYSIS','analysis'))
        if kind=='development':
            for round_number in range(1,max_rounds+1):
                slots += [(f'R{round_number}-reflection','reflect')]+[(f'R{round_number}-DEV-{n}','repair') for n in (1,2)]
        protocol=dict(schema_version='expert-gated-evolution-v1',kind=kind,max_rounds=max_rounds,
            batch_id='loop-'+uuid.uuid4().hex[:16],
            case=inputs['case_record'],visible=visible,source_relationship=source_relationship,
            input_path=str(self.root/'input'),candidate_files=inventory(files),
            candidate_sha256=sha(canonical(sources).encode()),file_modes=file_modes(Path(inputs['candidate']),files),
            store=str(Path(store).resolve()),binary=str(Path(binary).resolve()),node=str(Path(node).resolve()),
            calibration=calibration,scoring_inputs=scoring_inputs(inputs['case_record']),
            roles=ROLES,slots=[dict(name=name,role=role,requests=ROLES[role]['requests']) for name,role in slots],
            total_request_cap=sum(ROLES[role]['requests'] for _,role in slots),
            active_snapshot_sha256=frozen['sha256'],no_retry=True,concurrency=1)
        if backend is not None:protocol['backend']=backend
        archive.atomic_json(self.root/'protocol.json',protocol)
        archive.atomic_json(self.root/'active-snapshot.json',frozen)
        pinned=['protocol.json','active-snapshot.json','controller-prompt.md']
        if not automatic_analysis:
            archive.atomic_json(self.root/'initial-route.json',routed)
            pinned.append('initial-route.json')
        else:
            archive.atomic_json(self.root/'analysis/ast-report.json',ast_report)
            archive.atomic_json(self.root/'analysis/ast-evidence.json',ast_evidence)
            path=self.root/'analysis/prompt.md'
            path.write_text(routing.analysis_prompt(visible['task'],sources,ast_evidence),encoding='utf-8')
            pinned+=['analysis/ast-report.json','analysis/ast-evidence.json','analysis/prompt.md']
        self.save(dict(status='analysis_prepared' if automatic_analysis else 'prepared',round=0,jobs=[],
            pinned={name:sha((self.root/name).read_bytes()) for name in pinned},candidate_sha256=None))
        return self.state()

    def verify(self):
        state=self.state()
        for name,code in state['pinned'].items():
            if sha((self.root/name).read_bytes())!=code:raise EvidenceError('Frozen artifact changed: '+name)
        protocol=load(self.root/'protocol.json')
        files,_=capture(self.root/'input')
        if inventory(files)!=protocol['candidate_files'] or file_modes(self.root/'input',files)!=protocol['file_modes']:
            raise EvidenceError('Original candidate drift')
        approved=self.root/'analysis/approved-visible.json'
        if approved.is_file():
            protocol['visible']=load(approved)
        return protocol

    def common(self,protocol,body=None):
        visible=protocol['visible']
        node=protocol['node'] if protocol.get('backend',{}).get('kind')=='docker' else '/runtime/node'
        python='python3' if protocol.get('backend',{}).get('kind')=='docker' else '/usr/bin/python3'
        prompt=(visible['task']+'\n\nCandidate automatic Contract; check against actual task/source:\n'+
            visible['analysis']['contract']+'\n\nRead the candidate source in /workspace. Repair business code only. '
            'Preserve public interfaces, dependencies and build/test configuration. Do not access network or '
            'research archives, install dependencies, or create backups, patches or experiment summaries. '
            'Python performs all mechanical archival. Use '+node+' or '+python+' -B. '
            'Return the maintenance-schema JSON report in English, describing actual changes, validation and gaps.')
        return prompt if body is None else prompt+'\n\nFrozen experience guidance; verify applicability:\n'+body

    def session(self,backend,protocol,name,role,prompt,schema=None):
        self.verify();state=self.state()
        if any(j['slot']==name for j in state['jobs']):raise EvidenceError('Started slot cannot be retried')
        if not any(s['name']==name and s['role']==role for s in protocol['slots']):raise EvidenceError('Unplanned slot')
        directory=self.root/'runs'/name;directory.mkdir(parents=True)
        (directory/'prompt.md').write_text(prompt,encoding='utf-8')
        if schema is not None:archive.atomic_json(directory/'schema.json',schema)
        job=dict(slot=name,role=role,status='started',usage=None,requests=None)
        state['jobs'].append(job);self.save(state)
        started=time.monotonic()
        try:
            result=backend.execute(protocol,role,prompt,schema,directory)
            archive.atomic_json(directory/'result.json',result)
            job.update(usage=result.get('usage'),requests=(result.get('usage') or {}).get('requests_started'))
            if type(job['requests']) is int and (not 0<=job['requests']<=ROLES[role]['requests'] or
                    sum(j['requests'] for j in state['jobs'] if type(j['requests']) is int)>protocol['total_request_cap']):
                raise EvidenceError('Measured request count exceeds frozen budget')
            if result.get('completed') is not True or result.get('infrastructure_valid') is not True \
                    or (role=='repair' and result.get('scoring_admissible') is not True):
                raise EvidenceError('Incomplete or infrastructure-invalid session; no retry or behavioral failure')
            if role=='analysis':
                from ._session_runtime.schema_validator import validate
                validate(result['output'],schema)
            job['status']='valid'
            if role=='repair':
                self.verify()
                outcome=backend.score(protocol,result['final_candidate'],directory/'score')
                relation_states(outcome)
                job['outcome']=outcome
                job['original_delta']=delta(load(self.root/'original-score.json'),outcome)
                archive.atomic_json(directory/'score.json',outcome)
            job['seconds']=time.monotonic()-started;self.save(state)
            return result
        except (Exception,KeyboardInterrupt) as error:
            job.update(status='invalid',error=repr(error),seconds=time.monotonic()-started);self.save(state)
            archive.atomic_json(directory/'error.json',dict(error=repr(error),usage=job['usage'],
                requests=job['requests'],original_service_material='native archive and bridge files if present',
                no_retry=True,behavioral_failure=False))
            raise

    def run(self,execute=False,backend=None):
        protocol=self.verify()
        with (Path(protocol['store'])/'evolution-execution.lock').open('a') as lock:
            try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError as error:raise EvidenceError('Another evolution batch is executing in this memory store') from error
            return self._run(execute,backend)

    def _run(self,execute=False,backend=None):
        if not execute and getattr(backend,'kind',None)!='synthetic_fixture_not_model_or_effectiveness_evidence':
            raise EvidenceError('Live execution requires --execute; preparation never calls models')
        protocol=self.verify();state=self.state()
        if backend is None:
            if protocol.get('backend',{}).get('kind')=='docker':
                from .docker_backend import DockerBackend
                backend=DockerBackend()
            else:backend=NativeBackend()
        if state['status'] not in ('analysis_prepared','prepared','revision_requested'):
            raise EvidenceError('Only a fresh or explicitly revised batch can run; no implicit resume')
        state['status']='running';state['backend_kind']=backend.kind;self.save(state)
        try:
            backend.preflight(protocol)
            if 'analysis' in {s['role'] for s in protocol['slots']} \
                    and not any(job['role']=='analysis' for job in state['jobs']):
                return self.analyze(backend,protocol)
            route=load(self.root/'initial-route.json')
            if not any(job['role']=='repair' for job in state['jobs']):
                self.pin('original-score.json',backend.score(protocol,self.root/'input',self.root/'original'))
                if protocol['kind']=='evaluation':
                    prompts={arm:self.common(protocol,route['experience_text'] if arm=='B' else None) for arm in ('A','B')}
                    self.pin('evaluation-prompts.json',dict(prompts=prompts,identical=prompts['A']==prompts['B']))
                    for name in ('B1','A1','A2','B2'):
                        self.session(backend,protocol,name,'repair',prompts[name[0]])
                    state=self.state();state['status']='evaluation_complete';self.save(state)
                    self.report();return self.state()
                for n in (1,2):
                    self.session(backend,protocol,f'BASE-{n}','repair',self.common(protocol,route['experience_text']))
                state=self.state()
                if all(j['outcome']['verdict']=='PASS' for j in state['jobs'] if j['role']=='repair'):
                    state['status']='starting_repairs_passed';self.save(state);self.report();return state
            return self.develop(backend,protocol)
        except (Exception,KeyboardInterrupt) as error:
            state=self.state();state.update(status='cancelled' if isinstance(error,KeyboardInterrupt) else 'stopped',
                                           error=repr(error),no_retry=True)
            self.save(state);self.report();return state

    def analyze(self,backend,protocol):
        prompt=(self.root/'analysis/prompt.md').read_text(encoding='utf-8')
        result=self.session(backend,protocol,'ANALYSIS','analysis',prompt,taxonomy.analysis_schema())
        raw=result['output'];self.pin('analysis/raw-analysis.json',raw)
        issues=[];validation_issues=[]
        try:routing.validate_analysis(raw,protocol['visible']['task'],protocol['visible']['sources'])
        except routing.CitationError as error:issues=error.issues
        except EvidenceError as error:validation_issues=[str(error)]
        self.pin('analysis/citation-issues.json',issues)
        self.pin('analysis/validation-issues.json',validation_issues)
        # The operator supplies the actual reviewer identity and source evidence.
        request=dict(analysis=raw,reviewer=None,approved=None,blocking_issues=validation_issues,
                     scope_unknowns=[],evidence=[],reason='')
        archive.atomic_json(self.root/'analysis/review-input.json',request)
        state=self.state();state['status']='analysis_citation_review' if issues else 'analysis_review'
        self.save(state);self.report();return state

    def review_analysis(self,request):
        protocol=self.verify();state=self.state()
        if state['status'] not in ('analysis_review','analysis_citation_review'):
            raise EvidenceError('Only a completed automatic analysis can be reviewed')
        memory.object_fields(request,{'analysis','reviewer','approved','blocking_issues',
                                     'scope_unknowns','evidence','reason'},'analysis review')
        visible=protocol['visible']
        analysis=request['analysis']
        from ._session_runtime.schema_validator import validate
        try:validate(analysis,taxonomy.analysis_schema())
        except ValueError as error:raise EvidenceError(str(error)) from error
        routing.validate_analysis(analysis,visible['task'],visible['sources'])
        review=routing.review_template(analysis,visible['task'],visible['sources'])
        review.update({key:value for key,value in request.items() if key!='analysis'})
        visible=dict(visible,analysis=analysis,review=review)
        frozen=load(self.root/'active-snapshot.json')
        routed=memory.retrieve(protocol['store'],visible,frozen['sha256'],frozen)
        if routed['route']['reason'] in ('missing_or_drifted_semantic_review','unresolved_semantic_review'):
            raise EvidenceError('Provide a genuine source-bound analysis review before training')
        if protocol['kind']=='development' and not any(f['state']=='known' for f in analysis['facts']):
            raise EvidenceError('No established mechanism premises for development')
        if protocol['kind']=='development' and not analysis['obligation_labels']:
            raise EvidenceError('Development requires at least one evidence-supported obligation label')
        self.pin('analysis/approved-visible.json',visible)
        self.pin('initial-route.json',routed)
        state=self.state();state['status']='prepared';self.save(state)
        self.report();return state

    def develop(self,backend,protocol):
        state=self.state();number=state['round']+1
        if number>protocol['max_rounds']:raise EvidenceError('Frozen evolution round budget exhausted')
        state['round']=number;self.save(state)
        prior=state['candidate_sha256']
        ledger={'TASK':dict(kind='original_task',text=protocol['visible']['task'])}
        for index,(path,body) in enumerate(sorted(protocol['visible']['sources'].items()),1):
            ledger[f'S{index:03d}']=dict(kind='source_document',path=path,text=body)
        feedback=[]
        for job in state['jobs']:
            if 'outcome' not in job:continue
            result=load(self.root/'runs'/job['slot']/'result.json')
            record=dict(slot=job['slot'],outcome=job['outcome'],original_delta=job['original_delta'],
                patch=result.get('patch',''),agent_claim=result.get('output'),
                claim_status='unverified_self_report_not_authoritative',verified_causes=[])
            ledger['O-'+job['slot']]=dict(kind='execution_observation',record=record)
            feedback.append(record)
        initial=load(self.root/'initial-route.json')
        parent=next((e['bundle'] for e in load(self.root/'active-snapshot.json')['entries']
                     if e['bundle']['sha256']==(initial['selected_memory_record'] or {}).get('sha256')),None)
        if prior is not None:
            parent=next(b for b in memory.records(protocol['store']) if b['sha256']==prior)
        context=dict(fixed_analysis=protocol['visible']['analysis'],original=load(self.root/'original-score.json'),
            ledger=ledger,feedback_order=['O-'+record['slot'] for record in feedback],
            parent_rules=None if parent is None else parent['rules'],
            expert_feedback=state.get('expert_feedback'),causal_status='No causes independently verified.')
        self.pin(f'round-{number}/reflection-input.json',context)
        schema=reflection_schema(protocol['visible'],ledger)
        prompt=('Generate one evidence-backed experience candidate in English using the supplied structured schema. '
            'No tools. Do not repeat a complete experience alongside the rules. Distinguish requirements, source '
            'documents, actual observations, hypotheses and unknown causes. Source defects are not preservation '
            'requirements. Do not infer policy or causes from assertion names, PASS/FAIL or the repair agent report. '
            'Each normative rule needs genuine task/source support; preserve successful behavior and counterexamples. '
            'Cover applicability, event relations, preservation, exclusions and falsifiable verification, including '
            'in-callback timing windows when relevant. Do not prescribe a unique implementation without evidence. '
            'Do not include case IDs, source paths, evidence IDs, scorer names or copyable patches in rule bodies. '
            'The ledger holds the original task, source documents and complete job feedback once; '
            'feedback_order lists observation IDs in execution order. The parent is a prior candidate, not proof. '
            'Keep unknowns explicit. Return only one rules object.\n'+canonical(context))
        result=self.session(backend,protocol,f'R{number}-reflection','reflect',prompt,schema)
        raw=result['output'];self.pin(f'round-{number}/raw-reflection.json',raw)
        try:validate_reflection(raw,protocol['visible'],ledger)
        except (EvidenceError,TypeError,KeyError) as error:
            invalid=self.state();invalid['jobs'][-1].update(status='invalid',material_error=repr(error));self.save(invalid)
            raise
        rules=[dict(id=f'R{i:02d}',category=r['category'],body=r['body']) for i,r in enumerate(raw['rules'],1)]
        body=memory.render(dict(rules=rules))
        body_path=self.root/f'round-{number}'/'experience.md'
        body_path.write_text(body,encoding='utf-8')
        state=self.state();state['pinned'][str(body_path.relative_to(self.root))]=sha(body_path.read_bytes());self.save(state)
        self.pin(f'round-{number}/mechanical-review.json',dict(kind='mechanical_and_model_self_check_only',
            semantic_expert_approval=False,rule_ids_valid=True,source_links_present=True,body_sha256=memory.digest(body),
            unresolved=raw['unresolved'],source_support_does_not_prove_meaning=True))
        for n in (1,2):
            self.session(backend,protocol,f'R{number}-DEV-{n}','repair',self.common(protocol,body))
        state=self.state()
        bases=[j for j in state['jobs'] if j['slot'].startswith('BASE-')]
        devs=[j for j in state['jobs'] if j['slot'].startswith(f'R{number}-DEV-')]
        comparisons=[dict(development=d['slot'],starting=b['slot'],**delta(b['outcome'],d['outcome'])) for d in devs for b in bases]
        self.pin(f'round-{number}/comparisons.json',comparisons)
        source_paths=[self.root/f'round-{number}'/name for name in ('raw-reflection.json','reflection-input.json',
                       'mechanical-review.json','comparisons.json')]
        source_paths += [self.root/'runs'/j['slot']/'score.json' for j in devs]
        sources=[dict(path=str(p),sha256=sha(p.read_bytes())) for p in source_paths]
        code=sources[0]['sha256']
        payload=dict(schema_version=memory.BUNDLE_VERSION,id=parent['id'] if parent else protocol['batch_id'],
            version=f"{protocol['batch_id']}-r{number}",parent_sha256=None if parent is None else parent['sha256'],
            taxonomy_version=taxonomy.VERSION,labels=[v['code'] for v in protocol['visible']['analysis']['obligation_labels']],
            requires=raw['requires'],excludes=raw['excludes'],rules=rules,
            review=dict(status='candidate',kind='ai_assisted',source_sha256=sources[2]['sha256'],
                limitations=['Pending named expert review; mechanical and model self-checks are not semantic approval.']+raw['unresolved']),
            audit=dict(sources=sources,rule_links=[dict(rule_id=r['id'],source_sha256=code,pointer=f'/rules/{i}')
                for i,r in enumerate(rules)],notes=['Program-composed from one raw reflection; original bodies unchanged.'],
                outcome_refs=[dict(source_sha256=s['sha256'],pointer='') for s in sources[3:]]))
        bundle=memory.add(protocol['store'],payload,source_paths)
        if memory.render(bundle)!=body:raise EvidenceError('Candidate body changed during validation')
        state=self.state();state.update(status='awaiting_expert',candidate_sha256=bundle['sha256'],comparisons=comparisons)
        self.save(state);self.report();return state

    def expert(self,request,execute=False,backend=None):
        with (self.root/'expert.lock').open('a') as lock:
            try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError as error:raise EvidenceError('An expert action is already being applied') from error
            return self._expert(request,execute,backend)

    def _expert(self,request,execute=False,backend=None):
        protocol=self.verify();state=self.state()
        if protocol['kind']!='development' or state['status']!='awaiting_expert':
            raise EvidenceError('Only a fully validated development candidate can enter expert review')
        memory.object_fields(request,{'candidate_sha256','report_sha256','reviewed_outcomes','decision'},'expert submission')
        report=self.root/f"round-{state['round']}"/'expert-packet.json'
        if request['candidate_sha256']!=state['candidate_sha256'] or request['report_sha256']!=sha(report.read_bytes()) \
                or request['reviewed_outcomes'] is not True:
            raise EvidenceError('Expert must review the exact candidate and complete outcome report')
        decision=request['decision']
        if not isinstance(decision,dict):raise EvidenceError('Expert decision must be an object')
        if decision.get('decision')=='accept' and not any(c['gained'] for c in state['comparisons']) \
                and decision.get('scope')!='exploratory':
            raise EvidenceError('No observed development gain: acceptance must explicitly be exploratory')
        row=approval.decide(protocol['store'],state['candidate_sha256'],decision,request['report_sha256'])
        self.pin(f"round-{state['round']}/expert-decision.json",row)
        state=self.state();state['expert_feedback']=row
        if row['decision']=='accept':
            state['status']='accepted';self.save(state)
            self.pin('accepted-active-snapshot.json',approval.freeze(protocol['store']))
        elif row['decision']=='revise':
            state['status']='revision_requested' if state['round']<protocol['max_rounds'] else 'revision_budget_exhausted'
            self.save(state)
        else:
            state['status']='rejected';self.save(state)
        self.report()
        return self.run(execute=True,backend=backend) if execute and state['status']=='revision_requested' else self.state()

    def report(self):
        state=self.state();protocol=load(self.root/'protocol.json')
        jobs={j['slot']:j for j in state['jobs']}
        route=load(self.root/'initial-route.json') if (self.root/'initial-route.json').is_file() else None
        groups={}
        for slot in protocol['slots']:
            if slot['role']!='repair':continue
            name=slot['name']
            group=name[0] if protocol['kind']=='evaluation' else (
                'starting_'+(route['route']['condition'] if route else 'pending_analysis') if name.startswith('BASE-') else name.split('-DEV')[0]+'-candidate')
            row=groups.setdefault(group,dict(planned=0,started=0,valid_scores=0,invalid=0,unstarted=0,whole_passes=0))
            row['planned']+=1
            if name not in jobs:row['unstarted']+=1;continue
            row['started']+=1
            if jobs[name]['status']=='invalid':row['invalid']+=1
            if jobs[name].get('outcome') is not None and jobs[name]['status']=='valid':
                row['valid_scores']+=1;row['whole_passes']+=jobs[name]['outcome']['verdict']=='PASS'
        for row in groups.values():
            row['whole_pass_rate']=row['whole_passes']/row['valid_scores'] if row['valid_scores'] else None
        token_cost={}
        for key in ('input_tokens','cached_input_tokens','output_tokens','reasoning_output_tokens','total_tokens'):
            values=[(job['usage'] or {}).get('observed_usage_subtotal') or {} for job in jobs.values()]
            known=[value[key] for value in values if type(value.get(key)) in (int,float)]
            token_cost[key]=dict(known_subtotal=sum(known) if known else None,
                sessions_without_known_subtotal=len(values)-len(known),
                full_total=None if any(type(((job['usage'] or {}).get('total_usage') or {}).get(key)) not in (int,float)
                    for job in jobs.values()) or not jobs else sum(job['usage']['total_usage'][key] for job in jobs.values()))
        unknown_usage=[(j['usage'] or {}).get('usage_unknown_requests') for j in jobs.values()]
        known_unknown_usage=[v for v in unknown_usage if type(v) is int]
        summary=dict(status=state['status'],backend_kind=state.get('backend_kind'),kind=protocol['kind'],
            native_execution_attempted=bool(jobs) and state.get('backend_kind')=='native_research_runner',
            planned=len(protocol['slots']),started=len(jobs),valid=sum(j['status']=='valid' for j in jobs.values()),
            invalid=sum(j['status']=='invalid' for j in jobs.values()),unstarted=len(protocol['slots'])-len(jobs),
            behavior_vectors={key:job.get('outcome') for key,job in jobs.items() if job['role']=='repair'},
            known_requests=sum(j['requests'] for j in jobs.values() if type(j['requests']) is int),
            sessions_with_unknown_requests=sum(j['requests'] is None for j in jobs.values()),
            requests_with_unknown_token_usage=sum(known_unknown_usage) if len(known_unknown_usage)==len(jobs) else None,
            known_requests_with_unknown_token_usage=sum(known_unknown_usage),
            sessions_with_missing_usage_counter=len(jobs)-len(known_unknown_usage),
            groups=groups,known_seconds=sum(j.get('seconds',0) for j in jobs.values()),
            sessions_with_unknown_seconds=sum('seconds' not in j for j in jobs.values()),token_cost=token_cost,
            usage=[dict(slot=j['slot'],usage=j['usage']) for j in jobs.values()],comparisons=state.get('comparisons',[]),
            no_generalization_claim=True,no_test_feedback_learning=protocol['kind']=='evaluation')
        archive.atomic_json(self.root/'summary.json',summary)
        if state['status']=='awaiting_expert':
            bundle=next(b for b in memory.records(protocol['store']) if b['sha256']==state['candidate_sha256'])
            parent=next((b for b in memory.records(protocol['store']) if b['sha256']==bundle['parent_sha256']),None)
            changes=dict(parent_sha256=bundle['parent_sha256'],parent_rules=[] if parent is None else parent['rules'],
                candidate_rules=bundle['rules'],mechanisms={key:dict(before=None if parent is None else parent[key],after=bundle[key])
                    for key in ('labels','requires','excludes')})
            packet=dict(candidate=bundle,changes=changes,starting_route=load(self.root/'initial-route.json'),summary=summary,
                original=load(self.root/'original-score.json'),expert_review_required=True,
                claim='Mechanical checks and development observations do not establish semantic correctness or benefit.')
            target=f"round-{state['round']}/expert-packet.json"
            if not (self.root/target).exists():self.pin(target,packet)
            request=dict(candidate_sha256=bundle['sha256'],report_sha256=sha((self.root/target).read_bytes()),
                reviewed_outcomes=False,decision=dict(reviewer='',decision='revise',scope='exploratory',reason='',
                    rules=[dict(rule_id=r['id'],supported=False,reason='') for r in bundle['rules']]))
            archive.atomic_json(self.root/f"round-{state['round']}/decision-template.json",request)
            self.review_html(packet,request)
        (self.root/'REPORT.md').write_text('# Expert-gated evolution\n\n'+
            'This is a bounded development/evaluation execution record. Expert activation is a separate operator action.\n\n'+
            '```json\n'+json.dumps(summary,ensure_ascii=False,indent=2)+'\n```\n',encoding='utf-8')

    def review_html(self,packet,request):
        number=self.state()['round'];directory=self.root/f'round-{number}'
        data=json.dumps(request,ensure_ascii=False).replace('<','\\u003c')
        rows=''.join('<fieldset><legend>'+html.escape(r['id'])+'</legend><p>'+html.escape(r['body'])+
            '</p><label><input type="checkbox" class="supported">Evidence supports this rule and its bounds</label>'+
            '<p><textarea class="reason" placeholder="Optional: evidence, preservation obligations and counterexamples"></textarea></p></fieldset>'
            for r in packet['candidate']['rules'])
        body='''<!doctype html><html lang="en"><meta charset="utf-8"><title>Expert experience review</title>
<style>body{max-width:960px;margin:2rem auto;font:16px system-ui}pre{white-space:pre-wrap}textarea{width:95%;min-height:5rem}fieldset{margin:1rem 0}</style>
'''+('''<p><strong>SYNTHETIC FIXTURE — no model executed. These are not real repair results or actual expert approval.</strong></p>'''
        if packet['summary']['backend_kind']=='synthetic_fixture_not_model_or_effectiveness_evidence' else '')+'''
<h1>Expert review — no automatic activation</h1><p>Read the full evidence and outcomes, then download your decision.
Apply it with the explicit evolution expert command. This page never calls a model or changes the library.</p>
<p><a href="reflection-input.json">Task, source, actual patches and full feedback</a> ·
<a href="raw-reflection.json">Original model object</a> · <a href="expert-packet.json">Exact candidate and outcome packet</a></p>
<details><summary>Exact parent rules and candidate changes</summary><pre>'''+html.escape(json.dumps(packet['changes'],ensure_ascii=False,indent=2))+'''</pre></details>
<details open><summary>Complete outcomes, regressions and costs</summary><pre>'''+html.escape(json.dumps(packet['summary'],ensure_ascii=False,indent=2))+'''</pre></details>
<form id="review"><label>Your name <input id="name" required></label> <label>Decision <select id="decision"><option>revise</option><option>reject</option><option>accept</option></select></label>
<label>Scope <select id="scope"><option>exploratory</option><option>research</option></select></label>'''+rows+'''
<label>Overall reason (optional)<textarea id="overall"></textarea></label>
<p><label><input id="outcomes" type="checkbox" required>I reviewed all successes, losses, unknowns and costs.</label></p>
<button>Download decision JSON</button></form><script>const request='''+data+''';
document.querySelector('#review').addEventListener('submit',e=>{e.preventDefault();
const d=structuredClone(request);d.reviewed_outcomes=document.querySelector('#outcomes').checked;
d.decision.reviewer=document.querySelector('#name').value;d.decision.decision=document.querySelector('#decision').value;
d.decision.scope=document.querySelector('#scope').value;d.decision.reason=document.querySelector('#overall').value;
document.querySelectorAll('fieldset').forEach((f,i)=>{d.decision.rules[i].supported=f.querySelector('.supported').checked;d.decision.rules[i].reason=f.querySelector('.reason').value;});
const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(d,null,2)],{type:'application/json'}));a.download='expert-decision.json';a.click();URL.revokeObjectURL(a.href);});</script></html>'''
        (directory/'expert-review.html').write_text(body,encoding='utf-8')
