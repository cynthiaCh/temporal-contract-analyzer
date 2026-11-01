"""Prepare neutral source snapshots, reuse audit and balanced anonymous slots.

No candidate execution, scoring, model call or participant enrollment occurs.
Snapshot base+overlay construction is recorded; original runtime validation and
independent gold review are still required before an actual study.
"""
from collections import Counter
import csv
import hashlib
import itertools
import json
from pathlib import Path
import random
import shutil

ROOT = Path(__file__).resolve().parents[2]
BENCH = Path('/Volumes/Extreme/paper+survey/temporal-contract-bench')
OUT = ROOT / 'refine-logs/evidence/review-design'
SPECS = [
 ('T01','listener-registration-order-vanilla','reference/bounded','listener_delivery',True),
 ('T02','document-submit-snapshot-vanilla','mutants/document-key-notice','draft_handoff',True),
 ('T03','download-polling-restoration-low-cue-react18','mutants/shared-dialog-policy','preparation_lifecycle',True),
 ('T04','async-generator-close-python','reference/bounded','generator_resource',True),
 ('T05','transfer-progress-maintenance-v2-vanilla','mutants/drop-accepted-progress','transfer_delivery',True),
 ('T06','local-config-readiness-latent-vue2','mutants/promise-microtask-retention','component_readiness',True),
 ('C07','draft-async-save-handoff-vanilla','mutants/document-only-status','draft_handoff',False),
 ('C08','workspace-draft-projection-latent-vanilla','mutants/local-editor-only','draft_handoff',False),
]

def digest(path):
 return hashlib.sha256(path.read_bytes()).hexdigest()

def copy_files(source,destination):
 for path in sorted(source.rglob('*')):
  if path.is_symlink():raise ValueError('Symlink in snapshot: '+str(path))
  relative=path.relative_to(source)
  if any(p in {'node_modules','.git','__pycache__'} for p in relative.parts):continue
  target=destination/relative
  if path.is_dir():target.mkdir(parents=True,exist_ok=True)
  elif path.is_file():
   target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)

def main():
 if OUT.exists():raise SystemExit('Refusing to overwrite prepared design: '+str(OUT))
 OUT.mkdir(parents=True)
 roster=json.loads((BENCH/'benchmark/swe-tempoc.json').read_text())['cases']
 by={r['case_id']:r for r in roster};records=[]
 extensions={'.js','.jsx','.ts','.tsx','.vue','.py','.mjs','.cjs'}
 for task,case,variant,family,primary in SPECS:
  row=by[case];base=(BENCH/row['manifest']).parent
  project=OUT/'snapshots'/task/'project';project.mkdir(parents=True)
  copy_files(base/'base',project);copy_files(base/variant,project)
  files={str(p.relative_to(project)):digest(p) for p in sorted(project.rglob('*')) if p.is_file()}
  code={name:h for name,h in files.items() if Path(name).suffix.lower() in extensions}
  records.append(dict(task_id=task,case_id=case,source_unit=row['source_unit'],variant=variant,
      reuse_family=family,primary=primary,candidate_path=str(project.relative_to(ROOT)),
      construction='base plus variant file overlay; no runtime verification performed',
      all_candidate_file_sha256=files,code_file_sha256=code,expected_answers=None,
      status='prepared planning snapshot; gold and original scorer validation pending'))
 pairs=[]
 for left,right in itertools.combinations(records,2):
  common=[]
  for a,sha in left['code_file_sha256'].items():
   for b,shb in right['code_file_sha256'].items():
    if sha==shb:common.append(dict(left_path=a,right_path=b,sha256=sha))
  if common:pairs.append(dict(left=left['task_id'],right=right['task_id'],identical_source_files=common))
 primary=[r for r in records if r['primary']]
 assert len({r['reuse_family'] for r in primary})==len(primary)==6
 primary_ids={r['task_id'] for r in primary}
 collisions=[r for r in pairs if r['left'] in primary_ids and r['right'] in primary_ids]
 # A code-byte collision requires revisiting the declared reuse families.
 assert not collisions, collisions
 williams=[[0,1,3,2],[1,2,0,3],[2,3,1,0],[3,0,2,1]]
 conditions=['S','V0','F','U']
 orders=[[0,1,2,3,4,5],[3,4,5,0,1,2],[5,4,3,2,1,0]]
 slots=list(range(12));random.Random(20261029).shuffle(slots);schedule=[]
 for slot,design in enumerate(slots,1):
  row=williams[design%4];order=orders[design//4]
  for position,t in enumerate(order,1):
   task=primary[t]
   schedule.append(dict(slot_id='P%02d'%slot,position=position,task_id=task['task_id'],
       reuse_family=task['reuse_family'],condition=conditions[row[t%4]],
       status='planned anonymous slot; no participant assigned'))
 for slot in range(1,13):
  rows=[r for r in schedule if r['slot_id']=='P%02d'%slot]
  assert len(rows)==6 and len({r['reuse_family'] for r in rows})==6
  assert sorted(Counter(r['condition'] for r in rows).values())==[1,1,2,2]
 for task in primary:
  assert Counter(r['condition'] for r in schedule if r['task_id']==task['task_id'])==dict.fromkeys(conditions,3)
 for position in range(1,7):
  assert Counter(r['condition'] for r in schedule if r['position']==position)==dict.fromkeys(conditions,3)
 (OUT/'tasks-analyst-only.json').write_text(json.dumps(dict(records=records,exposure='author-exposed development corpus'),indent=2)+'\n')
 (OUT/'reuse-audit.json').write_text(json.dumps(dict(scope='full materialized candidate file hashes; code-byte pair overlap',pairs=pairs,primary_exact_source_collisions=collisions,
    caveat='absence of byte-identical files does not establish semantic or historical independence'),indent=2)+'\n')
 with (OUT/'allocation.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(schedule[0]));w.writeheader();w.writerows(schedule)
 (OUT/'allocation-checks.json').write_text(json.dumps(dict(participant_slots=12,actual_participants=0,tasks=6,answers_planned=72,answers_collected=0,
    per_task_condition=3,per_position_condition=3,per_person_condition_counts=[1,1,2,2],known_reuse_family_repeated_within_person=False,model_calls=0),indent=2)+'\n')
 print(json.dumps(dict(snapshots=len(records),primary_tasks=6,source_overlap_pairs=len(pairs),planned_answers=len(schedule),actual_participants=0,model_calls=0)))

if __name__=='__main__':main()
