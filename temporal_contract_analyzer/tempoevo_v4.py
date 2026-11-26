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
from . import preparation_validation as preparation
from .stage_retry import restart_counts

VERSION = 'tempoevo-trajectory-v13'
ACCEPTANCE_POLICIES = dict(learning='oracle_pass_or_action_budget_exhausted',
                           testing='single_submission_then_independent_gold')
MODEL = identity(resolve_profile())
CONDITIONS = ('baseline', 'contract', 'structured', 'fixed_contract', 'latent_experience')
LIMITS = dict(selection=dict(requests=12, seconds=600), contract=dict(requests=12, seconds=600), action=dict(requests=24, seconds=600),
              diagnosis=dict(requests=12, seconds=600), extract=dict(requests=12, seconds=600))
TERMINAL = ('passed', 'scored', 'repair_exhausted', 'execution_invalid', 'awaiting_expert_summary', 'awaiting_content_review', 'cancelled')
CONTRACT_FIELDS = ('scope', 'triggers', 'ordering_barriers', 'lifecycle_identity',
                   'preservation', 'forbidden_effects', 'checkpoints', 'unknowns')
BEHAVIOR_FIELDS = tuple(k for k in CONTRACT_FIELDS if k != 'unknowns') + ('obligations',)
CONTRACT_INSTRUCTION = (
    'Infer a concise temporal Contract from the original task and public sources. '
    'First identify the requested behavioral change; then identify preservation obligations at operations '
    'that this change can affect, including callback-capable boundaries. Do not preserve a behavior the task '
    'explicitly asks to change, or assume every existing behavior is correct. '
    'In each obligation text distinguish explicit task requirements from inferred preservation. '
    'Describe the applicable trigger and concrete observable outcome, using current source operation/object names. '
    'For an inferred obligation, briefly explain why the cited original behavior must survive this change. '
    'For every required ordering, identify the observable effect that depends on it; do not invent a universal '
    'flush-before-retirement or cancel-drops-work policy. Distinguish accepting new work, completing already '
    'accepted work, and publishing results to a current owner whenever relevant to this task. '
    'Support each obligation with short exact original task/source quotes in supporting_evidence; '
    'identify its supporting file and quote in the obligation text without repeating the full quote. '
    'A quotation being present does not establish that it entails the proposed rule. Check the entailment, '
    'including any proposed business obligations. Use experience to find boundaries to inspect, never as '
    'normative evidence or as a repair policy to copy. Absence of a prose deadline does not authorize '
    'weakening observable behavior when preservation is requested. '
    'Put unsupported policies, ambiguous preservation inferences and task/source conflicts in unknowns '
    'rather than mandatory obligations. Do not invent certainty or requirements to fill fields. '
    'Use obligations as the primary behavior description. Other fields contain only additional necessary '
    'details or obligation IDs, not paraphrases; use empty arrays when unnecessary. Merge duplicate '
    'obligations, omit generic advice and implementation recipes, and keep checkpoints to brief observable '
    'checks, not full test scenarios. Obey output_budget for the complete serialized JSON; shorten redundant '
    'prose before removing distinct supported obligations. Return the existing schema only.')
DIAGNOSIS_INSTRUCTION = '''Classify implementation_gap/contract_gap/both/unknown. Preserve original obligations.
Observations and a failed acceptance verdict are not new business requirements or proof of a failure cause.
Compare behavioral fields (scope, triggers, ordering_barriers, lifecycle_identity, preservation,
forbidden_effects, checkpoints, obligations) separately from supporting_evidence and unknowns.
Evidence formatting and unknown updates alone are not behavioral Contract changes and need no delta.
For implementation_gap or when contract_revision_allowed is false, keep behavioral fields unchanged.
For a real behavioral revision, return a nonempty structured_delta grounded only in
the original task/sources. Experience applicability will be rechecked separately.
Do not generate taxonomy routing analysis or infer requirements from experience.
contract_after.supporting_evidence must cite original task/sources. Diagnostic supporting_evidence may
also cite the supplied previous_candidate: use file PREVIOUS_CANDIDATE:<relative path> for those quotes.
Unprefixed files denote original sources; TASK denotes the original task. Quote literal public text.
Do not use repaired candidate text as evidence for original business requirements.'''


def read(path):
    return json.loads(Path(path).read_text())


def current_protocol(protocol):
    if protocol.get('training_recipe'):return False
    if protocol.get('preparation_validation_policy')!=preparation.POLICY:return False
    profile='business-source-v1' if protocol.get('condition') in ('structured','fixed_contract','latent_experience') else None
    if protocol.get('retrieval_profile')!=profile:return False
    expected=ACCEPTANCE_POLICIES.get(protocol.get('mode'))
    return (protocol.get('schema_version')==VERSION and protocol.get('mode') in ACCEPTANCE_POLICIES
            and protocol.get('acceptance_policy')==expected
            and (protocol['mode']!='testing' or (protocol.get('max_attempts')==1
                 and protocol.get('contract_review_policy') is None)))


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
CONTRIBUTION_SCHEMA=obj_schema(dict(experience_sha256=STR,rule_id=STR,rule_quote=STR,
    decision=dict(type='string',enum=['adopted','misleading','rule_error']),
    before=obj_schema(dict(file=STR,quote=STR)),after=obj_schema(dict(file=STR,quote=STR)),
    supporting_evidence=EVIDENCE,reason=STR))
REFLECTION_SCHEMA=obj_schema(dict(title=dict(type='string',minLength=1,maxLength=120),
    experience=EXPERIENCE_SCHEMA,update=REFLECTION_UPDATE_SCHEMA,
    abstract=dict(type='string',minLength=1,maxLength=1000),
    contributions=dict(type='array',maxItems=3,items=CONTRIBUTION_SCHEMA)))


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


