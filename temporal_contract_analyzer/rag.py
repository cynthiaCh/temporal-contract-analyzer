"""Task-only lexical retrieval from a frozen candidate, without failure feedback."""
from collections import Counter
import json
import math
from pathlib import PurePosixPath
import re

from . import archive
from .context import expand, merge_ranges, parse_sources
from .core import EvidenceError

STOP = set('a an the to of and or in on with for is be by from that this it as'.split())


def terms(text):
    text=re.sub(r'([a-z])([A-Z])',r'\1 \2',text).replace('_',' ')
    return [s for s in re.findall(r'[a-z][a-z0-9]*|[\u4e00-\u9fff]',text.lower()) if s not in STOP]


def build_rag_context(report_id, task, visible_files, store, node=None,
                      max_chars=12000, seed_chars=8000, top_k=8):
    """Only task and public candidate bytes affect retrieval."""
    if not isinstance(task,str) or not task.strip():raise EvidenceError('RAG query requires the original task')
    if not 1<=seed_chars<=max_chars<=100000 or not 1<=top_k<=100:
        raise EvidenceError('Invalid RAG budget')
    code=archive.read_sources(report_id,store)
    sources=dict(code)
    for path,raw in visible_files.items():
        if PurePosixPath(path).suffix.lower() not in {'.md','.txt'}:continue
        try:sources[path]=raw.decode('utf-8')
        except UnicodeDecodeError:continue
    chunks=[]
    for path,text in sorted(sources.items()):
        lines=text.splitlines(keepends=True)
        for start in range(0,len(lines),40):
            end=min(len(lines),start+48)
            counts=Counter(terms(''.join(lines[start:end])))
            chunks.append(dict(file=path,start_line=start+1,end_line=end,counts=counts,length=sum(counts.values())))
            if end==len(lines):break
    query=sorted(set(terms(task)))
    frequencies=Counter(t for c in chunks for t in c['counts'])
    average=sum(c['length'] for c in chunks)/max(1,len(chunks)) or 1
    ranked=[]
    for c in chunks:
        score=0.0
        for t in query:
            tf=c['counts'][t]
            if tf:
                idf=math.log(1+(len(chunks)-frequencies[t]+0.5)/(frequencies[t]+0.5))
                score+=idf*tf*2.5/(tf+1.5*(0.25+0.75*c['length']/average))
        if score>0:ranked.append((score,c))
    ranked.sort(key=lambda v:(-v[0],v[1]['file'],v[1]['start_line']))
    seeds=[];selected=[];omitted=[]
    for score,c in ranked:
        if len(selected)>=top_k:break
        item=dict(file=c['file'],start_line=c['start_line'],end_line=c['end_line'],kind='rag-seed',
                  reasons=[dict(kind='task-bm25',rank=len(selected)+1)])
        proposed=merge_ranges(seeds+[item],sources)
        if sum(len(s['code']) for s in proposed)>seed_chars:
            omitted.append(dict(file=c['file'],start_line=c['start_line'],end_line=c['end_line'],reason='seed-budget-limit'))
            continue
        seeds=proposed
        selected.append(dict(file=c['file'],start_line=c['start_line'],end_line=c['end_line'],score=score))
    docs=[s for s in seeds if s['file'] not in code]
    code_seeds=[s for s in seeds if s['file'] in code]
    document_chars=sum(len(s['code']) for s in docs)
    parsed,parser=parse_sources(code,node) if code_seeds else ({},dict(status='not-needed'))
    expanded,gaps=expand(code_seeds,sources,parsed,2,max_chars-document_chars,{})
    snippets=merge_ranges(docs+expanded,sources)
    packet=dict(schema_version='temporal-rag-only-1',report_id=report_id,query=task,query_terms=query,
                retriever='BM25 k1=1.5 b=0.75; 48 lines / stride 40; lexical definitions/imports depth 2',
                corpus='current frozen candidate source and visible Markdown/text; no external corpus',
                selected=selected,snippets=snippets,unresolved=gaps,omitted=omitted,parser=parser,
                limits=dict(top_k=top_k,seed_chars=seed_chars,max_code_chars=max_chars),
                code_chars=sum(len(s['code']) for s in snippets),
                qualification='Task-only lexical retrieval. No failure feedback, learned recipes, cause hypotheses or D explanations are provided. Source excerpts are not a correctness judgment.')
    lines=['# Retrieved candidate context','',packet['qualification'],'',
           'Selected from the current candidate snapshot using the original task. Retrieval is incomplete; inspect additional candidate files when needed.','']
    for s in snippets:
        fence='`'*max(3,max((len(v) for v in re.findall(r'`+',s['code'])),default=0)+1)
        lines+=['## '+s['file']+':'+str(s['start_line'])+'–'+str(s['end_line']),fence,s['code'].rstrip(),fence,'']
    if gaps or omitted:
        lines+=['## Retrieval gaps',json.dumps(dict(unresolved=gaps,omitted=omitted),ensure_ascii=False,indent=2),'']
    return packet,'\n'.join(lines)+'\n'
