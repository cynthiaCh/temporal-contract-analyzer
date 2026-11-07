"""Fixed interleaved sequence; gates only execution, no quality evaluation."""
import subprocess,sys,time
from pathlib import Path
from run import OUT,read,save,frozen

def main():
 frozen();assert not (OUT/'requests.json').exists();slots=read(OUT/'schedule.json')['order']
 for i,slot in enumerate(slots):
  call=slot['call_id'];run=subprocess.run(['/usr/bin/python3',str(OUT/'run.py'),call],cwd=OUT)
  gate=subprocess.run(['/usr/bin/python3',str(OUT/'execution_gate.py'),call],cwd=OUT) if (OUT/'runs'/call/'receipt.json').exists() else None
  if run.returncode or gate is None or gate.returncode:
   for unused in slots[i+1:]:save(OUT/'runs'/unused['call_id']/'slot.json',dict(**unused,status='NOT_RUN',reason='prior execution invalid; stop without retry',actual_prompt=None,actual_output=None))
   save(OUT/'execution-complete.json',{'status':'STOPPED_EXECUTION_INVALID','failed_slot':call,'slots_launched':i+1,'quality_not_used':True});return
 save(OUT/'execution-complete.json',{'status':'COMPLETE','slots_launched':8,'quality_evaluation_not_started':True,'at':time.time()})
if __name__=='__main__':main()
