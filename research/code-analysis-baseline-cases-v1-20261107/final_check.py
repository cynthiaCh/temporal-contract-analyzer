"""Offline final archive/reference checks; no semantic or behavioral scoring."""
import csv,json,re
from pathlib import Path
from run import OUT,ROOT,read,save,sha,frozen
from collect import main as collect

def main():
 frozen();collect()
 assert sha(OUT/'review.csv')==read(OUT/'review.freeze.json')['review_sha256']
 review=list(csv.DictReader((OUT/'review.csv').open()));assert len(review)==54
 keys=[(r['call_id'],r['item_id']) for r in review];assert len(keys)==len(set(keys))
 for row in review:
  quotes=json.loads(row['report_quotes']);f=OUT/'runs'/row['call_id']/'report.md';lines=f.read_text().splitlines()
  assert all(lines[q['line']-1]==q['text'] for q in quotes)
  for ref in row['source_refs'].split(';'):
   path,nums=ref.rsplit(':',1);a,*b=nums.split('-');start=int(a);end=int(b[0]) if b else start
   assert (OUT/path).is_file() and 1<=start<=end<=len((OUT/path).read_text().splitlines())
  for ref in row['standard_refs'].split(';'):
   path,n=ref.rsplit(':',1);assert (ROOT/path).is_file() and 1<=int(n)<=len((ROOT/path).read_text().splitlines())
  for ref in row['tool_refs'].split(';'):
   path,n=ref.rsplit(':',1);event=json.loads((OUT/path).read_text().splitlines()[int(n)-1]);assert event['type']=='item.completed' and event['item']['type']=='command_execution'
  assert row['judgment'] in ['满足','部分满足','不满足','证据不足']
  if row['row_kind']=='pending_policy':assert row['judgment']=='证据不足' and row['counts_as_definite_business_error']=='False'
 readback=[];nonzero=[];citation_checks=[]
 for rec in read(OUT/'requests.json'):
  folder=OUT/'runs'/rec['call_id'];raw=json.loads((folder/'raw-answer.txt').read_text());assert (folder/'report.md').read_text()==raw['report'] and len(raw['report'])<=6000
  output='\n'.join(t['item'].get('aggregated_output','') for t in rec['tool_index'])
  # Mechanical readback of source lines corroborates actual observations, not semantic use.
  material=OUT/'materials'/rec['case']/'candidate';missing=[]
  for f in material.rglob('*'):
   if f.is_file():
    for n,line in enumerate(f.read_text().splitlines(),1):
     if line.strip() and line.strip() not in output:missing.append(str(f.relative_to(material))+':'+str(n))
  assert not missing,(rec['call_id'],missing)
  readback.append(dict(call_id=rec['call_id'],all_nonempty_candidate_lines_in_actual_tool_outputs=True,semantic_use_inferred=False))
  for t in rec['tool_index']:
   if t['item'].get('exit_code')!=0:nonzero.append(dict(call_id=rec['call_id'],line=t['line'],exit_code=t['item'].get('exit_code')))
  # Report explicit path:line anchors checked against its own frozen candidate.
  matches=re.findall(r'(?:(?:/workspace/)?(?:src/)?(?:[A-Za-z0-9_-]+\.js|README\.md)):[0-9]+(?:[-–][0-9]+)?',raw['report'])
  for ref in matches:
   path,num=ref.rsplit(':',1);path=path.removeprefix('/workspace/') if hasattr(path,'removeprefix') else (path[len('/workspace/'):] if path.startswith('/workspace/') else path)
   q=material/path
   if not q.is_file():
    found=list(material.rglob(Path(path).name));assert len(found)==1,(rec['call_id'],ref);q=found[0]
   nums=re.split('[-–]',num);a=int(nums[0]);b=int(nums[-1]);assert 1<=a<=b<=len(q.read_text().splitlines()),(rec['call_id'],ref)
   citation_checks.append(dict(call_id=rec['call_id'],report_reference=ref,frozen_source=str(q.relative_to(OUT)),start=a,end=b))
 # Output documents local links; normalize model /workspace paths to that run's source.
 checked_links=0
 for f in OUT.rglob('*.md'):
  if 'workspace' in f.relative_to(OUT).parts or 'offline' in f.relative_to(OUT).parts or 'materials' in f.relative_to(OUT).parts:continue
  for link in re.findall(r'\]\(([^)]+)\)',f.read_text()):
   if '://' in link:continue
   match=re.match(r'^(.*?):(\d+)$',link);name=match.group(1) if match else link
   if name.startswith('/workspace/'):
    call=f.parent.name;q=OUT/'runs'/call/'workspace'/name[len('/workspace/'):]
   else:q=f.parent/name
   assert q.exists(),(f,link)
   if match:assert q.is_file() and 1<=int(match.group(2))<=len(q.read_text().splitlines())
   checked_links+=1
 summary=read(OUT/'summary.json');costs=read(OUT/'costs.json');assert summary['costs']==costs['totals'] and summary['candidate_repeated_gaps']==[] and summary['next_step']['choice']=='D'
 assert summary['standard_confirmed_items']==[] and all(not x['approved'] for x in read(OUT/'confirmation-status.json')['cases'])
 assert not nonzero
 save(OUT/'citation-and-review-check.json',dict(status='PASS',review_quote_rows_verified=len(review),source_and_standard_and_tool_refs_verified=True,original_reports_unmodified=True,explicit_model_path_line_anchors=len(citation_checks),model_reference_anchors=citation_checks,semantic_accuracy_checked_by='Unblinded executing Agent; mechanical anchor validity does not prove semantic correctness',source_readback=readback,nonzero_command_items=nonzero,local_markdown_links_checked=checked_links))
 artifacts={str(f.relative_to(OUT)):sha(f) for f in sorted(OUT.rglob('*')) if f.is_file() and '.runtime' not in f.parts and f.name not in ['final-validation.json','ARTIFACTS.sha256']}
 save(OUT/'final-validation.json',dict(status='PASS',frozen_protocol_unchanged=True,review_frozen_and_summary_consistent=True,all_six_slots_archived=True,baseline_K0_only=True,standards_approval_unchanged=True,original_reports_not_rewritten=True,model_and_tool_counts_reconciled=True,all_old_files_preserved=read(OUT/'execution-validation.json')['changed_existing_files']==[],new_model_calls_for_validation=0,artifacts=artifacts))
 (OUT/'ARTIFACTS.sha256').write_text('\n'.join(h+'  '+name for name,h in sorted(artifacts.items()))+'\n')
 print('FINAL_OFFLINE_VALIDATION_PASS: 54 review rows, six raw reports, usage and source links verified')
if __name__=='__main__':main()
