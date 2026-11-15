"""Within-task trajectories. Imports never execute a model or candidate."""
from copy import deepcopy
from pathlib import Path
import difflib
import fcntl
import json
import re
import shutil
import subprocess
import time

from . import archive, experience_approval as approval, experience_memory as memory, taxonomy
from .candidate_files import capture, inventory, write_files
from .core import EvidenceError, canonical, sha
from ._session_runtime.model_settings import resolve_profile, identity

VERSION = 'tempoevo-trajectory-v11'
MODEL = identity(resolve_profile())
CONDITIONS = ('baseline', 'contract', 'bm25', 'structured', 'fixed_contract')
LIMITS = dict(selection=dict(requests=12, seconds=600), routing=dict(requests=12, seconds=600), contract=dict(requests=12, seconds=600), action=dict(requests=24, seconds=600),
              diagnosis=dict(requests=12, seconds=600), extract=dict(requests=12, seconds=600))
TERMINAL = ('passed', 'repair_exhausted', 'execution_invalid', 'awaiting_expert_summary', 'awaiting_content_review', 'cancelled')
CONTRACT_FIELDS = ('scope', 'triggers', 'ordering_barriers', 'lifecycle_identity',
                   'preservation', 'forbidden_effects', 'checkpoints', 'unknowns')


def read(path):
    return json.loads(Path(path).read_text())


def visible_verdict(attempts):
    values=[a['visible_passed'] for a in attempts]
    if any(v is True for v in values):return True
    return False if values and all(v is False for v in values) else None


def obj_schema(properties):
    return dict(type='object', properties=properties, required=list(properties), additionalProperties=False)


STR = dict(type='string', minLength=1)
STRINGS = dict(type='array', items=STR)
EVIDENCE = dict(type='array', minItems=1, items=obj_schema(dict(file=STR, quote=STR)))
CONTRACT_SCHEMA = obj_schema(dict({k: STRINGS for k in CONTRACT_FIELDS},
    obligations=dict(type='array', minItems=1, items=obj_schema(dict(id=STR, text=STR))),
    supporting_evidence=EVIDENCE))
DIAGNOSIS_SCHEMA = obj_schema(dict(diagnosis=dict(type='string', enum=['implementation_gap','contract_gap','both','unknown']),
    contract_after=CONTRACT_SCHEMA, structured_delta=STRINGS, supporting_evidence=EVIDENCE,
    remaining_unknowns=STRINGS, explanation=STR))
DIAGNOSIS_SCHEMA['properties']['routing_analysis']=dict(anyOf=[dict(type='null'),taxonomy.analysis_schema()])
DIAGNOSIS_SCHEMA['required'].append('routing_analysis')

PREDICATES = list(taxonomy.definition()['mechanism_predicates'])
EXPERIENCE_SCHEMA = obj_schema(dict(
    labels=dict(type='array',minItems=1,items=dict(type='string',enum=list(taxonomy.CODES))),
    requires=dict(type='array',minItems=1,items=dict(type='string',enum=PREDICATES)),
    excludes=dict(type='array',items=dict(type='string',enum=PREDICATES)),
    rules=dict(type='array',minItems=1,items=obj_schema(dict(
        category=dict(type='string',enum=list(memory.CATEGORIES)),body=STR))),limitations=STRINGS))
REFLECTION_UPDATE_SCHEMA=obj_schema(dict(operation=dict(type='string',enum=['new','evidence','revise','merge']),
    target_sha256s=STRINGS,reason=STR,change_summary=STRINGS,
    failure_attribution=dict(type='string',enum=['experience_gap','implementation_gap','unknown','not_applicable']),
    supporting_attempts=dict(type='array',items=dict(type='integer',minimum=1,maximum=3))))
REFLECTION_SCHEMA=obj_schema(dict(experience=EXPERIENCE_SCHEMA,update=REFLECTION_UPDATE_SCHEMA))


def evidence_valid(rows, task, sources):
    for row in rows:
        task_ref=row['file'].strip().casefold() in ('task','original task')
        body=task if task_ref else sources.get(row['file'],'')
        def normalized(text):
            # Markdown inline-code delimiters change presentation, not wording.
            # Keep source-code backticks significant outside Markdown/task text.
            if task_ref or Path(row['file']).suffix.lower()=='.md':
                text=re.sub(r'(?<!`)`([^`\n]+)`(?!`)',r'\1',text)
            return ' '.join(text.split())
        quote=normalized(row['quote'])
        if not quote or quote not in normalized(body):raise EvidenceError('Unsupported public-source citation')


def check_contract(contract, task, sources, before=None):
    from ._session_runtime.schema_validator import validate
    validate(contract, CONTRACT_SCHEMA)
    evidence_valid(contract['supporting_evidence'],task,sources)
    obligations={r['id']:r['text'] for r in contract['obligations']}
    if len(obligations)!=len(contract['obligations']):raise EvidenceError('Duplicate obligation identity')
    if before and any(obligations.get(r['id'])!=r['text'] for r in before['obligations']):
        raise EvidenceError('Cannot delete or weaken retained obligations')


