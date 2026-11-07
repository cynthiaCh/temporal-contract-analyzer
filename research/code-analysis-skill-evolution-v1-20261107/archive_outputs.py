"""Post-generation anonymization and mechanical extraction, no semantic judge."""
import json,secrets,hashlib,shutil,csv,difflib
from pathlib import Path
OUT=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert (OUT/'K1-complete.json').exists() and len(read(OUT/'requests.json'))==9
 assert not (OUT/'private-report-labels.json').exists()
 records=[r for r in read(OUT/'requests.json') if r['mode']=='analysis'];package=OUT/'anonymous-review';package.mkdir();mapping={};index=[]
 for unit,name in [('U1','U1-transfer-admission.md'),('U2','U2-pending-waiting.md')]:
  d=package/'evidence'/unit;d.mkdir(parents=True);shutil.copytree(OUT/'materials'/unit/'candidate',d/'candidate');shutil.copyfile(OUT/'materials'/unit/'task.md',d/'task.md');shutil.copyfile(OUT.parent/'code-analysis-standard-drafts-v1-20261107'/name,d/'standard.md')
 for r in records:
  aid='R'+secrets.token_hex(5);d=package/aid;d.mkdir();folder=Path(r['path']);report=folder/'report.md'
  if report.exists():shutil.copyfile(report,d/'report.md')
  else:(d/'report.md').write_text('[No valid report; retain raw output and failure]')
  shutil.copyfile(folder/'raw-answer.txt',d/'raw-answer.txt');mapping[aid]=dict(call_id=r['call_id'],phase=r['phase'],unit=r.get('unit'),replicate=r.get('replicate'),report_sha256=sha(d/'report.md'),source_path=str(folder),status=r['status'])
  index.append(dict(anonymous_id=aid,unit=r.get('unit'),characters=len((d/'report.md').read_text()),status=r['status']))
 (OUT/'private-report-labels.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+'\n');(package/'index.json').write_text(json.dumps(sorted(index,key=lambda x:x['anonymous_id']),indent=2)+'\n')
 (package/'README.md').write_text('Random IDs hide phase/order labels only. Unit/source content may identify source or condition. Executing-agent review is unblinded proxy, not independent human blind review. Labels are outside this package. Use approved standard and source-only applicability; freeze review before unblinded summary.\n')
 print('Anonymous reports saved',len(records))
if __name__=='__main__':main()
