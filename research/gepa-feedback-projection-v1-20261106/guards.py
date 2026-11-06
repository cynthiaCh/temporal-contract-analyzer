"""Offline-testable scope, admission, budget and skill-delivery boundaries."""
import json,re,hashlib
from pathlib import Path
OUT=Path(__file__).resolve().parent
class AdmissionBlocked(RuntimeError):pass
class BudgetExceeded(RuntimeError):pass
def admission():
    source=json.loads((OUT/'source-verification.json').read_text());split=json.loads((OUT/'split.json').read_text())
    if source['status']!='PASS' or not split.get('formal_execution_allowed') or len(split['train'])<2 or len(split['val'])<2 or len(split['test'])<3:raise AdmissionBlocked('No qualifying new val/test source split. Formal model execution is disabled.')
    return split
class BudgetLedger:
    """Per-arm counters. Launches are never refunded; receipts and metric calls differ."""
    def __init__(self):self.tasks=0;self.metric_calls=0;self.cli_sessions=0;self.reflection_native=0;self.execution_native=0;self.reflection_sessions=0
    def reserve_task_batch(self,count):
        if not isinstance(count,int) or count<1 or self.tasks+count>12:raise BudgetExceeded('per-arm 12-task cap')
        self.tasks+=count;self.cli_sessions+=count
    def account_metrics(self,count):
        if count<0 or self.metric_calls+count>self.tasks:raise BudgetExceeded('metric receipts cannot exceed launches')
        self.metric_calls+=count
    def reserve_reflection_cli(self):
        if self.reflection_sessions>=3:raise BudgetExceeded('per-arm 3 reflection callable/CLI entries')
        self.reflection_sessions+=1;self.cli_sessions+=1
    def account_reflection_pre_request(self):
        if self.reflection_native>=3:raise BudgetExceeded('per-arm 3 native reflection requests')
        self.reflection_native+=1
    def account_execution_pre_request(self):self.execution_native+=1
    def may_start_iteration(self):return 12-self.tasks>=6 and self.reflection_native<3 and self.reflection_sessions<3
    def snapshot(self):return dict(task_executions=self.tasks,metric_calls=self.metric_calls,cli_sessions=self.cli_sessions,reflection_native_requests=self.reflection_native,execution_native_requests=self.execution_native)
def skill_boundary(candidate,review=None):
    text=candidate.get('temporal_skill','') if isinstance(candidate,dict) else '';errors=[]
    if not isinstance(candidate,dict) or set(candidate)!={'temporal_skill'} or not isinstance(text,str) or not text.strip() or len(text)>6000:errors.append('single-component text/length constraint')
    if not isinstance(text,str):text=''
    if re.search(r'```|\b[\w.-]+\.(?:js|jsx|vue|cjs|mjs|md|json)\b|/workspace|src/|</temporal-contract-skill>|evidence-[0-9a-f]+|e-[0-9a-f]{16}|\b[0-9a-f]{64}\b',text,re.I):errors.append('code, paths or research evidence identifier')
    if re.search(r'(?i)(?:ignore|replace|override|bypass) (?:the )?(?:original task|fixed ending|tool permissions|scor(?:e|ing))',text):errors.append('fixed perimeter override')
    bans=json.loads((OUT/'skill-banned-identifiers.json').read_text());bans+=json.loads((OUT/'private-score-identifiers.json').read_text())
    if any(v.lower() in text.lower() for v in bans):errors.append('case/program/private scoring identifier')
    if re.search(r'(?i)(?:set|assign)\s+(?:the\s+)?loading\s*(?:=|to)\s*(?:true|false)',text):errors.append('case-specific implementation recipe')
    h=hashlib.sha256(text.encode()).hexdigest();seed=text==(OUT/'K0.md').read_text()
    reviewed=bool(review and review.get('skill_sha256')==h and review.get('allow_execution') and all(review.get(k) is True for k in ['no_hidden_scoring_or_reference_repair','no_case_specific_answer_including_renamed_answers','source_qualified_not_new_business_rules','fixed_maintenance_objective_preserved']))
    return dict(mechanical_pass=not errors,errors=errors,sha256=h,allow_execution=not errors and (seed or reviewed),semantic_review_required=not seed,limitation='Lexical checks do not certify semantic non-leakage; every generated candidate requires a hash-bound semantic review. Renaming an answer does not authorize it.')

def deduplicated_test_schedule(cases,skills):
    if len(cases)!=3 or len(set(cases))!=3:raise AdmissionBlocked('Exactly three frozen test sources required')
    unique={}
    for label,text in skills.items():unique.setdefault(hashlib.sha256(text.encode()).hexdigest(),dict(text=text,aliases=[]))['aliases'].append(label)
    if len(unique)>3:raise BudgetExceeded('At most K0 and two selected versions')
    schedule=[dict(case=c,skill_sha256=h,replicate=r,aliases=v['aliases']) for r in [1,2] for c in cases for h,v in unique.items()]
    if len(schedule)>18:raise BudgetExceeded('18 test-task cap')
    return schedule
