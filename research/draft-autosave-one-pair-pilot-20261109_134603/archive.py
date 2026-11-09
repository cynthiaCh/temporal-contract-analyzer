"""Deterministic, non-LLM session archival, outside the candidate namespace."""
import hashlib,json,os,shutil,stat,subprocess,time
from pathlib import Path

def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def inventory(root):
    """Record all entries; never follow symlinks or silently drop special files."""
    root=Path(root);result={}
    def scan(directory):
        for p in sorted(directory.iterdir()):
            info=p.lstat();rel=str(p.relative_to(root));entry={'mode':stat.S_IMODE(info.st_mode)}
            if stat.S_ISLNK(info.st_mode):entry.update(kind='symlink',target=os.readlink(p))
            elif stat.S_ISDIR(info.st_mode):entry['kind']='directory'
            elif stat.S_ISREG(info.st_mode):entry.update(kind='file',sha256=sha(p),bytes=info.st_size)
            else:raise ValueError('unsupported special candidate entry: '+rel)
            result[rel]=entry
            if entry['kind']=='directory':scan(p)
    scan(root);return result

def digest(tree):return hashlib.sha256(json.dumps(tree,sort_keys=True,separators=(',',':')).encode()).hexdigest()

class Archive:
    def __init__(self,run_dir):
        self.run_dir=Path(run_dir).resolve();self.workspace=self.run_dir/'workspace';self.root=self.run_dir/'archive'
        self.original=self.root/'input/original';self.final=self.root/'final-candidate';self.errors=[]
        self.state={'status':'PREPARING','errors':self.errors,'steps':{},'model_outcome_file':'model-outcome.json'}

    def prepare(self,candidate,task,prompt,config):
        source=Path(candidate).resolve()
        if source==self.run_dir or source in self.run_dir.parents or self.run_dir in source.parents:
            raise ValueError('candidate source and run directory must be disjoint')
        self.run_dir.mkdir(parents=True,exist_ok=False);self.root.mkdir()
        try:
            shutil.copytree(candidate,self.original,symlinks=True)
            original=inventory(self.original)
            shutil.copytree(self.original,self.workspace,symlinks=True)
            if inventory(self.workspace)!=original:raise ValueError('initial workspace differs from original')
            (self.root/'input/task.md').write_bytes(Path(task).read_bytes())
            (self.root/'input/actual-prompt.md').write_text(prompt)
            save(self.root/'input/config.json',config)
            save(self.root/'input/frozen-start.json',{'files':original,'tree_sha256':digest(original),'prompt_sha256':sha(self.root/'input/actual-prompt.md'),'task_sha256':sha(self.root/'input/task.md'),'config_sha256':sha(self.root/'input/config.json')})
            self.state['steps']['prepare']='OK';self.state['status']='PREPARED';self._save()
        except Exception as exc:
            self.error('prepare',exc);self.state['status']='ERROR';self._save();raise
        return self

    def _save(self):save(self.root/'archive-status.json',self.state)

    def error(self,stage,exc):self.errors.append({'stage':stage,'error':repr(exc)})

    def collect(self):
        """Best-effort derivation; raw stream/ledger always remain primary."""
        from usage import summarize_ledger
        events=[];bad=[];messages=[];errors=[]
        path=self.root/'events.jsonl'
        if path.exists():
            with path.open(errors='replace') as stream,(self.root/'tool-outputs.jsonl').open('w') as tools:
                for n,line in enumerate(stream,1):
                    try:
                        e=json.loads(line)
                        if not isinstance(e,dict):raise ValueError('event must be object')
                    except (ValueError,TypeError):bad.append(n);continue
                    events.append(e);item=e.get('item') or {}
                    if not isinstance(item,dict):item={}
                    if e.get('type')=='item.completed' and item.get('type') in ['command_execution','file_change']:
                        tools.write(json.dumps({'event_line':n,'item':item},ensure_ascii=False)+'\n')
                    if e.get('type')=='item.completed' and item.get('type')=='agent_message' and isinstance(item.get('text'),str):messages.append(item['text'])
                    if e.get('type') in ['error','turn.failed']:errors.append({'event_line':n,'event':e})
        completed=sum(e.get('type')=='turn.completed' for e in events)==1 and not errors and not bad
        answer=messages[-1] if messages and completed else None
        (self.root/'raw-answer.txt').write_text(answer if answer is not None else '')
        save(self.root/'agent-messages.json',messages)
        if messages and not completed:(self.root/'partial-answer.txt').write_text(messages[-1])
        meter=self.root/'meter/ledger.json';ledger=None;meter_error=None
        try:
            if meter.exists():
                ledger=json.loads(meter.read_text())
                if not isinstance(ledger,dict):raise ValueError('ledger must be object')
        except (OSError,ValueError,TypeError) as exc:meter_error=repr(exc);ledger=None
        usage=summarize_ledger(ledger)
        save(self.root/'usage.json',usage)
        failed_posts=[x for x in ((ledger or {}).get('events') or []) if isinstance(x,dict) and isinstance(x.get('event'),dict) and x['event'].get('hook_event_name')=='PostModelRequest' and x['event'].get('status')!='completed']
        save(self.root/'service-errors.json',{'raw_cli_errors':errors,'failed_request_hooks':failed_posts,'meter_parse_error':meter_error,'raw_provider_wire_body':'not exposed by CLI; raw events/stderr/ledger retained'})
        summary={'event_lines_malformed':bad,'answer_present':answer is not None,'turn_completed':completed,'meter_present':ledger is not None,'meter_parse_error':meter_error,'service_error_count':len(errors),'events_present':path.exists(),'stderr_present':(self.root/'stderr.log').exists(),'partial_messages':len(messages) if not completed else 0}
        save(self.root/'collection.json',summary);self.state['steps']['collect']='OK';return events,answer,summary

    def annotate_extras(self,events):
        path=self.root/'file-changes.json'
        if not path.exists():return
        changes=json.loads(path.read_text())
        for entry in changes['extra_files']:
            entry['event_evidence']=[]
            entry['impact']='Preserved in final snapshot/diff/scorer input; business relevance not inferred from name or suffix.'
            for n,event in enumerate(events,1):
                item=event.get('item') or {}
                if not isinstance(item,dict):continue
                if event.get('type')!='item.completed':continue
                for change in (item.get('changes') or []) if item.get('type')=='file_change' else []:
                    source=change.get('path','')
                    if source in [entry['path'],'/workspace/'+entry['path'],str(self.workspace/entry['path'])]:
                        entry['event_evidence'].append({'event_line':n,'item_id':item.get('id'),'kind':'explicit_file_change','path':source})
            if entry['event_evidence']:entry['origin']='explicit file-change event; details retained in events.jsonl'
        save(path,changes)

    def finalize(self,*,model_stopped,diff_runner=subprocess.run):
        """Always attempted after process stop, including abnormal model outcomes."""
        self.state['status']='FINALIZING'
        if not model_stopped:
            self.error('process_stop','model process is not known stopped');self.state['status']='ERROR';self._save();return self.state
        try:
            before=inventory(self.workspace)
            shutil.copytree(self.workspace,self.final,symlinks=True)
            after=inventory(self.workspace);copied=inventory(self.final)
            if before!=after or copied!=before:raise ValueError('candidate changed during snapshot')
            original=inventory(self.original)
            if original!=json.loads((self.root/'input/frozen-start.json').read_text())['files']:raise ValueError('original snapshot changed')
            save(self.root/'final-manifest.json',{'files':copied,'tree_sha256':digest(copied),'workspace_sha256_before':digest(before),'workspace_sha256_after':digest(after)})
            added=sorted(set(copied)-set(original));deleted=sorted(set(original)-set(copied));changed=sorted(k for k in copied.keys()&original.keys() if copied[k]!=original[k])
            save(self.root/'file-changes.json',{'added':added,'deleted':deleted,'changed':changed,'extra_files': [{'path':p,'origin':'created during session; actor/cause may need event review','classification':'unclassified; preserved, never deleted by suffix/name','affects_snapshot_and_diff':True} for p in added],'all_entries_preserved':True})
            self.state['steps']['snapshot']='OK'
        except Exception as exc:self.error('snapshot',exc)
        if self.state['steps'].get('snapshot')=='OK':
            try:
                changes=sorted(k for k in set(original)|set(copied) if original.get(k)!=copied.get(k))
                commands=[];nontext=[]
                for rel in changes:
                    old=original.get(rel);new=copied.get(rel)
                    if (old is None or old['kind']=='file') and (new is None or new['kind']=='file'):
                        # /dev/null labels make addition/deletion unambiguous to patch,
                        # independent of host timezone or directory-depth differences.
                        commands.append(['diff','-u','--label','a/'+rel if old else '/dev/null','--label','b/'+rel if new else '/dev/null',str(self.original/rel) if old else '/dev/null',str(self.final/rel) if new else '/dev/null'])
                    else:nontext.append({'path':rel,'before':old,'after':new})
                if not commands:commands=[['diff','-ruN','--no-dereference',str(self.original),str(self.original)]]
                results=[]
                with (self.root/'patch.diff').open('wb') as out,(self.root/'diff.stderr').open('wb') as err:
                    for cmd in commands:
                        z=diff_runner(cmd,stdout=out,stderr=err,timeout=60,env={**os.environ,'LC_ALL':'C'})
                        results.append({'command':cmd,'exit_code':z.returncode})
                        if z.returncode not in [0,1]:break
                code=next((r['exit_code'] for r in results if r['exit_code'] not in [0,1]),1 if any(r['exit_code']==1 for r in results) else 0)
                status='UNCHANGED' if code==0 else 'CHANGED' if code==1 else 'ERROR'
                save(self.root/'nontext-changes.json',nontext)
                save(self.root/'diff-result.json',{'tools':results,'exit_code':code,'status':status,'candidate_changed':before!=original,'patch_bytes':(self.root/'patch.diff').stat().st_size,'metadata_or_empty_file_changes_not_represented_by_text_diff':before!=original and code==0,'coverage':'Text hunks are patch-compatible; binary contents, symlinks, mode/empty-file/type changes are fully preserved in final snapshot and manifests.'})
                if status=='ERROR':raise RuntimeError('diff tool exit '+str(code))
                self.state['steps']['diff']=status
            except Exception as exc:
                self.error('diff',exc)
                if not (self.root/'diff-result.json').exists():save(self.root/'diff-result.json',{'exit_code':None,'status':'ERROR','exception':repr(exc)})
        try:
            events,answer,summary=self.collect()
            self.annotate_extras(events)
        except Exception as exc:self.error('collect',exc)
        # Confirm that even a failing archiver/diff did not rewrite business code.
        try:
            current=inventory(self.workspace)
            if 'before' in locals() and current!=before:raise ValueError('archival operation altered business workspace')
            if self.state['steps'].get('snapshot')=='OK' and inventory(self.final)!=before:raise ValueError('archival operation altered final candidate')
            self.state['steps']['source_preserved']='OK'
        except Exception as exc:self.error('preservation',exc)
        self.state['status']='ERROR' if self.errors else 'OK';self._save();return self.state

    def write_manifest(self):
        files={str(p.relative_to(self.root)):sha(p) for p in self.root.rglob('*') if p.is_file() and not p.is_symlink() and p!=self.root/'ARTIFACTS.sha256'}
        (self.root/'ARTIFACTS.sha256').write_text(''.join(h+'  '+p+'\n' for p,h in sorted(files.items())))
