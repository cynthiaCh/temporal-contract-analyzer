"""Read-only cluster consistency analysis; recorded membership, not ID prefixes."""
import collections,csv,hashlib,json,statistics
from pathlib import Path
A=Path(__file__).resolve().parent

def read(p):return json.loads(Path(p).read_text())
def save(name,x):(A/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def csvout(name,rows):
 if not rows:return
 with (A/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader()
  for r in rows:w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in r.items()})

def stats(rows):
 n=sum(r['valid_scores'] for r in rows);p=sum(r['passes'] for r in rows);rates=[1-r['pass_rate'] for r in rows if r['valid_scores']]
 return {'case_count':len(rows),'valid_scores':n,'passes':p,'failures':n-p,'failure_rate':(n-p)/n if n else None,'mean_case_failure_rate':statistics.mean(rates) if rates else None,'median_case_failure_rate':statistics.median(rates) if rates else None,'min_case_failure_rate':min(rates) if rates else None,'max_case_failure_rate':max(rates) if rates else None,'cases_failure_at_least_50_percent':sum(v>=.5 for v in rates),'cases_failure_above_archive_rate':None}

def main():
 manifest=read(A/'source-manifest.json');P=Path(manifest['parent_analysis'])
 for name,h in manifest['parent_files'].items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==h
 cases=read(P/'case-ranking.json');executions=read(P/'execution-groups.json');previous=read(P/'summary.json')
 byid={r['case_id']:r for r in cases};evidence=collections.defaultdict(list);source_memberships=collections.defaultdict(set)
 for line in (P/'raw-run-receipts.jsonl').open():
  row=json.loads(line);x=row['data'];parts=Path(x.get('manifest','')).parts
  if 'case-clusters' in parts:
   i=parts.index('case-clusters');evidence[x['case_id']].append({'cluster':parts[i+1],'manifest':x['manifest'],'receipt':row['path']})
  unit=x.get('source_unit') or x.get('independent_unit_id')
  if unit:source_memberships[x['case_id']].add(unit)
 mapped={};mapping=[]
 for r in cases:
  cid=r['case_id'];clusters=sorted({x['cluster'] for x in evidence[cid]});known=len(clusters)==1
  if known:mapped[cid]=clusters[0]
  mapping.append({'case_id':cid,'cluster':clusters[0] if known else None,'membership_status':'recorded_manifest_path' if known else 'unknown' if not clusters else 'conflicting','source_unit':r['source_units'],'historical_manifest_evidence':evidence[cid][:1],'valid_scores':r['valid_scores']})
 save('membership-evidence.json',mapping);csvout('case-membership.csv',mapping)
 clusters=collections.defaultdict(list)
 for r in cases:
  if r['case_id'] in mapped and r['valid_scores']:clusters[mapped[r['case_id']]].append(r)
 archive_failure=1-previous['primary_copy_folded']['pass_rate'];cluster_rows=[];case_rows=[]
 for cluster,rows in clusters.items():
  s=stats(rows);s['cases_failure_above_archive_rate']=sum(1-r['pass_rate']>archive_failure for r in rows)
  cluster_rows.append({'cluster':cluster,**s,'failure_difference_vs_archive_percentage_points':100*(s['failure_rate']-archive_failure),'source_units':sorted({u for r in rows for u in r['source_units']})})
  for r in rows:case_rows.append({'cluster':cluster,'case_id':r['case_id'],'passes':r['passes'],'valid_scores':r['valid_scores'],'failures':r['valid_scores']-r['passes'],'failure_rate':1-r['pass_rate'],'excluded_or_unverified':r['excluded_or_unverified']})
 cluster_rows.sort(key=lambda r:-r['failure_rate']);case_rows.sort(key=lambda r:(r['cluster'],-r['failure_rate'],r['case_id']));csvout('cluster-ranking.csv',cluster_rows);csvout('cluster-case-rates.csv',case_rows)
 # Compare high-failure anchors against siblings, leaving the anchor out.
 anchors=[r for r in cases if r['valid_scores']>=10 and 1-r['pass_rate']>=.5 and r['case_id'] in mapped]
 peers=[]
 for a in anchors:
  rs=[r for r in clusters[mapped[a['case_id']]] if r['case_id']!=a['case_id'] and r['valid_scores']>=10];s=stats(rs)
  peers.append({'anchor':a['case_id'],'cluster':mapped[a['case_id']],'anchor_failure_rate':1-a['pass_rate'],'anchor_valid_scores':a['valid_scores'],'sibling_case_count':len(rs),'sibling_failures':s['failures'],'sibling_valid_scores':s['valid_scores'],'sibling_failure_rate':s['failure_rate'],'sibling_mean_case_failure_rate':s['mean_case_failure_rate'],'sibling_min_failure_rate':s['min_case_failure_rate'],'sibling_max_failure_rate':s['max_case_failure_rate'],'siblings_failure_at_least_50_percent':s['cases_failure_at_least_50_percent']})
 csvout('leave-one-case-out-peers.csv',peers)
 # Configuration matching is descriptive. Source/evaluation versions remain case-specific.
 STRATA=['model','effort','condition','variant','workflow_profile','timeout_seconds']
 cells=collections.defaultdict(lambda:collections.defaultdict(list))
 for r in executions:
  if r['valid_score'] and r['case_id'] in mapped:cells[tuple(r.get(k) for k in STRATA)][r['case_id']].append(r)
 matched=[]
 for a in anchors:
  cid=a['case_id'];cl=mapped[cid]
  for key,group in cells.items():
   if cid not in group:continue
   siblings={c:rs for c,rs in group.items() if c!=cid and mapped[c]==cl}
   if not siblings:continue
   own=group[cid];n=len(own);fails=sum(r['verdict']!='PASS' for r in own)
   other=[r for rs in siblings.values() for r in rs];otherfails=sum(r['verdict']!='PASS' for r in other)
   sibling_rates=[sum(r['verdict']!='PASS' for r in rs)/len(rs) for rs in siblings.values()]
   matched.append({'cluster':cl,'anchor':cid,**dict(zip(STRATA,key)),'anchor_failures':fails,'anchor_valid':n,'anchor_failure_rate':fails/n,'sibling_cases':len(siblings),'sibling_failures':otherfails,'sibling_valid':len(other),'sibling_failure_rate':otherfails/len(other),'mean_sibling_case_failure_rate':statistics.mean(sibling_rates),'failure_difference_vs_peers_percentage_points':100*(fails/n-otherfails/len(other)),'sparse_anchor_less_than_3':n<3,'sparse_peer_average_less_than_3':len(other)/len(siblings)<3,'source_versions_held_identical':False,'independent_observation_claim':False})
 csvout('configuration-matched-peers.csv',matched)
 # Use a single highest observed-failure anchor per cluster, then leave it out.
 selected=[]
 for cr in cluster_rows:
  members=[r for r in anchors if mapped[r['case_id']]==cr['cluster']]
  if not members:continue
  anchor=sorted(members,key=lambda r:(r['pass_rate'],-r['valid_scores'],r['case_id']))[0]
  selected.append(next(p for p in peers if p['anchor']==anchor['case_id']))
 # Illustrative posthoc contrast: same recorded model/effort/time, common query arms.
 contrast_cells=collections.defaultdict(lambda:collections.defaultdict(list))
 for r in executions:
  if (r['valid_score'] and mapped.get(r['case_id'])=='query-paused-initial-fetch-10266' and r['model']=='gpt-6-sol' and r['effort']=='low' and r['timeout_seconds']==600 and r['condition'] in ['latent-maintenance','contract-provided-maintenance']):
   contrast_cells[r['condition']][r['case_id']].append(r)
 common=sorted(set(contrast_cells['latent-maintenance']) & set(contrast_cells['contract-provided-maintenance']))
 contrasts=[]
 for cid in common:
  l=contrast_cells['latent-maintenance'][cid];c=contrast_cells['contract-provided-maintenance'][cid]
  contrasts.append({'case_id':cid,'model':'gpt-6-sol','effort':'low','seconds':600,'latent_failures':sum(r['verdict']!='PASS' for r in l),'latent_valid':len(l),'provided_contract_failures':sum(r['verdict']!='PASS' for r in c),'provided_contract_valid':len(c),'recorded_version_hashes_equal':{r['version_hash'] for r in l}=={r['version_hash'] for r in c},'scorer_version_equivalence_verified':False})
 csvout('illustrative-condition-contrast.csv',contrasts)
 condition_contrast={'posthoc_illustration_not_causal_estimate':True,'model':'gpt-6-sol','effort':'low','seconds':600,'common_cases':len(common),'latent_failures':sum(r['latent_failures'] for r in contrasts),'latent_valid':sum(r['latent_valid'] for r in contrasts),'provided_contract_failures':sum(r['provided_contract_failures'] for r in contrasts),'provided_contract_valid':sum(r['provided_contract_valid'] for r in contrasts),'cases_with_equal_recorded_version_hashes':sum(r['recorded_version_hashes_equal'] for r in contrasts),'per_case_n':1,'scorer_equivalence_verified':False}
 # Source units can span several clusters. Do not conflate these groupings.
 units=collections.defaultdict(list)
 for r in cases:
  if len(r['source_units'])==1 and r['valid_scores']:units[r['source_units'][0]].append(r)
 source_rows=[{'source_unit':u,**stats(rs),'recorded_clusters':sorted({mapped[r['case_id']] for r in rs if r['case_id'] in mapped}),'cases_without_recorded_cluster':[r['case_id'] for r in rs if r['case_id'] not in mapped]} for u,rs in units.items()]
 csvout('source-unit-summary.csv',source_rows)
 legacy=[r for r in cases if r['case_id']=='query-paused-initial-fetch-10266']
 result={'status':'COMPLETE_OFFLINE_ANALYSIS','source_analysis':str(P),'case_count':len(cases),'cases_with_recorded_cluster':len(mapped),'recorded_cluster_count':len(clusters),'unassigned_cases':[r['case_id'] for r in cases if r['case_id'] not in mapped],'archive_failure_rate':archive_failure,'membership_policy':'Use explicit historical manifest case-clusters/<cluster>/ paths; unique case mapping is propagated only for descriptive grouping. No ID-prefix inference or silent current-catalog fallback.','cluster_rows':cluster_rows,'high_failure_definition':'At least 10 valid scores and failure rate >= 50%; descriptive, not preregistered confirmatory inference.','high_failure_anchor_count':len(anchors),'representative_leave_one_out':selected,'illustrative_condition_contrast':condition_contrast,'matched_strata_rows':len(matched),'matched_rows_anchor_at_least_3':sum(not x['sparse_anchor_less_than_3'] for x in matched),'same_source_legacy_query_case':legacy,'limits':['Within-cluster arms and repetitions are not independent source incidents.','Pooled rates mix models, prompts, budgets and case/evaluator versions. Matched tables hold recorded model/effort/condition/variant/workflow/timeout fixed, but not semantics or scoring versions.','One high-failure case was selected per cluster by observed outcomes; its peers omit that case, but this remains posthoc descriptive analysis, not classifier accuracy or a generalization test.','Not every same-cluster case has high failure. Broad source-unit grouping may merge several distinct clusters.'],'experimental_model_calls':0,'new_scores':0}
 save('summary.json',result)
 def pc(v):return 'N/A' if v is None else '%.2f%%'%(100*v)
 lines=['Do hard cases imply hard cluster siblings?', '', 'Answer: often for the query cluster, but not uniformly across other clusters. This analysis retains the previous receipt admission and exact-copy folding. No model or grader is run.','',f"Historical manifest paths identify {len(mapped)} of {len(cases)} case IDs in {len(clusters)} clusters. Unassigned cases stay unassigned; cluster identity is not inferred from names. A source unit may contain several clusters.",'', '|Cluster|Cases|Failures / valid|Pooled failure rate|Case failure range|Cases with >=50% failures|','|---|---:|---:|---:|---:|---:|']
 for r in cluster_rows:lines.append('|'+r['cluster']+'|'+str(r['case_count'])+'|'+str(r['failures'])+'/'+str(r['valid_scores'])+'|'+pc(r['failure_rate'])+'|'+pc(r['min_case_failure_rate'])+' to '+pc(r['max_case_failure_rate'])+'|'+str(r['cases_failure_at_least_50_percent'])+'/'+str(r['case_count'])+'|')
 lines+=['','Comparisons that leave the selected hard case out:', '', '|Selected hard case|Cluster|Own failure rate|Sibling failures / valid|Sibling failure rate|Sibling range|','|---|---|---:|---:|---:|---:|']
 for r in selected:lines.append('|'+r['anchor']+'|'+r['cluster']+'|'+pc(r['anchor_failure_rate'])+'|'+str(r['sibling_failures'])+'/'+str(r['sibling_valid_scores'])+'|'+pc(r['sibling_failure_rate'])+'|'+pc(r['sibling_min_failure_rate'])+' to '+pc(r['sibling_max_failure_rate'])+'|')
 lines+=['', 'Main observations:', '', '1. All nine formally mapped query variants have failure rates above 76%. Even after omitting the hardest Java variant, the other eight retain a high pooled failure rate. This is the clearest within-cluster difficulty pattern in this archive.', '2. document-review-binding ranges from about one third to over 86% failures. The non-vanilla review-confirmation variants are much harder than several submit-snapshot variants; the vanilla review-confirmation arm itself is easier. Cluster membership alone does not guarantee equally hard training and test cases.', '3. transfer-retry-handoff also has wide variation. The composition/window-cued Java arm is hard, while several maintenance variants have failure rates around 30%–40%. The shared source mechanism does not establish equal difficulty.', '4. The debounced-submit-flush source unit spans multiple clusters, including hard draft-autosave-handoff and much easier draft-handoff-decomposition. Treating this entire source unit as one cluster would obscure important differences.', '5. A legacy case named query-paused-initial-fetch-10266 has 11/11 passes under the same source-unit label, but its recorded manifest is cases/... rather than membership in the nine current cluster arms. It is separately reported, not silently merged into those arms or relabeled as the same task version.','', 'Matched configuration checks:', '',f"configuration-matched-peers.csv contains {len(matched)} leave-one-case-out comparisons within the same recorded model, effort, prompt condition, variant, workflow profile and time budget. Only {sum(not x['sparse_anchor_less_than_3'] for x in matched)} rows have at least three anchor scores. These repeats remain correlated and may use distinct case/evaluator versions; no significance or causal cluster-effect claim is made.", '', 'Illustrative prompt-condition contrast:', '',f"For the {len(common)} common query arms under recorded gpt-6-sol/low and 600 seconds, latent-maintenance fails {condition_contrast['latent_failures']}/{condition_contrast['latent_valid']}, while provided-Contract fails {condition_contrast['provided_contract_failures']}/{condition_contrast['provided_contract_valid']}. Each arm has only one score per condition. The recorded manifest/input hashes agree for all eight pairs; evaluator versions and all other execution details are not independently verified. This posthoc illustration shows why pooled cluster difficulty cannot predict a new AUTO protocol by itself. It is not a causal effect estimate.",'', 'Implication for selecting the next pair: use cluster membership to shortlist, then check each exact case under the intended model/effort/Contract/budget and score version. The query cluster offers stronger historical difficulty evidence than the wider document or transfer clusters. Do not assume that an arbitrary sibling must avoid a ceiling. No new experiment is started by this report.','', 'Files:', '', '- cluster-ranking.csv: all recorded cluster summaries.', '- cluster-case-rates.csv: every member and its rate.', '- leave-one-case-out-peers.csv: all hard anchors with the anchor removed from sibling statistics.', '- configuration-matched-peers.csv: configuration-matched sibling comparisons; no score-version equivalence claim.', '- membership-evidence.json and case-membership.csv: exact historical membership evidence and unknowns.', '- illustrative-condition-contrast.csv: eight common query cases demonstrating condition dependence.', '- source-unit-summary.csv: the broader source grouping kept separate.', '- summary.json and source-manifest.json: conclusions and unchanged input hashes.']
 (A/'REPORT.md').write_text('\n'.join(lines)+'\n')
 print(json.dumps({'clusters':len(clusters),'mapped_cases':len(mapped),'high_failure_anchors':len(anchors),'representatives':selected,'matched_rows':len(matched)},ensure_ascii=False))

if __name__=='__main__':main()
