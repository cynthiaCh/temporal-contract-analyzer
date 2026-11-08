import pathlib as P,json,subprocess,collections
B=P.Path('/home/sribd/Downloads/wangshu/temporal-contract-bench-git');R=P.Path.cwd();C=B/'case-clusters/download-polling-restoration'
paths=subprocess.check_output(['rg','--files','--hidden','--no-ignore',str(B/'results'),str(R/'research'),'-g','run.json','-g','receipt.json'],text=True).splitlines();out=[]
for path in paths:
 p=P.Path(path)
 try:d=json.loads(p.read_text())
 except (ValueError,OSError):continue
 if not isinstance(d,dict):continue
 cid=d.get('case_id',d.get('case',''))
 if not isinstance(cid,str) or not cid.startswith('download-polling-restoration'):continue
 out.append({'path':str(p),'data':d})
P.Path('/tmp/download-history-discovery.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print('matching records',len(out))
agg=collections.Counter((x['data'].get('case_id',x['data'].get('case')),x['data'].get('model'),x['data'].get('reasoning_effort'),x['data'].get('condition'),x['data'].get('status'),x['data'].get('verdict',x['data'].get('raw_verdict'))) for x in out)
for k,v in sorted(agg.items(),key=lambda x:str(x[0])):print(v,k)
