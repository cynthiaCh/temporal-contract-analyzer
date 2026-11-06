"""Mechanical output extraction/diff/blinding only; no semantic judge."""
import csv,difflib,hashlib,json,re,secrets,shutil
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
def read(p):return json.loads(Path(p).read_text())
def sha(x):return hashlib.sha256(x if isinstance(x,bytes) else x.encode()).hexdigest()
def save(p,x):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
CRITERIA=['relation_direction','target_not_neighbor','executable_targeted_checks','preserve_passed_behavior','hypotheses_not_facts','maintain_original_maintenance','reusable_no_leak_no_expansion','length_and_nonredundancy']
def main():
    if (OUT/'private-label-mapping.json').exists():raise RuntimeError('Refuse re-anonymization')
    assert (OUT/'generation-complete.json').exists(),'Finalize after generation stops; no outputs sampled while running'
    schedule=read(OUT/'schedule.json')['order'];requests={r['call_id']:r for r in read(OUT/'requests.json')};ek=read(OUT/'evidence-key.json');pack=OUT/'anonymous-review';pack.mkdir(exist_ok=True);unit_alias={k['unit']:'E'+secrets.token_hex(3) for k in ek['units']};mapping={};results=[];reconciled=[]
    bans=read(OUT.parent/'gepa-feedback-projection-v1-20261106/skill-banned-identifiers.json')+read(OUT.parent/'gepa-feedback-projection-v1-20261106/private-score-identifiers.json')
    for key in ek['units']:
        alias=unit_alias[key['unit']];d=pack/'evidence'/alias;shutil.copytree(OUT/'evidence'/key['unit'],d)
        clean={k:v for k,v in key.items() if k not in ['unit','case','job','parent_origin','selection_reason','projection_source','raw_score_source','original_trajectory','patch_source']};clean.update(evidence_alias=alias,raw_score='raw-score.json',trajectory='events.jsonl',patch='patch.diff',review_scope='exposed development evidence; condition labels hidden, semantic source recognition possible');save(d/'key.json',clean);shutil.copyfile(OUT/'inputs'/key['unit']/'parent.md',d/'parent.md')
    for slot in schedule:
        cid='C'+secrets.token_hex(5);alias=unit_alias[slot['unit']];record=requests.get(slot['call_id']);folder=OUT/'runs'/slot['call_id'];raw=(folder/'raw-answer.txt').read_text() if (folder/'raw-answer.txt').exists() else '';d=pack/'candidates'/cid;d.mkdir(parents=True);(d/'raw.txt').write_text(raw);errors=[];obj=None;skill=None;notes=[]
        try:
            obj=json.loads(raw)
            assert isinstance(obj,dict) and set(obj)=={'skill','change_notes'} and isinstance(obj['skill'],str) and isinstance(obj['change_notes'],list)
            assert all(isinstance(n,dict) and set(n)=={'step','change','feedback_basis'} and all(isinstance(v,str) for v in n.values()) for n in obj['change_notes'])
            skill=obj['skill'];notes=obj['change_notes']
        except (ValueError,AssertionError,TypeError):errors.append('missing_or_invalid_output_schema')
        effective=False;diagnostics=[];real_tools=[]
        if record is not None:
            for line in (folder/'events.jsonl').read_text().splitlines():
                e=json.loads(line);i=e.get('item',{})
                if e.get('type')=='item.completed' and i.get('type')=='error':diagnostics.append(i.get('message',''))
                elif e.get('type')=='item.completed' and i.get('type') not in [None,'reasoning','agent_message']:real_tools.append(i)
            known=all(m.startswith('`--dangerously-bypass-hook-trust` is enabled.') or m.startswith('Code Mode is unavailable because code-mode host is disabled.') for m in diagnostics)
            session=record.get('native_request_account',{});effective=bool(record.get('exit_code')==0 and record.get('completed_turns')==1 and raw.strip() and session.get('started')==session.get('completed')==1 and not session.get('blocked_requests') and not session.get('tool_attempts') and not real_tools and not record.get('errors') and known)
            reconciled.append(dict(call_id=slot['call_id'],original_monitor_status=record['status'],effective_completion=effective,diagnostic_item_messages=diagnostics,actual_tool_items=len(real_tools),native_request_account=session,correction='Original monitor counted item.error diagnostics as tools; raw receipts and generation protocol remain unchanged.'))
        if not effective:errors.append('generation_not_completed')
        skillchars=len(skill) if skill is not None else None;noteschars=sum(len(v) for n in notes for v in n.values());hits=[]
        if skill is not None:
            if not skill.strip() or len(skill)>6000:errors.append('skill_length')
            if not notes or noteschars>1200:errors.append('notes_length_or_missing')
            hits=[b for b in bans if b.lower() in skill.lower()]
            pattern_hits=re.findall(r'\b[\w.-]+\.(?:js|jsx|vue|cjs|mjs|json)\b|evidence-[0-9a-f]+|src/|```',skill,re.I)
            (d/'skill.md').write_text(skill);(d/'notes.md').write_text('\n\n'.join('Note '+str(i)+'\nstep: '+n['step']+'\nchange: '+n['change']+'\nfeedback_basis: '+n['feedback_basis'] for i,n in enumerate(notes,1)))
            parent=(OUT/'inputs'/slot['unit']/'parent.md').read_text();(d/'parent.diff').write_text(''.join(difflib.unified_diff(parent.splitlines(True),skill.splitlines(True),fromfile='parent',tofile=cid)))
            sentences=[s.strip().lower() for s in re.split(r'[.!?]\s+|\n+',skill) if len(s.strip())>50];dups=sorted({s for s in sentences if sentences.count(s)>1});parent_match=sum(b.size for b in difflib.SequenceMatcher(None,parent,skill,autojunk=False).get_matching_blocks())
        else:pattern_hits=[];dups=[];parent_match=None;(d/'NO_VALID_SKILL.md').write_text('No schema-valid skill extracted. Raw output is preserved, not repaired.\n')
        mechanical=dict(candidate_id=cid,evidence_alias=alias,format_errors=errors,skill_characters=skillchars,notes_characters=noteschars,literal_forbidden_hits=hits,pattern_hits=pattern_hits,exact_internal_repeated_sentences=dups,parent_matching_characters=parent_match,semantic_judgment='not automated',raw_sha256=sha(raw))
        save(d/'mechanical.json',mechanical);results.append(mechanical);mapping[cid]=dict(**slot,evidence_alias=alias,raw_sha256=sha(raw),source_receipt=str(folder/'receipt.json'))
    save(OUT/'receipt-reconciliation.json',reconciled)
    save(OUT/'private-label-mapping.json',dict(created_after_raw_outputs=True,randomness='OS secrets.token_hex; no condition-coded IDs',candidates=mapping))
    save(pack/'mechanical-index.json',sorted(results,key=lambda x:x['candidate_id']))
    with (pack/'blank-review.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['candidate_id','evidence_alias','criterion','judgment','citations','rationale','reviewer_mode']);w.writeheader()
        for m in sorted(results,key=lambda x:x['candidate_id']):
            for criterion in CRITERIA:w.writerow(dict(candidate_id=m['candidate_id'],evidence_alias=m['evidence_alias'],criterion=criterion,judgment='',citations='',rationale='',reviewer_mode=''))
    (pack/'README.md').write_text('# Review package\n\nCandidate IDs and order are random. The private condition/unit/generation-order map is outside this package. Use evidence/<alias>/key.json, raw evidence and parent.md, and candidates/<ID>/skill.md/notes.md/parent.diff.\n\nLabels alone are hidden; content, parent skills and necessary raw evidence can reveal source or suggest condition. The executing agent participated in preparation: its review MUST be marked unblinded proxy, not independent human or independent blind assessment. No LLM judge is invoked. Keep a blank form for future independent human review. Freeze review.csv before unblinding.\n\nEight candidates are two units with two repetitions per condition, not eight independent tasks.\n')
    save(OUT/'anonymization.json',dict(candidate_count=len(results),label_map_sha256=sha((OUT/'private-label-mapping.json').read_bytes()),independent_human_review_complete=False,executing_agent_review_mode='unblinded proxy',created_after_raw=True))
    print('ANONYMIZED_PACKAGE_READY',len(results),'No condition labels printed')
if __name__=='__main__':main()
