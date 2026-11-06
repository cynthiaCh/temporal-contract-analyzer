"""Study-local pure BM25 over original visible bytes; no analyzer/AST input."""
import math,re,time
from collections import Counter
STOP=set('a an the to of and or in on with for is be by from that this it as'.split())
def terms(t):
 t=re.sub(r'([a-z])([A-Z])',r'\1 \2',t).replace('_',' ')
 return [x for x in re.findall(r'[a-z][a-z0-9]*|[\u4e00-\u9fff]',t.lower()) if x not in STOP]
def retrieve(task,files):
 start=time.monotonic();sources={};chunks=[]
 for name,raw in sorted(files.items()):
  try:t=raw.decode('utf-8')
  except UnicodeDecodeError:continue
  if '\0' in t:continue
  sources[name]=t;lines=t.splitlines(keepends=True)
  for i in range(0,len(lines),40):
   end=min(len(lines),i+48);counts=Counter(terms(name)+terms(''.join(lines[i:end])))
   chunks.append(dict(file=name,start_line=i+1,end_line=end,counts=counts,length=sum(counts.values())))
   if end==len(lines):break
 df=Counter(t for c in chunks for t in c['counts']);average=sum(c['length'] for c in chunks)/max(1,len(chunks)) or 1;query=sorted(set(terms(task)));ranked=[]
 for c in chunks:
  score=0.
  for term in query:
   tf=c['counts'][term]
   if tf:score+=math.log(1+(len(chunks)-df[term]+.5)/(df[term]+.5))*tf*2.5/(tf+1.5*(.25+.75*c['length']/average))
  if score>0:ranked.append((score,c))
 ranked.sort(key=lambda v:(-v[0],v[1]['file'],v[1]['start_line']))
 def merged(selected):
  by={}
  for c in selected:by.setdefault(c['file'],[]).append((c['start_line'],c['end_line']))
  out=[]
  for name,ranges in sorted(by.items()):
   joined=[]
   for lo,hi in sorted(ranges):
    if joined and lo<=joined[-1][1]+1:joined[-1]=(joined[-1][0],max(joined[-1][1],hi))
    else:joined.append((lo,hi))
   lines=sources[name].splitlines(keepends=True)
   for lo,hi in joined:out.append(dict(file=name,start_line=lo,end_line=hi,code=''.join(lines[lo-1:hi])))
  return out
 selected=[];omitted=[]
 for score,c in ranked:
  if len(selected)>=8:break
  item={k:c[k] for k in ['file','start_line','end_line']};item['score']=score
  snippets=merged(selected+[item])
  if sum(len(x['code']) for x in snippets)>12000:omitted.append(dict(item,reason='character-budget'));continue
  selected.append(item)
 snippets=merged(selected);packet=dict(query=task,query_terms=query,retriever='Pure BM25 k1=1.5,b=.75, path tokens + raw text,48lines/stride40,top8,max12000raw characters',corpus_files=sorted(sources),selected=selected,snippets=snippets,omitted=omitted,code_characters=sum(len(s['code']) for s in snippets),ast_expansion=False,static_findings_used=False,elapsed_seconds=time.monotonic()-start)
 lines=['# Retrieved candidate context','', 'Raw source, configuration and documentation excerpts selected using the original task only. Retrieval is incomplete; inspect other candidate files when needed.','']
 for s in snippets:
  fence='`'*max(3,max((len(v) for v in re.findall(r'`+',s['code'])),default=0)+1)
  lines+=['## '+s['file']+':'+str(s['start_line'])+'-'+str(s['end_line']),fence,s['code'].rstrip(),fence,'']
 return packet,'\n'.join(lines)+'\n'