class Trajectory:
    def __init__(self, root):self.root=Path(root).resolve()
    def save(self, name, value):archive.atomic_json(self.root/name,value)
    def state(self):return read(self.root/'state.json')
    def status(self, status, **fields):
        state=self.state()
        if state.get('cancelled') and status!='cancelled':return state
        state.update(status=status,**fields);self.save('state.json',state);return state

    def prepare(self, config):
        if self.root.exists():raise EvidenceError('Use a new trajectory root')
        cfg=deepcopy(config)
        policy=cfg.get('learning_policy','frozen')
        if policy not in ('frozen','online'):raise EvidenceError('Invalid learning policy')
        if policy=='online' and (cfg.get('mode')!='learning' or cfg.get('condition') not in ('structured','bm25') or not cfg.get('online_memory') or not memory.text(cfg.get('task_id'))):raise EvidenceError('Online memory requires memory-enabled learning and an explicit training pool')
        if policy!='online' and cfg.get('online_memory'):raise EvidenceError('Frozen/testing trajectories cannot access an online pool')
        cfg['learning_policy']=policy
        for key in ('task','candidate','store','mode','condition'):
            if key not in cfg:raise EvidenceError('Missing '+key)
        if cfg['mode'] not in ('learning','testing') or cfg['condition'] not in CONDITIONS:raise EvidenceError('Invalid mode/condition')
        if any(key in cfg for key in ('public_checks','repair_policy','testing_policy')):
            raise EvidenceError('Repair strategy switches were removed; training and testing always use Oracle acceptance')
        if cfg.get('acceptance_policy','oracle_pass_or_action_budget_exhausted')!='oracle_pass_or_action_budget_exhausted':
            raise EvidenceError('Historical protocol is read-only; prepare a new trajectory')
        if cfg.get('required_visible_checks'):
            raise EvidenceError('Training and testing use public checks as advisory feedback only')
        from .evaluation_split import enforce
        split=enforce(cfg)
        if split:cfg['evaluation_split']=split
        from .training_acceptance import validate_mapping
        if cfg['mode']=='learning' and not cfg.get('training_evaluator'):raise EvidenceError('Learning requires training_evaluator; public PASS is not acceptance')
        if cfg['mode']=='testing' and (cfg.get('training_evaluator') or cfg.get('training_feedback')):raise EvidenceError('Testing cannot use training acceptance feedback')
        if cfg['mode']=='testing' and cfg.get('training_feedback_used'):raise EvidenceError('Training-exposed cases cannot be independent tests')
        validate_mapping(cfg.get('training_feedback',{}))
        if type(cfg.get('required_visible_checks',True)) is not bool:raise EvidenceError('required_visible_checks must be boolean')
        if cfg['mode']=='testing':
            registry=Path(__file__).resolve().parents[1]/'experiments/training-cases.json'
            if registry.exists() and cfg.get('task_id') in {r['id'] for r in read(registry)['cases']}:raise EvidenceError('Known exposed development case cannot be an independent test')
        attempts=cfg.get('max_attempts',3)
        if type(attempts) is not int or not 1<=attempts<=3:raise EvidenceError('At most three Actions total')
        try:settings=resolve_profile(cfg.get('model_profile'),cfg.get('model_config'))
        except (ValueError,TypeError,OSError) as error:raise EvidenceError('Invalid model configuration: '+str(error)) from error
        if cfg.get('model',identity(settings))!=identity(settings):raise EvidenceError('Model must match the selected profile')
        cfg['model_settings']=settings
        cfg['model_profile']=settings['profile']
        cfg.pop('model_config',None)  # Freeze resolved values, not a mutable external file.
        if cfg['mode']=='testing' and not cfg.get('gold_evaluator'):raise EvidenceError('Testing requires a separate gold evaluator')
        if cfg['mode']=='testing' and not cfg.get('memory_snapshot'):raise EvidenceError('Testing requires explicit frozen approved bank')
        source=Path(cfg['candidate']).resolve()
        if self.root==source or source in self.root.parents:raise EvidenceError('Trajectory must be outside candidate')
        files,_=capture(source);sources={k:v.decode('utf-8') for k,v in files.items()}
        store=Path(cfg['store']).resolve()
        if policy=='online':
            pool=Path(cfg['online_memory']).resolve()
            if any(pool==p or pool in p.parents or p in pool.parents for p in (store,source,self.root)):raise EvidenceError('Online pool must be separate from long-term store and trajectory/candidate')
            cfg['online_memory']=str(pool)
        bank=approval.validate_snapshot(store,cfg['memory_snapshot']) if cfg.get('memory_snapshot') else approval.freeze(store)
        from .preanalysis import analyze_candidate
        if cfg.get('backend',{}).get('kind')=='docker':
            from .tempoevo_docker import analyze,image_identity
            image_identity(cfg['backend']['grader_image'])
            full,ast=analyze(sources,cfg['backend'])
        else:full, ast=analyze_candidate(sources,node=cfg.get('node'))
        evaluator_hashes={}
        for name in ('visible_evaluator','training_evaluator','gold_evaluator'):
            if not cfg.get(name):continue
            command=cfg[name].get('command')
            if not isinstance(command,list) or not command or any(not isinstance(x,str) or not x for x in command):raise EvidenceError('Evaluator command must be argv')
            cfg[name].setdefault('seconds',60)
            if type(cfg[name]['seconds']) not in (int,float) or not 0<cfg[name]['seconds']<=600:raise EvidenceError('Invalid evaluator timeout')
            if cfg[name].get('image'):
                from .tempoevo_docker import image_identity,evaluator_inputs
                image_identity(cfg[name]['image'])
                mounts=evaluator_inputs(cfg[name])
                cfg[name]['inputs']={str(path):target for path,target in mounts}
                for path,_ in mounts:
                    if source in path.parents:raise EvidenceError('Trusted evaluators must be outside candidate')
                    evaluator_hashes[str(path)]=sha(path.read_bytes())
                continue
            command=cfg[name].get('command')
            if not isinstance(command,list) or not command or any(not isinstance(x,str) for x in command):raise EvidenceError('Evaluator command must be argv')
            normalized=[]
            for arg in command:
                path=Path(shutil.which(arg) or arg).resolve()
                if path.is_file():
                    if source==path or source in path.parents:raise EvidenceError('Trusted evaluators must be outside candidate')
                    evaluator_hashes[str(path)]=sha(path.read_bytes());normalized.append(str(path))
                else:normalized.append(arg)
            cfg[name]['command']=normalized
        for key in ('binary','node'):
            if cfg.get(key) and Path(cfg[key]).is_file():evaluator_hashes[str(Path(cfg[key]).resolve())]=sha(Path(cfg[key]).read_bytes())
        self.root.mkdir(parents=True);write_files(self.root/'original',files)
        self.save('ast-report.json',full);self.save('ast-evidence.json',ast);self.save('memory-snapshot.json',bank)
        limits=cfg.get('limits',LIMITS)
        if set(limits)!=set(LIMITS):raise EvidenceError('Declare every LLM stage limit')
        for role,limit in limits.items():
            if set(limit)!= {'requests','seconds'} or type(limit['requests']) is not int or not 1<=limit['requests']<=LIMITS[role]['requests'] or not 0<limit['seconds']<=600:
                raise EvidenceError('Invalid stage limits')
        uses_contract=cfg['condition']!='baseline'
        total=attempts*limits['action']['requests']+((attempts-1)*limits['diagnosis']['requests']+limits['contract']['requests'] if uses_contract else 0)+(limits['extract']['requests'] if cfg['mode']=='learning' else 0)
        if cfg['condition'] in ('structured','fixed_contract') and not cfg.get('routing_analysis'):total+=limits['routing']['requests']
        if cfg['condition'] in ('structured','fixed_contract'):
            total+=(attempts if cfg['condition']=='structured' else 1)*limits['selection']['requests']
        from . import semantic_retrieval
        cfg['retrieval_policy']=(dict(version=semantic_retrieval.VERSION,max_candidates=semantic_retrieval.MAX_CANDIDATES,
            max_experiences=semantic_retrieval.MAX_EXPERIENCES,max_characters=semantic_retrieval.MAX_CHARACTERS)
            if cfg['condition'] in ('structured','fixed_contract') else
            dict(version='bm25-v1' if cfg['condition']=='bm25' else 'no-memory',max_experiences=5 if cfg['condition']=='bm25' else 0))
        cfg.update(schema_version=VERSION,model=identity(settings),memory_snapshot=bank,max_attempts=attempts,limits=limits,total_request_cap=total,
            store=str(store),original_inventory=inventory(files),feedback_fields=['observations','regressions','unknowns'],
            required_visible_checks=False,acceptance_policy='oracle_pass_or_action_budget_exhausted',
            evaluation_budget=dict(visible=attempts if cfg.get('visible_evaluator') else 0,oracle=attempts),
            held_out_eligible=False,split_status='oracle_verdict_feedback_testing' if cfg['mode']=='testing' else 'unverified_no_independent_split_evidence',
            memory_snapshot_sha256=bank['sha256'],source_sha256=sha(canonical(sources).encode()))
        self.save('protocol.json',cfg);self.save('state.json',dict(status='prepared',attempts=[],stages=[],contract=None,diagnoses=[],cancelled=False))
        # Freeze executables and their static inputs; no evaluator output enters model context here.
        self.save('binding.json',dict(protocol=sha((self.root/'protocol.json').read_bytes()),
            bank=sha((self.root/'memory-snapshot.json').read_bytes()),ast=sha((self.root/'ast-evidence.json').read_bytes()),
            implementation=sha(Path(__file__).read_bytes()),evaluators=evaluator_hashes,
            runtime={str(path):sha(path.read_bytes()) for path in [Path(__file__).with_name(name) for name in ('semantic_retrieval.py','experience_routing.py','experience_memory.py','experience_updates.py','compact_experience.py','taxonomy.py','contract-taxonomy.json')]+[Path(__file__).with_name('evaluation_split.py'),Path(__file__).resolve().parents[1]/'experiments/evaluation-splits.json',Path(__file__).with_name('online_memory.py'),Path(__file__).with_name('experience_reflection.py'),Path(__file__).with_name('training_acceptance.py'),Path(__file__).with_name('stage_retry.py'),Path(__file__).with_name('tempoevo_backend.py'),Path(__file__).with_name('tempoevo_docker.py'),Path(__file__).with_name('docker_backend.py'),Path(__file__).with_name('execution_backend.py'),Path(__file__).with_name('_session_runtime')/'model-profiles.json',Path(__file__).with_name('_session_runtime')/'research-config.toml']+list(Path(__file__).with_name('_session_runtime').glob('*.py'))}))
        self.report();return self.state()

    def verify(self):
        p=read(self.root/'protocol.json')
        if p.get('schema_version')!=VERSION or p.get('acceptance_policy')!='oracle_pass_or_action_budget_exhausted':raise EvidenceError('Historical protocol is read-only; prepare a new V11 root')
        from .evaluation_split import enforce
        enforce(p)
        binding=read(self.root/'binding.json')
        for name,key in [('protocol.json','protocol'),('memory-snapshot.json','bank'),('ast-evidence.json','ast')]:
            if sha((self.root/name).read_bytes())!=binding[key]:raise EvidenceError('Frozen V4 input drift')
        if sha(Path(__file__).read_bytes())!=binding['implementation']:raise EvidenceError('Frozen implementation changed')
        online_digest=self.state().get('online_snapshot_sha256')
        if online_digest:
            from .online_memory import validate_snapshot
            snapshot=validate_snapshot(read(self.root/'online-snapshot.json'))
            if snapshot['sha256']!=online_digest:raise EvidenceError('Online task snapshot changed')
        for path,digest in dict(binding['evaluators'],**binding['runtime']).items():
            if sha(Path(path).read_bytes())!=digest:raise EvidenceError('Frozen evaluator/runtime drift')
        if inventory(capture(self.root/'original')[0])!=p['original_inventory']:raise EvidenceError('Original code drift')
        for attempt in self.state()['attempts']:
            if inventory(capture(self.root/'attempts'/str(attempt['number'])/'candidate')[0])!=attempt['candidate_inventory']:raise EvidenceError('Archived candidate drift')
        return p

    def cancel(self):
        if read(self.root/'protocol.json').get('schema_version')!=VERSION:raise EvidenceError('Historical protocol is read-only')
        return self.status('cancelled',cancelled=True,stop_reason='cancelled')

    def retrieve(self,p,backend=None,selection_key='selection-1'):
        bank=p['memory_snapshot'];bundles=[e['bundle'] for e in bank['entries']]
        condition=p['condition'];result=dict(selected_sha256s=[],experience_text=None,reason='condition_has_no_memory')
        if condition=='bm25':
            hits=memory.search_records(bundles,p['task'],limit=5,include_all=True)['results']
            selected=[next(b for b in bundles if b['sha256']==h['sha256']) for h in hits]
            result=dict(selected_sha256s=[b['sha256'] for b in selected],experience_text=memory.delivery_text(selected),reason='bm25_frozen_bank')
        elif condition in ('structured','fixed_contract'):
            from . import semantic_retrieval as retrieval
            sources={k:v.decode() for k,v in capture(self.root/'original')[0].items()};a=p['routing_analysis']
            recalled=retrieval.recall(p['task'],sources,a,bundles)
            self.save('retrieval/'+selection_key+'-recall.json',recalled)
            if recalled['candidates']:
                if backend is None:raise EvidenceError('Structured delivery requires explicit semantic assessment execution')
                assessment=self._step(p,backend,selection_key,'selection',
                    retrieval.payload(p['task'],sources,read(self.root/'ast-evidence.json'),a,recalled))['output']
                result=retrieval.select(assessment,recalled,a,p['task'],sources,bundles)
            else:
                result=dict(selected_sha256s=[],experience_text=None,reason='no_mechanism_eligible_experience',route=recalled['mechanism_route'])
        online={r['bundle']['sha256'] for r in read(self.root/'online-snapshot.json')['entries']} if p.get('learning_policy')=='online' else set()
        result['provisional_sha256s']=[c for c in result.get('selected_sha256s',[]) if c in online]
        if result['provisional_sha256s']:result['experience_text']='TRAINING ONLY: includes unreviewed provisional guidance with unknown effectiveness. Check against public task/source evidence.\n'+result['experience_text']
        self.save('delivery.json',result);return result

    def _step(self,p,backend,key,kind,payload):
        directory=self.root/'stages'/key;state=self.state()
        existing=next((s for s in state['stages'] if s['key']==key),None)
        if existing:
            if existing['status']=='complete':
                if sha((directory/'result.json').read_bytes())!=existing['result_sha256']:raise EvidenceError('Completed stage result drift')
                return read(directory/'result.json')
            raise EvidenceError('Partially started stage cannot be replayed')
        if state['cancelled']:raise EvidenceError('Cancelled')
        limit=p['limits'].get(kind,dict(requests=0,seconds=600))
        if kind in p['limits']:
            used=sum(s.get('requests',0) for s in state['stages'])
            if used+limit['requests']>p['total_request_cap']:raise EvidenceError('Request budget exhausted')
        directory.mkdir(parents=True);self.save(directory.relative_to(self.root)/'input.json',payload)
        state['stages'].append(dict(key=key,kind=kind,status='started',reserved_requests=limit['requests']));self.save('state.json',state)
        started=time.monotonic()
        if kind in ('visible','gold'):
            try:result=backend.evaluate(kind,payload,directory)
            except Exception as error:
                result=dict(valid=False,error=repr(error),failure_type='timeout' if isinstance(error,(TimeoutError,subprocess.TimeoutExpired)) else 'infrastructure_error')
        else:result=self._execute_stage(p,backend,key,kind,payload,limit,directory)
        if kind=='gold':
            self.save(directory.relative_to(self.root)/'raw-result.json',result)
            from .training_acceptance import normalize
            result=normalize(result,p.get('training_feedback',{}) if p['mode']=='learning' else {})
        self.save(directory.relative_to(self.root)/'result.json',result)
        state=self.state()
        row=next(s for s in state['stages'] if s['key']==key)
        requests=result.get('requests',0) if kind not in ('visible','gold') else 0
        row.update(tokens=result.get('tokens'),seconds=time.monotonic()-started,result_sha256=sha((directory/'result.json').read_bytes()))
        row.update(observed_tokens=result.get('observed_tokens'),usage_incomplete=result.get('usage_incomplete',False),unknown_usage_requests=result.get('unknown_usage_requests',0))
        if type(requests) is int and requests>=0:row['requests']=requests
        self.save('state.json',state)
        if self.state()['cancelled']:raise EvidenceError('Cancelled during stage')
        if result.get('valid') is not True:
            row['failure_type']=result.get('failure_type','invalid_output');self.save('state.json',state)
            raise EvidenceError('Invalid '+kind+' execution: '+str(result.get('error')))
        if type(requests) is not int or requests<0 or requests>limit['requests']:raise EvidenceError('Invalid measured request count')
        if kind in p['limits'] and result.get('model')!=p['model']:raise EvidenceError('Actual model settings mismatch')
        row['status']='complete';self.save('state.json',state)
        return result

    def _execute_stage(self,p,backend,key,kind,payload,limit,directory):
        from .stage_retry import aggregate
        policy=p['model_settings']['retry_policy'];results=[];started=time.monotonic()
        for index in range(policy['max_retries']+1):
            if self.state()['cancelled']:raise EvidenceError('Cancelled before transport execution')
            used=sum(r['requests'] for r in results)
            remaining=dict(requests=limit['requests']-used,seconds=limit['seconds']-(time.monotonic()-started))
            trial=directory/'executions'/str(index+1);trial.mkdir(parents=True)
            state=self.state();row=next(s for s in state['stages'] if s['key']==key)
            execution=dict(number=index+1,status='started',limits=remaining,input_sha256=sha(canonical(payload).encode()))
            row.setdefault('executions',[]).append(execution);self.save('state.json',state)
            result=backend.execute(kind,deepcopy(payload),p['model'],remaining,trial)
            self.save(trial.relative_to(self.root)/'result.json',result)
            state=self.state();row=next(s for s in state['stages'] if s['key']==key)
            execution=row['executions'][-1];execution.update(status='complete',valid=result.get('valid'),requests=result.get('requests'),
                failure_type=result.get('failure_type'),result_sha256=sha((trial/'result.json').read_bytes()))
            results.append(result);row.update(aggregate(results));self.save('state.json',state)
            requests=result.get('requests')
            if type(requests) is not int or not 0<=requests<=remaining['requests']:
                raise EvidenceError('Invalid measured request count; transport retry prohibited')
            if result.get('model')!=p['model']:raise EvidenceError('Actual model settings mismatch')
            if result.get('valid') is True or result.get('failure_type')!='transient_transport_error':break
            if index==policy['max_retries']:break
            delay=policy['backoff_seconds']*(index+1)
            if sum(r['requests'] for r in results)>=limit['requests'] or time.monotonic()-started+delay>=limit['seconds']:break
            until=time.monotonic()+delay
            while time.monotonic()<until:
                if self.state()['cancelled']:raise EvidenceError('Cancelled during transport backoff')
                time.sleep(min(.1,until-time.monotonic()) if time.monotonic()<until else 0)
            self.verify()  # Recheck frozen bindings before spending another request.
        return dict(result,**aggregate(results),transport_executions=len(results),transport_retries=len(results)-1)

    def run(self, backend, execute=False):
        if not execute:raise EvidenceError('Explicit execution authorization required')
        self.verify()
        with (self.root/'execution.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            return self._run(backend)

    def _run(self,backend):
        p=self.verify();state=self.state()
        if state['status'] in TERMINAL and (state['status']!='passed' or state.get('finalized')):return state
        sources={k:v.decode() for k,v in capture(self.root/'original')[0].items()}
        public=dict(task=p['task'],sources=sources,ast=read(self.root/'ast-evidence.json'))
        try:
            if p['learning_policy']=='online':
                from . import online_memory
                path=self.root/'online-snapshot.json'
                if not path.exists():
                    if self.state()['stages']:raise EvidenceError('Cannot resnapshot a started online trajectory')
                    snapshot=online_memory.capture(Path(p['online_memory']),self.root,p.get('task_id'))
                    self.save('online-snapshot.json',snapshot);self.status(self.state()['status'],online_snapshot_sha256=snapshot['sha256'])
                else:
                    snapshot=online_memory.validate_snapshot(read(path))
                    if self.state().get('online_snapshot_sha256')!=snapshot['sha256']:raise EvidenceError('Unbound online snapshot')
                p=deepcopy(p);p['memory_snapshot']['entries']+=snapshot['entries']
            if not (self.root/'delivery.json').exists() and p['condition'] in ('structured','fixed_contract') and not p.get('routing_analysis'):
                from . import experience_routing as routing
                proposal=self._step(p,backend,'routing','routing',dict(public,schema=taxonomy.analysis_schema(),
                    instruction=routing.analysis_prompt(p['task'],sources,public['ast'])))['output']
                from ._session_runtime.schema_validator import validate
                validate(proposal,taxonomy.analysis_schema())
                p=deepcopy(p);p['routing_analysis']=proposal;self.save('routing-analysis.json',proposal)
            delivery=read(self.root/'delivery.json') if (self.root/'delivery.json').exists() else self.retrieve(p,backend)
            if p['condition']!='baseline' and state['contract'] is None:
                result=self._step(p,backend,'contract','contract',dict(public,experience=delivery['experience_text'],schema=CONTRACT_SCHEMA))
                check_contract(result['output'],p['task'],sources);state=self.state();state['contract']=result['output'];self.save('initial-contract.json',result['output']);self.save('state.json',state)
            self.status('contract_ready');state=self.state()
            for number in range(1,p['max_attempts']+1):
                if state['attempts']:
                    last=state['attempts'][-1]
                    if last['acceptance_passed']:break
                if len(state['attempts'])>=number:
                    state=self.state();continue
                if number>1 and p['condition']!='baseline' and not any(d['attempt']==number for d in state['diagnoses']):
                    before=deepcopy(state['contract']);last=state['attempts'][-1]
                    diagnostic=self._step(p,backend,'diagnosis-'+str(number),'diagnosis',dict(public,
                        contract_before=before,contract_revision_allowed=p['condition']!='fixed_contract',routing_recheck_required=p['condition']=='structured',feedback=last['feedback'],previous_candidate=last['candidate_sources'],
                        instruction='Classify implementation_gap/contract_gap/both/unknown. Preserve original obligations. Observations are not new business requirements. Cite original public sources. Return unchanged contract when sufficient.',schema=DIAGNOSIS_SCHEMA))['output']
                    from ._session_runtime.schema_validator import validate
                    validate(diagnostic,DIAGNOSIS_SCHEMA);evidence_valid(diagnostic['supporting_evidence'],p['task'],sources)
                    after=diagnostic['contract_after'];check_contract(after,p['task'],sources,before)
                    if (diagnostic['diagnosis']=='implementation_gap' or p['condition']=='fixed_contract') and after!=before:
                        raise EvidenceError('Implementation-only/fixed condition cannot change Contract')
                    if after!=before and not diagnostic['structured_delta']:raise EvidenceError('Missing Contract delta')
                    self.save('revisions/'+str(number)+'.json',dict(contract_before=before,**diagnostic))
                    state=self.state();state['contract']=after
                    if not any(d['attempt']==number for d in state['diagnoses']):state['diagnoses'].append(dict(attempt=number,contract_changed=after!=before,**diagnostic))
                    self.save('state.json',state)
                    if after!=before:
                        if p['condition']=='structured' and diagnostic.get('routing_analysis') is None:raise EvidenceError('Changed structured Contract requires source-bound routing recheck')
                        if diagnostic.get('routing_analysis') is not None:
                            from .experience_routing import validate_analysis
                            validate_analysis(diagnostic['routing_analysis'],p['task'],sources,text_grounding=True)
                            routed=deepcopy(p);routed['routing_analysis']=diagnostic['routing_analysis']
                            delivery=self.retrieve(routed,backend,'selection-'+str(number))
                            self.save('revisions/'+str(number)+'-delivery.json',delivery)
                state=self.state();base=self.root/'original' if number==1 else self.root/'attempts'/str(number-1)/'candidate'
                self.status('action_running',current_attempt=number)
                payload=dict(public,contract=state['contract'],experience=delivery['experience_text'],
                    candidate_sources={k:v.decode() for k,v in capture(base)[0].items()},
                    feedback=None if number==1 else state['attempts'][-1]['feedback'],
                    within_task_reflections=[dict(source_attempt=d['attempt']-1,for_action=d['attempt'],
                        observed_feedback=deepcopy(state['attempts'][d['attempt']-2]['feedback']),
                        status='unverified_task_local_reflection',**{k:deepcopy(d[k]) for k in ('diagnosis','explanation','structured_delta','supporting_evidence','remaining_unknowns','contract_changed')})
                        for d in state['diagnoses'] if d['attempt']<=number],
                    instruction='Repair the supplied current candidate. Use cumulative within_task_reflections from the actual preceding failed candidates, including when Contract is unchanged or no cross-task experience matched. Treat their explanations as fallible hypotheses: retain unknowns, check against public task/source and observations, and do not turn inferred causes or checks into new business requirements. Preserve original task obligations and correct behavior. No scorer, reference, gold patch or hidden tests are available.')
                result=self._step(p,backend,'action-'+str(number),'action',payload)
                candidate=result['candidate_sources']
                if not isinstance(candidate,dict) or any(not isinstance(v,str) for v in candidate.values()):raise EvidenceError('Invalid candidate output')
                from .experience_routing import source_inputs
                source_inputs(p['task'],candidate)
                directory=self.root/'attempts'/str(number)/'candidate'
                if not directory.exists():write_files(directory,{k:v.encode() for k,v in candidate.items()})
                elif inventory(capture(directory)[0])!=inventory({k:v.encode() for k,v in candidate.items()}):raise EvidenceError('Candidate drift')
                protected=set(p.get('protected_paths',[])) | {k for k in sources if k.startswith(('tests/','test/')) or Path(k).name in ('package.json','package-lock.json','pyproject.toml','setup.cfg')}
                if any(candidate.get(k)!=sources.get(k) for k in protected):raise EvidenceError('Action changed protected checks/configuration')
                original_diff=''.join(''.join(difflib.unified_diff(sources.get(k,'').splitlines(True),candidate.get(k,'').splitlines(True),fromfile='original/'+k,tofile='candidate/'+k)) for k in sorted(set(sources)|set(candidate)))
                self.save('attempts/'+str(number)+'/diff.json',dict(from_original=original_diff,from_previous=''.join(''.join(difflib.unified_diff(payload['candidate_sources'].get(k,'').splitlines(True),candidate.get(k,'').splitlines(True),fromfile='previous/'+k,tofile='candidate/'+k)) for k in sorted(set(candidate)|set(payload['candidate_sources'])))))
                self.status('evaluation_running')
                if not p.get('visible_evaluator'):
                    evaluation=dict(passed=None,observations=[],regressions=[],unknowns=['No external public behavioral checks were run; candidate correctness is unverified.'])
                else:
                    evaluation=self._step(p,backend,'visible-'+str(number),'visible',dict(candidate=str(directory),evaluator=p['visible_evaluator']))
                if inventory(capture(directory)[0])!=inventory({k:v.encode() for k,v in candidate.items()}):raise EvidenceError('Evaluator mutated candidate')
                if 'passed' not in evaluation or (evaluation['passed'] is not None and type(evaluation['passed']) is not bool):raise EvidenceError('No visible verdict')
                feedback={k:deepcopy(evaluation[k]) for k in p['feedback_fields'] if k in evaluation}
                if set(feedback)!=set(p['feedback_fields']):raise EvidenceError('Visible evaluator must return complete observations/regressions/unknowns')
                learning=p['mode']=='learning'
                evaluator=p['training_evaluator'] if learning else p['gold_evaluator']
                key=('acceptance-' if learning else 'oracle-')+str(number)
                result=self._step(p,backend,key,'gold',dict(candidate=str(directory),evaluator=evaluator,
                    purpose='training_acceptance' if learning else 'testing_acceptance'))
                if inventory(capture(directory)[0])!=inventory({k:v.encode() for k,v in candidate.items()}):raise EvidenceError('Oracle evaluator mutated candidate')
                accepted=result['passed']
                feedback['oracle_acceptance']=deepcopy(result['feedback'])
                if p['mode']=='learning':
                    self.save('training-exposure.json',dict(task_id=p.get('task_id'),source_sha256=p['source_sha256'],training_feedback_used=True,eligible_for_independent_testing=False))
                state=self.state();state['attempts'].append(dict(number=number,visible_passed=evaluation['passed'],
                    delivered_sha256s=delivery.get('selected_sha256s',[]),
                    acceptance_passed=accepted,training_result=result if learning else None,oracle_result=result,
                    feedback=feedback,candidate_sources=candidate,candidate_inventory=inventory(capture(directory)[0])))
                self.save('state.json',state)
                if p['learning_policy']=='online':
                    from .online_memory import usage
                    usage(Path(p['online_memory']),self.root,number,delivery.get('provisional_sha256s',[]),accepted)
                if accepted:break
                self.status('revision_pending');state=self.state()
            state=self.state();last=state['attempts'][-1]
            passed=last['acceptance_passed']
            reason='oracle_accepted' if passed else 'action_budget_exhausted'
            final_status='passed' if passed else 'repair_exhausted'
            self.status(final_status,repair_stop_reason=reason,first_pass_attempt=len(state['attempts']) if passed else None,stop_reason=reason,
                training_accepted=passed if p['mode']=='learning' else None,final_acceptance=last['oracle_result'],gold_result=last['oracle_result'])
            if p['mode']=='learning':
                from . import experience_reflection as reflection
                used=list(dict.fromkeys(delivery.get('selected_sha256s',[])+[code for a in self.state()['attempts'] for code in a.get('delivered_sha256s',[])]))
                related=reflection.related(p,dict(delivery,selected_sha256s=used))
                evidence=dict(public_inputs=public,task_id=p.get('task_id'),source_sha256=p['source_sha256'],
                    diffs=[read(self.root/'attempts'/str(i) /'diff.json') for i in range(1,len(self.state()['attempts'])+1)])
                if passed:
                    learned=self._step(p,backend,'extract','extract',dict(public,related_experiences=related,initial_contract=read(self.root/'initial-contract.json') if p['condition']!='baseline' else None,
                        final_contract=self.state()['contract'],trajectory=[{k:a[k] for k in ('number','visible_passed','acceptance_passed','feedback','candidate_sources','delivered_sha256s')} for a in self.state()['attempts']],delivery=delivery,
                        schema=REFLECTION_SCHEMA,instruction='Reflect against the supplied frozen related experiences before creating guidance. Choose evidence if guidance is unchanged (copy its exact rules and applicability); revise for a source-supported correction or boundary/checkpoint improvement; merge for overlapping complementary guidance (first target is the primary lineage); new only for distinct reusable guidance. Name exact target hashes and actual supporting attempt numbers, explain the delta and distinguish experience_gap from implementation_gap/unknown. Failed implementation alone does not disprove guidance. Extract complete reusable source-supported rules/checks with limitations using schema enums. Passing once does not prove causality or cross-task benefit.'))['output']
                    from ._session_runtime.schema_validator import validate
                    validate(learned,REFLECTION_SCHEMA)
                    update=reflection.plan(learned['experience'],learned['update'],related,len(self.state()['attempts']))
                    self.save('candidate-pool/success.json',dict(status='awaiting_content_review',origin='success',
                        task=p['task'],evidence=evidence,training_accepted=True,final_training_acceptance=self.state()['final_acceptance'],source_sha256=p['source_sha256'],initial_contract=read(self.root/'initial-contract.json') if p['condition']!='baseline' else None,
                        final_contract=self.state()['contract'],trajectory=self.state()['attempts'],experience=learned['experience'],reflection_update=update,related_experiences=related,effectiveness_verified=False))
                    self._enqueue_online(p,'success')
                elif len(state['attempts'])==3 and all(a['acceptance_passed'] is False for a in state['attempts']):
                    self.save('expert-summary-task.json',dict(status='awaiting_expert_summary',task=p['task'],evidence=evidence,
                        initial_contract=read(self.root/'initial-contract.json') if p['condition']!='baseline' else None,final_contract=self.state()['contract'],
                        attempts=self.state()['attempts'],contract_changes=self.state()['diagnoses'],
                        summary=None,expert=None,related_experiences=related,reflection_update_schema=REFLECTION_UPDATE_SCHEMA,effectiveness_verified=False))
                    self.status('awaiting_expert_summary')
        except (Exception,KeyboardInterrupt) as error:
            if self.state()['status']!='cancelled':self.status('execution_invalid',error=repr(error),stop_reason='execution_invalid',training_accepted=self.state().get('training_accepted'))
        if self.state()['status'] in ('passed','awaiting_expert_summary','repair_exhausted'):self.status(self.state()['status'],finalized=True)
        self.report();return self.state()

    def submit_expert(self, summary):
        p=self.verify()
        if p['mode']!='learning' or self.state()['status']!='awaiting_expert_summary':raise EvidenceError('No expert task')
        for key in ('expert','confirmed_conclusions','unverified_hypotheses','unresolved_behaviors','boundaries_counterexamples','suggested_checks','experience'):
            if key not in summary:raise EvidenceError('Missing human summary '+key)
        if not isinstance(summary['expert'],str) or not summary['expert'].strip():raise EvidenceError('Actual expert name required')
        for key in ('confirmed_conclusions','unverified_hypotheses','unresolved_behaviors','boundaries_counterexamples','suggested_checks'):
            if not isinstance(summary[key],list):raise EvidenceError('Expert findings must be lists; unknown findings may be empty')
        if (self.root/'candidate-pool/expert.json').exists():raise EvidenceError('Summary already submitted; edit through immutable memory versions')
        task=read(self.root/'expert-summary-task.json')
        from . import experience_reflection as reflection
        from ._session_runtime.schema_validator import validate
        validate(summary['experience'],EXPERIENCE_SCHEMA)
        update=reflection.plan(summary['experience'],summary.get('reflection_update'),task.get('related_experiences',[]),len(task['attempts']))
        task.update(status='submitted_by_human',summary=summary,expert=summary['expert'])
        self.save('expert-summary-task.json',task)
        self.status('awaiting_content_review')
        self.save('candidate-pool/expert.json',dict(status='awaiting_content_review',origin='expert_failure',summary=task,
            experience=summary['experience'],reflection_update=update,related_experiences=task.get('related_experiences',[]),effectiveness_verified=False))
        self._enqueue_online(p,'expert')
        return task

    def _enqueue_online(self,p,name):
        if p.get('learning_policy')!='online':return
        from .online_memory import append
        record=read(self.root/'candidate-pool'/(name+'.json'))
        result=append(Path(p['online_memory']),self.root,p.get('task_id'),record)
        self.save('candidate-pool/'+name+'-online.json',result)

    def publish_candidate(self, name):
        """Materialize an immutable unapproved record for the existing human review UI."""
        p=self.verify()
        if p['mode']!='learning':raise EvidenceError('Testing cannot write experience')
        if name not in ('success','expert'):raise EvidenceError('Unknown candidate kind')
        path=self.root/'candidate-pool'/(name+'.json');record=read(path)
        if record.get('published_sha256') or record.get('published_proposal_sha256'):return record.get('published_sha256') or record['published_proposal_sha256']
        if name=='success' and (self.state().get('training_accepted') is not True or record.get('training_accepted') is not True):raise EvidenceError('Success experience requires training acceptance')
        from . import experience_reflection as reflection
        update=record['reflection_update'];experience=record['experience']
        from . import compact_experience as compact
        if compact.is_library(p['store']):
            receipt=compact.publish_candidate(p['store'],record)
            record.update(receipt);self.save(path.relative_to(self.root),record)
            return receipt.get('published_sha256') or receipt['published_proposal_sha256']
        if update['operation']=='evidence':
            code=reflection.publish_evidence(p['store'],record)
            record.update(published_proposal_sha256=code,publication_kind='evidence_proposal');self.save(path.relative_to(self.root),record)
            return code
        source=self.root/'candidate-pool'/(name+'-evidence.json')
        stable_record={k:v for k,v in record.items() if k not in ('published_sha256','published_proposal_sha256','publication_kind')}
        self.save(source.relative_to(self.root),stable_record);code=sha(source.read_bytes())
        rules=[dict(id='R%02d'%i,**rule) for i,rule in enumerate(experience['rules'],1)]
        parent=next((b for b in record['related_experiences'] if b['sha256']==next(iter(update['target_sha256s']),None)),None)
        if parent and not any(b['sha256']==parent['sha256'] for b in memory.records(p['store'])):parent=None
        payload=dict(schema_version=memory.BUNDLE_VERSION_V2,id=parent['id'] if parent else 'v8-'+sha(str(self.root).encode())[:16]+'-'+name,version='reflection-'+code[:16],parent_sha256=parent['sha256'] if parent else None,
            taxonomy_version=__import__('temporal_contract_analyzer.taxonomy',fromlist=['VERSION']).VERSION,
            labels=experience['labels'],requires=experience['requires'],excludes=experience['excludes'],rules=rules,
            review=dict(status='candidate',kind='human' if name=='expert' else 'ai_assisted',source_sha256=code,limitations=experience.get('limitations',[])),
            audit=dict(sources=[dict(path=str(source),sha256=code)],rule_links=[dict(rule_id=r['id'],source_sha256=code,pointer='/experience/rules/'+str(i)) for i,r in enumerate(rules)],notes=['V8 origin: '+record['origin'],'Reflection operation: '+update['operation'],'Reflection targets: '+','.join(update['target_sha256s']),'Not approved; training acceptance or expert summary does not verify cross-task effectiveness'],outcome_refs=[]))
        with (Path(p['store'])/'decision.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            expected=memory.seal(payload)
            existing=next((b for b in memory.records(p['store']) if b['id']==payload['id'] and b['version']==payload['version']),None)
            if existing is not None and existing!=expected:raise EvidenceError('Existing staged version differs; use immutable editing')
            bundle=existing or memory.add(p['store'],payload,[source])
        record.update(published_sha256=bundle['sha256'],publication_kind='experience_version');self.save(path.relative_to(self.root),record)
        return bundle['sha256']

    def report(self):
        state=self.state();attempts=state['attempts'];p=read(self.root/'protocol.json')
        if p.get('schema_version')!=VERSION or p.get('acceptance_policy')!='oracle_pass_or_action_budget_exhausted':return read(self.root/'summary.json')
        for row in state['stages']:
            path=self.root/'stages'/row['key']/'result.json'
            if path.exists() and 'requests' not in row:
                result=read(path);row['measured_requests']=result.get('requests');row['measured_tokens']=result.get('tokens')
        result=dict(protocol=p['schema_version'],evaluation_split=p.get('evaluation_split'),learning_policy=p['learning_policy'],online_snapshot_sha256=state.get('online_snapshot_sha256'),model=p['model'],model_profile=p['model_profile'],mode=p['mode'],condition=p['condition'],status=state['status'],
            reflection_updates=[dict(name=name,update=read(self.root/'candidate-pool'/(name+'.json')).get('reflection_update'),
                publication_kind=read(self.root/'candidate-pool'/(name+'.json')).get('publication_kind')) for name in ('success','expert') if (self.root/'candidate-pool'/(name+'.json')).exists()],
            transport_executions=sum(len(s.get('executions',[])) for s in state['stages']),
            transport_retries=sum(max(len(s.get('executions',[]))-1,0) for s in state['stages']),
            known_tokens=sum((s.get('observed_tokens') or s.get('tokens') or {}).get('total_tokens') or 0 for s in state['stages']),
            unknown_usage_requests=None if any(s.get('unknown_usage_requests',0) is None for s in state['stages']) else sum(s.get('unknown_usage_requests',0) for s in state['stages']),
            usage_incomplete=any(s.get('usage_incomplete',False) for s in state['stages']),
            cumulative_visible_pass=[visible_verdict(attempts[:n]) if len(attempts)>=n or visible_verdict(attempts) is True else None for n in (1,2,3)],
            unstarted_actions=p['max_attempts']-sum(s['kind']=='action' for s in state['stages']),
            missing_action_evaluations=sum(s['kind']=='action' for s in state['stages'])-len(attempts),
            attempt_results=[dict(number=a['number'],visible_passed=a['visible_passed'],acceptance_passed=a.get('acceptance_passed'),feedback=a['feedback'],candidate_inventory=a['candidate_inventory']) for a in attempts],
            first_visible_pass_attempt=next((a['number'] for a in attempts if a['visible_passed']),None),
            first_training_acceptance_attempt=next((a['number'] for a in attempts if a.get('acceptance_passed')),None) if p['mode']=='learning' else None,
            first_oracle_pass_attempt=next((a['number'] for a in attempts if a.get('oracle_result') and a['oracle_result']['passed']),None),
            final_visible_passed=attempts[-1]['visible_passed'] if attempts else None,
            first_pass_attempt=state.get('first_pass_attempt'),visible_passed=visible_verdict(attempts),
            training_accepted=state.get('training_accepted'),final_acceptance=state.get('final_acceptance'),stop_reason=state.get('stop_reason'),repair_stop_reason=state.get('repair_stop_reason'),acceptance_policy=p.get('acceptance_policy'),
            per_round_evaluations=[dict(stage=s['key'],result=read(self.root/'stages'/s['key']/'result.json')) for s in state['stages'] if s['kind'] in ('visible','gold') and (self.root/'stages'/s['key']/'result.json').exists()],
            per_attempt_acceptance=[a.get('training_result') for a in attempts],required_visible_checks=p.get('required_visible_checks'),
            per_attempt_oracle=[a.get('oracle_result') for a in attempts],
            held_out_eligible=p.get('held_out_eligible',False),split_status=p.get('split_status','unverified'),
            gold_result=state.get('gold_result'),attempts_started=sum(s['kind']=='action' for s in state['stages']),valid_attempts=len(attempts),
            contract_changes=sum(d['contract_changed'] for d in state['diagnoses']),
            diagnoses=[d['diagnosis'] for d in state['diagnoses']],requests=sum(s['requests'] for s in state['stages'] if type(s.get('requests')) is int),
            unknown_request_stages=[s['key'] for s in state['stages'] if s['kind'] in LIMITS and type(s.get('requests')) is not int],
            cumulative_action_request_cap=p['limits']['action']['requests']*p['max_attempts'],
            stages=state['stages'],delivery=read(self.root/'delivery.json') if (self.root/'delivery.json').exists() else None,
            candidate_learning_enabled=p['mode']=='learning',error=state.get('error'))
        self.save('summary.json',result);return result
