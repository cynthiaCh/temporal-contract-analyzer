"""Read-only consolidation candidates; no guidance, review or scores modified."""
import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from temporal_contract_analyzer.compact_experience import documents,active_view,SECTIONS
OUT=Path(__file__).resolve().parent
LIBRARY=OUT.parents[2]/'experience-memory/library'

# Source comparison judgments, not automatically generated merge instructions.
SPEC=[
 ('trailing-coalescing',['trailing-coalescing','editor-trailing-bursts'],'priority',
  'Same latest-value trailing batch policy and applicability.',
  ['Keep empty input and no-current-document guard.','Retain independent keys, restartable quiet interval, later reuse and no hardcoded120ms.']),
 ('consume-before-callback',['consume-before-callback','editor-batch-reentry'],'priority',
  'Both consume old pending state before synchronous reentrant saving.',
  ['Retain exact absence sentinel and valid empty values.','Retain nested flush cardinality and callback-created next batch.']),
 ('full-frame-arrival-order',['result-freshness','progress-full-frame-order'],'priority',
  'Same arrival-defined full-frame freshness; the progress entry adds explicit cross-retry scope.',
  ['Only with target-supported full-frame arrival-order policy; never required deltas.','Preserve independent audit and decreases/resets; commit watermark before callbacks.','Determine visit/attempt scope from current source.']),
 ('audit-versus-publication',['retained-effects','progress-audit-publication'],'priority',
  'Same independently retained admitted audit and visit-bound publication.',
  ['Retain audit cardinality after retirement.','Recheck publication authority after audit callback; preserve current visit delivery.','Explicit source discard policies override retention applicability.']),
 ('persistent-owner',['persistent-owner','editor-owner-lifetime'],'priority',
  'Same persistent buffer owner distinct from view subscription lifetime.',
  ['Preserve origin identity, subscription cleanup and reopening.','Persistent ownership does not establish synchronous departure flush.','Do not transfer retention to transient preview discard.']),
 ('terminal-modal',['candidate-a272','candidate-a631','candidate-acc7'],'priority',
  'Same terminal-modal completion guard across framework ports.',
  ['Preserve invocation and original-result completion outside modal effect guard.','Preserve shell independence and current terminal lifecycle.','Publication exists only where source supplies it; reentry checkpoint is conditional, not universal.']),
 ('active-buffer-clear',['candidate-a5cf','candidate-1848','candidate-b9be','candidate-4430'],'conditional',
  'Common active-only discard policy, with predicate declarations and native-storage evidence differences.',
  ['Reconcile applicability predicates without taking their blanket union.','Preserve committed replay during inline completion callbacks, undefined presence and subscribers.','Preserve instance/native storage ownership; unavailable host details remain unknown.']),
 ('progress-reception',['candidate-c0da','candidate-336b','candidate-5f84','candidate-4eef','candidate-a53e','candidate-c034'],'split-policy',
  'Shared reception/lifecycle/audit basis, but two incompatible unconditional freshness policies.',
  ['Keep maintenance-only variant separate from explicit full-frame freshness variant.','Maintenance IDs c0da/c034 do not authorize arrival filtering.','Freshness IDs336b/5f84/4eef/a53e require target-supported ordering.','Preserve retry records, stale notice suppression, ownership reentry and independent diagnostic consumer.']),
 ('owned-async-cleanup',['candidate-aab8','candidate-1ace','candidate-04f8','candidate-4ce8'],'conditional',
  'Common owned-source cleanup-before-consumer-settlement; error policies vary.',
  ['Keep early match, exhaustion, failure and cancellation cleanup.','Preserve first-result/read/predicate order and original failure identity where established.','Simultaneous scan/cleanup failure precedence is not uniformly specified.','Native close carrier, cancellation and snapshot gating remain target-specific.']),
 ('local-config-readiness',['candidate-7d98','candidate-15bd'],'keep-branches',
  'Common readiness-preservation principle, but concrete readiness and effects differ.',
  ['Do not mandate ready() in timer/API-publication framework.','Do not replace imperative writes with declarative hydration.','Preserve evaluation timing, clones, picker hooks and separate editor scope where supplied.'])]


def audit():
    files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in LIBRARY.glob('*.json')}
    view=active_view(LIBRARY);active=set(view['active_ids'])
    rows={i['id']:i for _,v in documents(LIBRARY) for i in v['experiences'] if i['id'] in active}
    groups=[]
    for key,prefixes,status,reason,obligations in SPEC:
        ids=[]
        for pref in prefixes:
            matches=[key for key in rows if key==pref or key.startswith(pref)]
            assert len(matches)==1,(pref,matches)
            ids.extend(matches)
        groups.append(dict(id=key,status=status,source_ids=ids,reason=reason,
            obligations_to_preserve=obligations,source_body_characters=sum(len(rows[i][section]) for i in ids for section,_ in SECTIONS),
            lineage_requires_reconciliation=sorted(set(ids)&set(view['unresolved_ids']))))
    priority=[g for g in groups if g['status']=='priority']
    sizes=sorted(sum(len(i[k]) for k,_ in SECTIONS) for i in rows.values())
    result=dict(scope='Read-only source-text comparison. Candidate merges are not authored, accepted, applied or behaviorally verified.',
        active_count=len(rows),accepted_archive_count=view['accepted_count'],body_characters=sum(sizes),
        median_body_characters=sizes[len(sizes)//2],max_body_characters=max(sizes),entries_over4000_characters=sum(n>4000 for n in sizes),
        priority_groups=len(priority),priority_source_entries=sum(len(g['source_ids']) for g in priority),
        potential_semantic_entry_reduction=sum(len(g['source_ids'])-1 for g in priority),
        caveat='Potential reduction is arithmetic only. Draft/obligation coverage and lifecycle reconciliation are required before activation.',
        groups=groups,source_hashes=files)
    assert files=={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in LIBRARY.glob('*.json')}
    (OUT/'audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('groups','source_hashes')}))

if __name__=='__main__':audit()