def validate_diagnosis(diagnostic, before, task, sources, previous_candidate, condition):
    """Validate before committing a revision; retain the source version of each anchor."""
    from ._session_runtime.schema_validator import validate
    validate(diagnostic, DIAGNOSIS_SCHEMA)
    bindings = []
    for row in diagnostic['supporting_evidence']:
        prefix = 'PREVIOUS_CANDIDATE:'
        version_correction = {}
        if row['file'].startswith(prefix):
            anchor = dict(row, file=row['file'][len(prefix):])
            if anchor['file'] not in previous_candidate:
                raise EvidenceError('Missing previous-candidate citation file')
            try:
                evidence_valid([anchor], '', previous_candidate)
                matched = ['previous_candidate']
            except EvidenceError:
                # Resolve a mislabeled version only by literal same-file evidence;
                # retain the claimed scope and the correction for the next Action.
                evidence_valid([anchor], task, sources)
                matched = ['original']
                version_correction = dict(claimed_source_version='previous_candidate', source_version_corrected=True)
        else:
            # Older responses used bare paths for the two source maps supplied in the
            # diagnosis payload. Resolve literal matches without promoting them to
            # Contract evidence, and archive the actual matched version(s).
            matched = []
            for name, texts in [('original', sources), ('previous_candidate', previous_candidate)]:
                if name == 'previous_candidate' and row['file'] not in texts:
                    continue
                try:
                    evidence_valid([row], task if name == 'original' else '', texts)
                except EvidenceError:
                    continue
                matched.append(name)
            if not matched:
                raise EvidenceError('Unsupported diagnostic public-source citation')
        bindings.append(dict(file=row['file'], quote=row['quote'], source_versions=matched, **version_correction))
    after = deepcopy(diagnostic['contract_after'])
    changed = any(after[key] != before[key] for key in BEHAVIOR_FIELDS)
    candidate_only = []
    if not changed:
        for anchor in after['supporting_evidence']:
            try:
                evidence_valid([anchor], task, sources)
            except EvidenceError:
                # A diagnostic may describe the edited implementation while keeping
                # every requirement unchanged. Preserve the prior normative evidence
                # instead of treating implementation text as a new requirement.
                if anchor['file'] not in previous_candidate:
                    raise
                evidence_valid([anchor], '', previous_candidate)
                candidate_only.append(dict(**anchor, source_versions=['previous_candidate']))
        if candidate_only:
            after['supporting_evidence'] = deepcopy(before['supporting_evidence'])
    check_contract(after, task, sources, before)
    if changed and (diagnostic['diagnosis'] == 'implementation_gap' or condition == 'fixed_contract'):
        raise EvidenceError('Implementation-only/fixed condition cannot change Contract')
    if changed and not diagnostic['structured_delta']:
        raise EvidenceError('Missing Contract delta')
    return dict(contract_after=after, contract_changed=changed, supporting_evidence_bindings=bindings,
                restored_original_contract_evidence=bool(candidate_only), candidate_only_contract_evidence=candidate_only)


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
        cfg.setdefault('ast_policy','disabled')
        if cfg['ast_policy'] not in ('enabled','disabled'):
            raise EvidenceError('Invalid AST policy')
        cfg.setdefault('contract_output_max_chars',8000)
        if type(cfg['contract_output_max_chars']) is not int or cfg['contract_output_max_chars']<1:
            raise EvidenceError('Invalid Contract output character budget')
        policy=cfg.get('learning_policy','frozen')
        if policy not in ('frozen','online'):raise EvidenceError('Invalid learning policy')
        if policy=='online' and (cfg.get('mode')!='learning' or cfg.get('condition') not in ('structured',) or not cfg.get('online_memory') or not memory.text(cfg.get('task_id'))):raise EvidenceError('Online memory requires memory-enabled learning and an explicit training pool')
        if policy!='online' and cfg.get('online_memory'):raise EvidenceError('Frozen/testing trajectories cannot access an online pool')
        cfg['learning_policy']=policy
        for key in ('task','candidate','store','mode','condition'):
            if key not in cfg:raise EvidenceError('Missing '+key)
        if cfg['mode'] not in ('learning','testing') or cfg['condition'] not in CONDITIONS:raise EvidenceError('Invalid mode/condition')
        if 'frozen_experience_delivery' in cfg:raise EvidenceError('Frozen delivery is derived from validated selection')
        if cfg['condition']=='latent_experience':
            if cfg['mode']!='testing' or policy!='frozen' or 'frozen_selection' not in cfg:
                raise EvidenceError('Latent experience requires frozen testing and an explicit frozen selection')
        elif 'frozen_selection' in cfg:raise EvidenceError('Frozen selection is only supported by latent experience testing')
        if any(key in cfg for key in ('public_checks','repair_policy','testing_policy')):
            raise EvidenceError('Repair strategy switches were removed; testing submits once before independent Gold scoring')
        if cfg.get('training_recipe'):raise EvidenceError('Historical training recipes have been removed')
        uses_experience=cfg['condition'] in ('structured','fixed_contract','latent_experience')
        retrieval_profile=cfg.get('retrieval_profile','business-source-v1' if uses_experience else None)
        if retrieval_profile!=('business-source-v1' if uses_experience else None):
            raise EvidenceError('Only Abstract-based business-source-v1 retrieval is supported; prepare a new trajectory')
        if 'routing_analysis' in cfg:raise EvidenceError('Taxonomy routing was removed from training and testing')
        if cfg.get('preparation_validation_policy',preparation.POLICY)!=preparation.POLICY:raise EvidenceError('Historical validation policy is read-only; prepare a new trajectory')
        cfg['preparation_validation_policy']=preparation.POLICY
        cfg['retrieval_profile']=retrieval_profile
        acceptance=ACCEPTANCE_POLICIES[cfg['mode']]
        if cfg.get('acceptance_policy',acceptance)!=acceptance:
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
        if cfg['mode']=='testing' and cfg.get('evaluation_purpose')!='training_replay':
            registry=Path(__file__).resolve().parents[1]/'experiments/training-cases.json'
            if registry.exists() and cfg.get('task_id') in {r['id'] for r in read(registry)['cases']}:raise EvidenceError('Known exposed development case cannot be an independent test')
        attempts=cfg.get('max_attempts',1 if cfg['mode']=='testing' else 3)
        if type(attempts) is not int or not 1<=attempts<=3:raise EvidenceError('At most three Actions total')
        if cfg['mode']=='testing' and attempts!=1:raise EvidenceError('Testing requires exactly one bounded Action and one final submission')
        if cfg.get('contract_review_policy') is not None:raise EvidenceError('Historical Contract review policy is read-only')
        try:settings=resolve_profile(cfg.get('model_profile'),cfg.get('model_config'))
        except (ValueError,TypeError,OSError) as error:raise EvidenceError('Invalid model configuration: '+str(error)) from error
        if cfg.get('model',identity(settings))!=identity(settings):raise EvidenceError('Model must match the selected profile')
        cfg['model_settings']=settings
        if settings['provider']['wire_api']=='qoder_cli':
            cfg.setdefault('qoder_auth_dir',str(Path(__file__).resolve().parents[1]/'.tempoevo/qoder/account'))
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
        if uses_experience:approval.require_current_abstract_bank(store,bank)
        supplements=cfg.get('approved_memory_supplements',[])
        if not isinstance(supplements,list):raise EvidenceError('Approved memory supplements must be a list')
        if supplements:
            if cfg['mode']!='testing' or policy!='frozen' or cfg['condition']!='structured':raise EvidenceError('Approved supplements require frozen structured testing')
            bank=deepcopy(bank);seen={e['bundle']['sha256'] for e in bank['entries']}
            for supplement in supplements:
                if not isinstance(supplement,dict) or set(supplement)!={'store','snapshot'}:raise EvidenceError('Supplement requires an audited store and exact approved snapshot')
                accepted=approval.validate_snapshot(Path(supplement['store']),supplement['snapshot'])
                approval.require_current_abstract_bank(Path(supplement['store']),accepted)
                if not accepted['entries']:raise EvidenceError('Approved supplement must contain accepted guidance')
                for entry in accepted['entries']:
                    if entry['bundle']['sha256'] in seen:raise EvidenceError('Duplicate approved supplemental experience')
                    seen.add(entry['bundle']['sha256']);bank['entries'].append(deepcopy(entry))
            bank['sha256']=sha(canonical({k:v for k,v in bank.items() if k!='sha256'}).encode())
        if cfg['condition']=='latent_experience':
            from .business_retrieval import replay
            cfg['frozen_experience_delivery']=replay(cfg['frozen_selection'],cfg['task'],sources,[e['bundle'] for e in bank['entries']],summaries={e['bundle']['sha256']:e['retrieval_summary'] for e in bank['entries'] if 'retrieval_summary' in e},learning={e['bundle']['sha256']:e['learning'] for e in bank['entries'] if 'learning' in e},model=identity(settings)['model'])
        from .preanalysis import analyze_candidate
        if cfg.get('ast_policy')=='disabled':
            full,ast=dict(status='disabled',reason='ast_policy_disabled'),{}
        elif cfg.get('backend',{}).get('kind')=='docker':
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
        self.root.mkdir(parents=True);write_files(self.root/'original',files)
        from .compact_experience import is_library,active_view
        if is_library(store):self.save('memory-lifecycle.json',active_view(store))
        self.save('ast-report.json',full);self.save('ast-evidence.json',ast);self.save('memory-snapshot.json',bank)
        limits=cfg.get('limits',LIMITS)
        if set(limits)!=set(LIMITS):raise EvidenceError('Declare every LLM stage limit')
        for role,limit in limits.items():
            if set(limit)!= {'requests','seconds'} or type(limit['requests']) is not int or not 1<=limit['requests']<=LIMITS[role]['requests'] or not 0<limit['seconds']<=600:
                raise EvidenceError('Invalid stage limits')
        uses_contract=cfg['condition'] not in ('baseline','latent_experience')
        total=attempts*limits['action']['requests']+((attempts-1)*limits['diagnosis']['requests']+limits['contract']['requests'] if uses_contract else 0)+(limits['extract']['requests'] if cfg['mode']=='learning' else 0)
        if cfg['condition'] in ('structured','fixed_contract'):
            total+=(attempts if cfg['condition']=='structured' else 1)*limits['selection']['requests']
        if uses_experience:
            from . import business_retrieval
            cfg['retrieval_policy']=dict(version=business_retrieval.VERSION,max_candidates=business_retrieval.MAX_CANDIDATES,max_experiences=business_retrieval.MAX_EXPERIENCES,max_characters=business_retrieval.MAX_CHARACTERS)
        else:
            cfg['retrieval_policy']=dict(version='no-memory',max_experiences=0)
        cfg.update(schema_version=VERSION,model=identity(settings),memory_snapshot=bank,max_attempts=attempts,limits=limits,total_request_cap=total,
            contract_review_policy=None,
            store=str(store),original_inventory=inventory(files),feedback_fields=['observations','regressions','unknowns'],
            required_visible_checks=False,acceptance_policy=acceptance,
            evaluation_budget=dict(visible=attempts if cfg.get('visible_evaluator') else 0,oracle=attempts if cfg['mode']=='learning' else 0,gold=1 if cfg['mode']=='testing' else 0),
            held_out_eligible=False,split_status='final_only_gold_testing' if cfg['mode']=='testing' else 'unverified_no_independent_split_evidence',
            memory_snapshot_sha256=bank['sha256'],source_sha256=sha(canonical(sources).encode()))
        self.save('protocol.json',cfg);self.save('state.json',dict(status='prepared',attempts=[],stages=[],contract=None,diagnoses=[],cancelled=False))
        # Bind task artifacts and trusted scoring inputs, not the shared runner source.
        self.save('binding.json',dict(protocol=sha((self.root/'protocol.json').read_bytes()),
            bank=sha((self.root/'memory-snapshot.json').read_bytes()),ast=sha((self.root/'ast-evidence.json').read_bytes()),
            evaluators=evaluator_hashes))
        self.report();return self.state()

    def verify(self):
        p=read(self.root/'protocol.json')
        if not current_protocol(p):raise EvidenceError('Historical protocol is read-only; prepare a new root under '+VERSION)
        from .evaluation_split import enforce
        enforce(p)
        binding=read(self.root/'binding.json')
        for name,key in [('protocol.json','protocol'),('memory-snapshot.json','bank'),('ast-evidence.json','ast')]:
            if sha((self.root/name).read_bytes())!=binding[key]:raise EvidenceError('Frozen V4 input drift')
        online_digest=self.state().get('online_snapshot_sha256')
        if online_digest:
            from .online_memory import validate_snapshot
            snapshot=validate_snapshot(read(self.root/'online-snapshot.json'))
            if snapshot['sha256']!=online_digest:raise EvidenceError('Online task snapshot changed')
        # Older bindings included the agent executable and Qoder adapter. Those
        # are execution infrastructure, not trusted scoring inputs. Ignore legacy
        # implementation/runtime inventories without rewriting historical records.
        infrastructure={str(Path(p[key]).resolve()) for key in ('binary','node') if p.get(key)}
        infrastructure.add(str(Path(__file__).with_name('qoder_backend.py').resolve()))
        for path,digest in binding['evaluators'].items():
            if str(Path(path).resolve()) in infrastructure:continue
            if sha(Path(path).read_bytes())!=digest:raise EvidenceError('Trusted evaluator input changed')
        if inventory(capture(self.root/'original')[0])!=p['original_inventory']:raise EvidenceError('Original code drift')
        for attempt in self.state()['attempts']:
            if inventory(capture(self.root/'attempts'/str(attempt['number'])/'candidate')[0])!=attempt['candidate_inventory']:raise EvidenceError('Archived candidate drift')
        return p

    def cancel(self):
        if not current_protocol(read(self.root/'protocol.json')):raise EvidenceError('Historical protocol is read-only')
        return self.status('cancelled',cancelled=True,stop_reason='cancelled')

    def retrieve(self,p,backend=None,selection_key='selection-1'):
        bank=p['memory_snapshot'];bundles=[e['bundle'] for e in bank['entries']]
        condition=p['condition'];result=dict(selected_sha256s=[],experience_text=None,reason='condition_has_no_memory')
        if condition=='latent_experience':
            result=deepcopy(p['frozen_experience_delivery'])
        elif condition in ('structured','fixed_contract'):
            from . import business_retrieval as retrieval
            sources={k:v.decode() for k,v in capture(self.root/'original')[0].items()}
            recalled=retrieval.recall(p['task'],sources,bundles,summaries={e['bundle']['sha256']:e['retrieval_summary'] for e in bank['entries'] if 'retrieval_summary' in e},learning={e['bundle']['sha256']:e['learning'] for e in bank['entries'] if 'learning' in e},model=p['model']['model'])
            self.save('retrieval/'+selection_key+'-recall.json',recalled)
            if recalled['candidates']:
                if backend is None:raise EvidenceError('Business delivery requires explicit public-source applicability assessment')
                result=self._preparation_output(p,backend,selection_key,'selection',retrieval.payload(p['task'],sources,read(self.root/'ast-evidence.json'),recalled),
                    lambda output:retrieval.select(output,recalled,p['task'],sources,bundles))
                if result is None:result=dict(selected_sha256s=[],experience_text=None,reason='invalid_business_selection_discarded')
                elif result.get('validation',{}).get('partial'):
                    validation=result['validation']
                    self.save('retrieval/'+selection_key+'-validation.json',validation)
                    self._preparation_warning(selection_key,'business_selection_partial',
                        issue_count=len(validation['issues']),selected_count=len(result['selected_sha256s']),
                        detail_path='retrieval/'+selection_key+'-validation.json')
            else:result=dict(selected_sha256s=[],experience_text=None,reason='empty_approved_bank')
        online={r['bundle']['sha256'] for r in read(self.root/'online-snapshot.json')['entries']} if p.get('learning_policy')=='online' else set()
        result['provisional_sha256s']=[c for c in result.get('selected_sha256s',[]) if c in online]
        if result['provisional_sha256s']:result['experience_text']='TRAINING ONLY: includes unreviewed provisional guidance with unknown effectiveness. Check against public task/source evidence.\n'+result['experience_text']
        self.save('delivery.json',result);return result

    def _step(self,p,backend,key,kind,payload,budget_group=None,limit_cap=None):
        directory=self.root/'stages'/key;state=self.state()
        existing=next((s for s in state['stages'] if s['key']==key),None)
        if existing:
            if existing['status']=='complete':
                if sha((directory/'result.json').read_bytes())!=existing['result_sha256']:raise EvidenceError('Completed stage result drift')
                return read(directory/'result.json')
            raise EvidenceError('Partially started stage cannot be replayed')
        if state['cancelled']:raise EvidenceError('Cancelled')
        limit=self._remaining_limit(p,kind,budget_group or key)
        if limit_cap:
            limit={k:min(v,limit_cap[k]) for k,v in limit.items()}
        if kind in p['limits']:
            if limit['requests']<1 or limit['seconds']<=0:raise EvidenceError('Stage budget exhausted')
            used=sum(s.get('requests',0) for s in state['stages'])
            if used+limit['requests']>p['total_request_cap']:raise EvidenceError('Request budget exhausted')
        directory.mkdir(parents=True);self.save(directory.relative_to(self.root)/'input.json',payload)
        state['stages'].append(dict(key=key,kind=kind,status='started',reserved_requests=limit['requests'],budget_group=budget_group or key));self.save('state.json',state)
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
            if p['mode']=='testing':result.pop('feedback',None)
        self.save(directory.relative_to(self.root)/'result.json',result)
        state=self.state()
        row=next(s for s in state['stages'] if s['key']==key)
        requests=result.get('requests',0) if kind not in ('visible','gold') else 0
        row.update(tokens=result.get('tokens'),seconds=time.monotonic()-started,result_sha256=sha((directory/'result.json').read_bytes()))
        row.update(observed_tokens=result.get('observed_tokens'),usage_incomplete=result.get('usage_incomplete',False),unknown_usage_requests=result.get('unknown_usage_requests',0))
        if result.get('request_measurement'):
            row.update(request_measurement=result['request_measurement'],http_requests=result.get('http_requests'),credits=result.get('credits'))
        if type(requests) is int and requests>=0:row['requests']=requests
        self.save('state.json',state)
        if self.state()['cancelled']:raise EvidenceError('Cancelled during stage')
        if type(requests) is not int or requests<0 or requests>limit['requests']:raise EvidenceError('Invalid measured request count')
        if kind in p['limits'] and result.get('model')!=p['model']:raise EvidenceError('Actual model settings mismatch')
        if result.get('valid') is not True:
            failure=result.get('failure_type') or 'unclassified_execution_error'
            row.update(status='invalid',failure_type=failure);self.save('state.json',state)
            recoverable=failure in ('invalid_output','preparation_output_limit')
            error=preparation.OutputError if kind in preparation.ROLES and recoverable else EvidenceError
            raise error('Invalid '+kind+' execution: '+str(result.get('error')))
        row['status']='complete';self.save('state.json',state)
        return result

    def _remaining_limit(self,p,kind,budget_group=None):
        limit=dict(p['limits'].get(kind,dict(requests=0,seconds=600)))
        if budget_group:
            stages=[s for s in self.state()['stages'] if s.get('budget_group',s['key'])==budget_group]
            limit['requests']-=sum(s.get('requests',0) for s in stages)
            limit['seconds']-=sum(s.get('seconds',0) for s in stages)
        return limit

    def _preparation_warning(self,stage,code,**details):
        state=self.state();entry=dict(stage=stage,code=code,**details)
        warnings=state.setdefault('preparation_warnings',[])
        if entry not in warnings:warnings.append(entry)
        self.save('state.json',state)

    def _preparation_output(self,p,backend,key,kind,payload,validator):
        """One correction in the original stage budget, then discard invalid guidance.

        Output/semantic validation and Qoder preparation output limits are recoverable.
        Other execution, authorization,
        measured usage, model identity, protected inputs and evaluator failures
        propagate unchanged through _step.
        """
        error=None;output=None
        raw_output=None
        qoder=p['model_settings']['provider'].get('wire_api')=='qoder_cli' and kind in ('selection','contract')
        for number in (1,2):
            current=key if number==1 else key+'-validation-correction'
            prior=next((s for s in self.state()['stages'] if s['key']==current),None)
            limit=self._remaining_limit(p,kind,key)
            if prior is None and (limit['requests']<1 or limit['seconds']<=0):
                self._preparation_warning(key,'preparation_budget_exhausted',error=error)
                break
            candidate=deepcopy(payload)
            cap=None
            if qoder and number==1:
                # Reserve correction capacity without increasing the group budget.
                cap=dict(requests=max(1,limit['requests']-3),seconds=max(1,limit['seconds']-120))
            if number==2:
                candidate['validation_feedback']=dict(error=error,previous_output=output,
                    instruction='This is the single validation correction within the original stage budget. Correct the reported output using only original public task/source evidence already supplied. Do not restart analysis or reread files; repair the JSON or the reported evidence issue directly. Do not edit code, invent citations, consult a scorer, or add requirements from feedback. Mark unsupported premises unknown. Return only one JSON object in the original requested schema, without prose or fences.')
                if raw_output is not None:candidate['validation_feedback']['previous_response']=raw_output
            try:
                if prior and prior['status']=='invalid' and prior.get('failure_type') in ('invalid_output','preparation_output_limit'):
                    path=self.root/'stages'/current/'result.json'
                    if sha(path.read_bytes())!=prior['result_sha256']:raise EvidenceError('Archived preparation result drift')
                    raise preparation.OutputError(str(read(path).get('error')))
                result=self._step(p,backend,current,kind,candidate,budget_group=key,limit_cap=cap)
            except preparation.OutputError as exception:
                error=str(exception);output=None
                answers=sorted((self.root/'stages'/current/'executions').glob('*/raw-answer.txt'))
                if answers:raw_output=answers[-1].read_text()
            else:
                output=result.get('output')
                try:
                    checked=validator(output)
                except (EvidenceError,ValueError) as exception:
                    error=str(exception)
                else:
                    self.save('validation/'+current+'.json',dict(accepted=True,correction=number==2))
                    return checked
            self.save('validation/'+current+'.json',dict(accepted=False,error=error,correction=number==2))
            self._preparation_warning(key,'invalid_preparation_output',attempt=number,error=error)
        self._preparation_warning(key,'guidance_discarded',error=error)
        return None

    def _execute_stage(self,p,backend,key,kind,payload,limit,directory):
        from .stage_retry import aggregate, contract_write_denial, restart_counts
        policy=p['model_settings']['retry_policy'];results=[];started=time.monotonic()
        stage_payload=deepcopy(payload);restart_reason='initial'
        for index in range(policy['max_retries']+2):
            if self.state()['cancelled']:raise EvidenceError('Cancelled before transport execution')
            used=sum(r['requests'] for r in results)
            remaining=dict(requests=limit['requests']-used,seconds=limit['seconds']-(time.monotonic()-started))
            trial=directory/'executions'/str(index+1);trial.mkdir(parents=True)
            state=self.state();row=next(s for s in state['stages'] if s['key']==key)
            execution=dict(number=index+1,status='started',limits=remaining,restart_reason=restart_reason,input_sha256=sha(canonical(stage_payload).encode()))
            row.setdefault('executions',[]).append(execution);row.update(restart_counts(row));self.save('state.json',state)
            self.save(trial.relative_to(self.root)/'input.json',stage_payload)
            result=backend.execute(kind,deepcopy(stage_payload),p['model'],remaining,trial)
            self.save(trial.relative_to(self.root)/'result.json',result)
            state=self.state();row=next(s for s in state['stages'] if s['key']==key)
            execution=row['executions'][-1];execution.update(status='complete',valid=result.get('valid'),requests=result.get('requests'),
                failure_type=result.get('failure_type'),result_sha256=sha((trial/'result.json').read_bytes()))
            results.append(result);row.update(aggregate(results));self.save('state.json',state)
            requests=result.get('requests')
            if type(requests) is not int or not 0<=requests<=remaining['requests']:
                raise EvidenceError('Invalid measured request count; transport retry prohibited')
            if result.get('model')!=p['model']:raise EvidenceError('Actual model settings mismatch')
            if result.get('valid') is True:break
            counts=restart_counts(row)
            if counts['tool_policy_recoveries']==0 and contract_write_denial(result,kind,payload.get('sources',{})):
                restart_reason='contract_write_recovery';delay=0
                stage_payload=deepcopy(payload)
                stage_payload['tool_policy_feedback']=dict(reason='A patch to a public workspace file was blocked in the read-only Contract stage.',
                    instruction='This is your single correction opportunity. Do not call apply_patch or change files. Return only the requested structured Contract. Describe intended fixes as obligations or unknowns; the later Action performs code edits. The blocked patch was not applied.')
            elif result.get('failure_type')=='transient_transport_error' and counts['transport_retries']<policy['max_retries']:
                restart_reason='transient_transport';delay=policy['backoff_seconds']*(counts['transport_retries']+1)
            else:break
            if sum(r['requests'] for r in results)>=limit['requests'] or time.monotonic()-started+delay>=limit['seconds']:break
            until=time.monotonic()+delay
            while time.monotonic()<until:
                if self.state()['cancelled']:raise EvidenceError('Cancelled during transport backoff')
                time.sleep(min(.1,until-time.monotonic()) if time.monotonic()<until else 0)
            self.verify()  # Recheck frozen bindings before spending another request.
        return dict(result,**aggregate(results),transport_executions=len(results),**restart_counts(row))

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
                # Proposals remain available for review, not automatic retrieval.
                # Only the prepared reviewed-Abstract bank can guide this task.
            delivery=read(self.root/'delivery.json') if (self.root/'delivery.json').exists() else self.retrieve(p,backend)
            if p['condition'] not in ('baseline','latent_experience') and state['contract'] is None and not state.get('contract_preparation_complete'):
                def validate_draft(output):
                    check_contract(output,p['task'],sources)
                    cap=p.get('contract_output_max_chars')
                    if cap is not None and len(canonical(output))>cap:
                        raise EvidenceError('Contract exceeds output budget of '+str(cap)+' serialized JSON characters; compress duplication without inventing or dropping supported requirements')
                    return deepcopy(output)
                draft=self._preparation_output(p,backend,'contract','contract',dict(public,experience=delivery['experience_text'],business_obligations=delivery.get('business_obligations',[]),instruction=CONTRACT_INSTRUCTION,output_budget=dict(max_serialized_json_characters=p.get('contract_output_max_chars'),unit='characters in canonical JSON, not tokens'),schema=CONTRACT_SCHEMA),validate_draft)
                state=self.state();state.update(contract=draft,contract_preparation_complete=True)
                self.save('initial-contract.json',draft);self.save('state.json',state)
            self.status('contract_ready');state=self.state()
            for number in range(1,p['max_attempts']+1):
                if state['attempts']:
                    last=state['attempts'][-1]
                    if last['acceptance_passed']:break
                if len(state['attempts'])>=number:
                    state=self.state();continue
                if number>1 and p['condition']!='baseline' and not any(d['attempt']==number for d in state['diagnoses']):
                    before=deepcopy(state['contract']);last=state['attempts'][-1]
                    def validate_diagnostic(output):
                        from ._session_runtime.schema_validator import validate
                        validate(output,DIAGNOSIS_SCHEMA);proposal=deepcopy(output)
                        return proposal,validate_diagnosis(proposal,before,p['task'],sources,last['candidate_sources'],p['condition'])
                    validated=None
                    if before is not None:
                        validated=self._preparation_output(p,backend,'diagnosis-'+str(number),'diagnosis',dict(public,
                            contract_before=before,contract_revision_allowed=p['condition']!='fixed_contract',feedback=last['feedback'],previous_candidate=last['candidate_sources'],
                            instruction=DIAGNOSIS_INSTRUCTION,schema=DIAGNOSIS_SCHEMA),validate_diagnostic)
                    else:self._preparation_warning('diagnosis-'+str(number),'diagnosis_skipped_without_contract')
                    if validated is None:
                        diagnostic=dict(diagnosis='unknown',contract_after=before,structured_delta=[],
                            supporting_evidence=deepcopy(before['supporting_evidence']) if before else [],
                            remaining_unknowns=['No accepted diagnostic revision.'],explanation='No validated diagnostic revision is available; preserve the previous draft and use original task/source evidence.')
                        checked=dict(contract_after=before,contract_changed=False,supporting_evidence_bindings=[],diagnostic_fallback=True)
                    else:diagnostic,checked=validated
                    after=checked.pop('contract_after')
                    diagnostic=dict(diagnostic,contract_after=after)
                    if checked['contract_changed'] and p['condition']=='structured':
                        delivery=self.retrieve(p,backend,'selection-'+str(number))
                        self.save('revisions/'+str(number)+'-delivery.json',delivery)
                    self.save('revisions/'+str(number)+'.json',dict(contract_before=before,**diagnostic,**checked))
                    state=self.state();state['contract']=after
                    if not any(d['attempt']==number for d in state['diagnoses']):state['diagnoses'].append(dict(attempt=number,**diagnostic,**checked))
                    self.save('state.json',state)
                state=self.state();base=self.root/'original' if number==1 else self.root/'attempts'/str(number-1)/'candidate'
                self.status('action_running',current_attempt=number)
                payload=dict(public,contract=state['contract'],experience=delivery['experience_text'],
                    candidate_sources={k:v.decode() for k,v in capture(base)[0].items()},
                    feedback=None if number==1 else state['attempts'][-1]['feedback'],
                    within_task_reflections=[dict(source_attempt=d['attempt']-1,for_action=d['attempt'],
                        observed_feedback=deepcopy(state['attempts'][d['attempt']-2]['feedback']),
                        supporting_evidence_bindings=deepcopy(d.get('supporting_evidence_bindings',[])),
                        status='unverified_task_local_reflection',**{k:deepcopy(d[k]) for k in ('diagnosis','explanation','structured_delta','supporting_evidence','remaining_unknowns','contract_changed')})
                        for d in state['diagnoses'] if d['attempt']<=number],
                    instruction='Repair the supplied current candidate. Use cumulative within_task_reflections from the actual preceding failed candidates, including when Contract is unchanged or no cross-task experience matched. Treat their explanations as fallible hypotheses: retain unknowns, check against public task/source and observations, and do not turn inferred causes or checks into new business requirements. Preserve original task obligations and correct behavior. No scorer, reference, gold patch or hidden tests are available.')
                payload['preparation_warnings']=deepcopy(state.get('preparation_warnings',[]))
                payload['instruction']+=' The automatic Contract and preparation checks are unverified guidance. Original task and public source establish requirements. If Contract is null or preparation warnings remain, investigate from those original inputs; do not infer new requirements from rejected guidance or unknown premises.'
                if p['mode']=='testing':
                    payload['instruction']+=' This is the only testing Action. You may run available public project tests and revise code within this session budget. Submit one final candidate; no Gold verdict or later repair Action will be available.'
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
                result=None;accepted=None
                if learning:
                    result=self._step(p,backend,'acceptance-'+str(number),'gold',dict(candidate=str(directory),
                        evaluator=p['training_evaluator'],purpose='training_acceptance'))
                    if inventory(capture(directory)[0])!=inventory({k:v.encode() for k,v in candidate.items()}):raise EvidenceError('Oracle evaluator mutated candidate')
                    accepted=result['passed'] and (evaluation['passed'] is True or not p['required_visible_checks'])
                    feedback['oracle_acceptance']=deepcopy(result['feedback'])
                    self.save('training-exposure.json',dict(task_id=p.get('task_id'),source_sha256=p['source_sha256'],training_feedback_used=True,eligible_for_independent_testing=False))
                state=self.state();state['attempts'].append(dict(number=number,visible_passed=evaluation['passed'],
                    delivered_sha256s=delivery.get('selected_sha256s',[]),
                    acceptance_passed=accepted,training_result=result if learning else None,oracle_result=result,
                    feedback=feedback,candidate_sources=candidate,candidate_inventory=inventory(capture(directory)[0])))
                self.save('state.json',state)
                if not learning:break
                if p['learning_policy']=='online':
                    from .online_memory import usage
                    usage(Path(p['online_memory']),self.root,number,delivery.get('provisional_sha256s',[]),accepted)
                if accepted:break
                self.status('revision_pending');state=self.state()
            state=self.state();last=state['attempts'][-1]
            passed=last['acceptance_passed']
            if p['mode']=='testing':
                self.status('submitted',repair_stop_reason='single_submission',stop_reason='single_submission')
                directory=self.root/'attempts'/str(last['number'])/'candidate'
                result=self._step(p,backend,'final-gold','gold',dict(candidate=str(directory),
                    evaluator=p['gold_evaluator'],purpose='final_scoring'))
                if inventory(capture(directory)[0])!=last['candidate_inventory']:raise EvidenceError('Gold evaluator mutated submitted candidate')
                self.status('scored',gold_result=result)
            else:
                reason='oracle_accepted' if passed else 'action_budget_exhausted'
                final_status='passed' if passed else 'repair_exhausted'
                self.status(final_status,repair_stop_reason=reason,first_pass_attempt=len(state['attempts']) if passed else None,stop_reason=reason,
                    training_accepted=passed,final_acceptance=last['oracle_result'],gold_result=last['oracle_result'])
            if p['mode']=='learning':
                from . import experience_reflection as reflection
                used=list(dict.fromkeys(delivery.get('selected_sha256s',[])+[code for a in self.state()['attempts'] for code in a.get('delivered_sha256s',[])]))
                related=reflection.related(p,dict(delivery,selected_sha256s=used))
                evidence=dict(public_inputs=public,task_id=p.get('task_id'),source_sha256=p['source_sha256'],
                    diffs=[read(self.root/'attempts'/str(i) /'diff.json') for i in range(1,len(self.state()['attempts'])+1)])
                failed_attempts={a['number'] for a in state['attempts'][:-1] if a['acceptance_passed'] is False and
                    (a['visible_passed'] is False or (a.get('oracle_result') or {}).get('passed') is False)}
                if passed and failed_attempts:
                    try:
                        learned=self._step(p,backend,'extract','extract',dict(task=p['task'],sources=sources,
                            related_experiences=related,
                            initial_contract=read(self.root/'initial-contract.json') if p['condition']!='baseline' else None,
                            final_contract=self.state()['contract'],
                            trajectory=[dict(number=a['number'],visible_passed=a['visible_passed'],acceptance_passed=a['acceptance_passed'],
                                feedback=a['feedback'],delivered_sha256s=a['delivered_sha256s'],
                                diff=evidence['diffs'][i]['from_previous']) for i,a in enumerate(state['attempts'])],
                            schema=REFLECTION_SCHEMA,instruction='Compare the failed and successful changes, using the original task/source and the supplied related guidance only. '
                            'Extract only a reusable correction, not routine syntax/import/path fixes. Classify implementation-only work as implementation_gap. '
                            'Prefer evidence or an in-place revision over new entries; merge only explicitly overlapping guidance. '
                            'Use actual failed AND successful supporting_attempts. Preserve still-applicable obligations and distinguish unknown causes. '
                            'Write a concise English title naming the reusable action and its key boundary, not an applicability sentence or a truncated excerpt. '
                            'Write a concise English abstract within 1000 characters, covering applicability, recommendation, preservation and exclusions. '
                            'Retain material conditions, negations, operation order and exceptions; do not turn conditional settlement into a universal deadline. Omit historical outcomes and repeated context. '
                            'For each contribution, quote an exact delivered rule, before code from any failed attempt and after code retained in the final successful attempt, plus original TASK/source evidence. For pure additions or deletions, include adjacent context on the unchanged side of the same edit. '
                            'Use adopted only for an observable implementation of the rule, misleading only for a specifically evidenced harmful recommendation, '
                            'and rule_error only when the rule itself or its applicability is demonstrably wrong. Do not score all delivered guidance for the overall verdict. '
                            'Omit uncertain contributions; no contribution is preferable to a fabricated attribution. Passing does not prove causal benefit.'))['output']
                        from ._session_runtime.schema_validator import validate
                        validate(learned,REFLECTION_SCHEMA)
                        from . import experience_learning as learning
                        judgments,issues=learning.contributions(learned['contributions'],related,state['attempts'],p['task'],sources)
                        self.status(self.state()['status'],contributions=learned['contributions'],contribution_decisions=judgments,contribution_issues=issues)
                        update=reflection.plan(learned['experience'],learned['update'],related,len(state['attempts']))
                        if update['failure_attribution']=='implementation_gap':
                            self.status(self.state()['status'],extraction_disposition='implementation_only')
                        else:
                            supporting=set(update['supporting_attempts'])
                            if state['attempts'][-1]['number'] not in supporting or not supporting.intersection(failed_attempts):
                                raise EvidenceError('Reusable experience needs failed and successful attempt evidence')
                            origin=dict(reflection_model=p['model']['model'],reflection_effort=p['model']['reasoning_effort'],
                                repair_model=p['model']['model'],first_success_attempt=len(state['attempts']))
                            metadata=learning.empty(origin,1 if update['failure_attribution']=='experience_gap' else 0)
                            self.save('candidate-pool/success.json',dict(status='awaiting_content_review',origin='success',
                                task=p['task'],evidence=evidence,training_accepted=True,final_training_acceptance=self.state()['final_acceptance'],
                                source_sha256=p['source_sha256'],initial_contract=read(self.root/'initial-contract.json') if p['condition']!='baseline' else None,
                                final_contract=self.state()['contract'],trajectory=state['attempts'],title=learned['title'],experience=learned['experience'],abstract=learned['abstract'],
                                learning=metadata,reflection_update=update,related_experiences=related,effectiveness_verified=False))
                            self._enqueue_online(p,'success')
                    except Exception as error:
                        if self.state()['cancelled']:raise
                        self.status(self.state()['status'],extraction_disposition='failed',extraction_error=repr(error),contribution_decisions={})
                elif passed:
                    self.status(self.state()['status'],extraction_disposition='first_pass_skipped' if len(state['attempts'])==1 else 'no_confirmed_failure')
                elif len(state['attempts'])==3 and all(a['acceptance_passed'] is False for a in state['attempts']):
                    self.save('expert-summary-task.json',dict(status='awaiting_expert_summary',task=p['task'],evidence=evidence,
                        initial_contract=read(self.root/'initial-contract.json') if p['condition']!='baseline' else None,final_contract=self.state()['contract'],
                        attempts=self.state()['attempts'],contract_changes=self.state()['diagnoses'],
                        summary=None,expert=None,related_experiences=related,reflection_update_schema=REFLECTION_UPDATE_SCHEMA,effectiveness_verified=False))
                    self.status('awaiting_expert_summary')
                try:self._record_learning_usage(p)
                except Exception as error:
                    if self.state()['cancelled']:raise
                    self.status(self.state()['status'],learning_error=repr(error))
        except (Exception,KeyboardInterrupt) as error:
            if self.state()['status']!='cancelled':self.status('execution_invalid',error=repr(error),stop_reason='execution_invalid',training_accepted=self.state().get('training_accepted'))
        if self.state()['status'] in ('passed','scored','awaiting_expert_summary','repair_exhausted'):self.status(self.state()['status'],finalized=True)
        self.report();return self.state()

    def _record_learning_usage(self,p):
        from .experience_learning import record_usage
        used={code for a in self.state()['attempts'] for code in a['delivered_sha256s']}
        expected={e['bundle']['id']:e['bundle']['sha256'] for e in p['memory_snapshot']['entries'] if e['bundle']['sha256'] in used}
        case_id=p.get('task_id') or (p.get('case') or {}).get('id') or p['source_sha256']
        changed=record_usage(p['store'],str(case_id),p['model']['model'],expected,self.state().get('contribution_decisions',{}))
        self.status(self.state()['status'],learning_updates=changed)

    def submit_expert(self, summary):
        p=self.verify()
        if p['mode']!='learning' or self.state()['status']!='awaiting_expert_summary':raise EvidenceError('No expert task')
        for key in ('expert','confirmed_conclusions','unverified_hypotheses','unresolved_behaviors','boundaries_counterexamples','suggested_checks','experience'):
            if key not in summary:raise EvidenceError('Missing human summary '+key)
        if not isinstance(summary['expert'],str) or not summary['expert'].strip():raise EvidenceError('Actual expert name required')
        for key in ('confirmed_conclusions','unverified_hypotheses','unresolved_behaviors','boundaries_counterexamples','suggested_checks'):
            if not isinstance(summary[key],list):raise EvidenceError('Expert findings must be lists; unknown findings may be empty')
        if (self.root/'candidate-pool/expert.json').exists():raise EvidenceError('Expert summary already submitted for this trajectory')
        task=read(self.root/'expert-summary-task.json')
        from . import experience_reflection as reflection
        from ._session_runtime.schema_validator import validate
        validate(summary['experience'],EXPERIENCE_SCHEMA)
        update=reflection.plan(summary['experience'],summary.get('reflection_update'),task.get('related_experiences',[]),len(task['attempts']))
        task.update(status='submitted_by_human',summary=summary,expert=summary['expert'])
        self.save('expert-summary-task.json',task)
        self.status('awaiting_content_review')
        self.save('candidate-pool/expert.json',dict(status='awaiting_content_review',origin='expert_failure',summary=task,
            title=summary.get('title'),experience=summary['experience'],reflection_update=update,related_experiences=task.get('related_experiences',[]),effectiveness_verified=False))
        self._enqueue_online(p,'expert')
        return task

    def _enqueue_online(self,p,name):
        if p.get('learning_policy')!='online':return
        from .online_memory import append
        record=read(self.root/'candidate-pool'/(name+'.json'))
        result=append(Path(p['online_memory']),self.root,p.get('task_id'),record)
        self.save('candidate-pool/'+name+'-online.json',result)

    def publish_candidate(self, name):
        """Publish pending guidance into the categorized review library."""
        p=self.verify()
        if p['mode']!='learning':raise EvidenceError('Testing cannot write experience')
        if name not in ('success','expert'):raise EvidenceError('Unknown candidate kind')
        if name=='success' and self.state().get('training_accepted') is not True:raise EvidenceError('Success experience requires training acceptance')
        path=self.root/'candidate-pool'/(name+'.json')
        if not path.is_file():raise EvidenceError('No reusable experience was extracted; first-pass successes are not published')
        record=read(path)
        if record.get('published_sha256') or record.get('published_proposal_sha256'):return record.get('published_sha256') or record['published_proposal_sha256']
        if name=='success' and (self.state().get('training_accepted') is not True or record.get('training_accepted') is not True):raise EvidenceError('Success experience requires training acceptance')
        from . import experience_reflection as reflection
        update=record['reflection_update'];experience=record['experience']
        from . import compact_experience as compact
        if compact.is_library(p['store']):
            receipt=compact.publish_candidate(p['store'],record)
            record.update(receipt);self.save(path.relative_to(self.root),record)
            return receipt.get('published_sha256') or receipt['published_proposal_sha256']
        raise EvidenceError('Publish new experience into the categorized library; archive stores are read-only')

    def report(self):
        state=self.state();attempts=state['attempts'];p=read(self.root/'protocol.json')
        if not current_protocol(p):return read(self.root/'summary.json')
        for row in state['stages']:
            path=self.root/'stages'/row['key']/'result.json'
            if path.exists() and 'requests' not in row:
                result=read(path);row['measured_requests']=result.get('requests');row['measured_tokens']=result.get('tokens')
        result=dict(protocol=p['schema_version'],evaluation_split=p.get('evaluation_split'),learning_policy=p['learning_policy'],online_snapshot_sha256=state.get('online_snapshot_sha256'),model=p['model'],model_profile=p['model_profile'],mode=p['mode'],condition=p['condition'],status=state['status'],
            reflection_updates=[dict(name=name,update=read(self.root/'candidate-pool'/(name+'.json')).get('reflection_update'),
                publication_kind=read(self.root/'candidate-pool'/(name+'.json')).get('publication_kind')) for name in ('success','expert') if (self.root/'candidate-pool'/(name+'.json')).exists()],
            transport_executions=sum(len(s.get('executions',[])) for s in state['stages']),
            transport_retries=sum(restart_counts(s)['transport_retries'] for s in state['stages']),
            tool_policy_recoveries=sum(restart_counts(s)['tool_policy_recoveries'] for s in state['stages']),
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
            preparation_validation_policy=p.get('preparation_validation_policy'),preparation_warnings=state.get('preparation_warnings',[]),
            preparation_corrections=sum(s['key'].endswith('-validation-correction') for s in state['stages']),
            contract_review_policy=p.get('contract_review_policy'),
            diagnoses=[d['diagnosis'] for d in state['diagnoses']],requests=sum(s['requests'] for s in state['stages'] if type(s.get('requests')) is int),
            unknown_request_stages=[s['key'] for s in state['stages'] if s['kind'] in LIMITS and type(s.get('requests')) is not int],
            cumulative_action_request_cap=p['limits']['action']['requests']*p['max_attempts'],
            stages=state['stages'],delivery=read(self.root/'delivery.json') if (self.root/'delivery.json').exists() else None,
            candidate_learning_enabled=p['mode']=='learning',extraction_disposition=state.get('extraction_disposition'),
            extraction_error=state.get('extraction_error'),learning_error=state.get('learning_error'),error=state.get('error'))
        self.save('summary.json',result);return result
